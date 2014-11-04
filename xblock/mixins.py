"""
This module defines all of the Mixins that provide components of XBlock-family
functionality, such as ScopeStorage, RuntimeServices, and Handlers.
"""

import functools
try:
    import simplesjson as json  # pylint: disable=F0401
except ImportError:
    import json
from webob import Response

from xblock.exceptions import JsonHandlerError, KeyValueMultiSaveError, XBlockSaveError
from xblock.fields import Field, Reference, Scope, ReferenceList


class HandlersMixin(object):
    """
    A mixin provides all of the machinery needed for working with XBlock-style handlers.
    """

    @classmethod
    def json_handler(cls, func):
        """Wrap a handler to consume and produce JSON.

        Rather than a Request object, the method will now be passed the
        JSON-decoded body of the request.  Any data returned by the function
        will be JSON-encoded and returned as the response.

        The wrapped function can raise JsonHandlerError to return an error
        response with a non-200 status code.
        """
        @cls.handler
        @functools.wraps(func)
        def wrapper(self, request, suffix=''):
            """The wrapper function `json_handler` returns."""
            if request.method != "POST":
                return JsonHandlerError(405, "Method must be POST").get_response(allow=["POST"])
            try:
                request_json = json.loads(request.body)
            except ValueError:
                return JsonHandlerError(400, "Invalid JSON").get_response()
            try:
                response = func(self, request_json, suffix)
            except JsonHandlerError as err:
                return err.get_response()
            if isinstance(response, Response):
                return response
            else:
                return Response(json.dumps(response), content_type='application/json')
        return wrapper

    @classmethod
    def handler(cls, func):
        """A decorator to indicate a function is usable as a handler."""
        func._is_xblock_handler = True      # pylint: disable=protected-access
        return func

    def handle(self, handler_name, request, suffix=''):
        """Handle `request` with this block's runtime."""
        return self.runtime.handle(self, handler_name, request, suffix)


class ModelMetaclass(type):
    """
    A metaclass for using Fields as class attributes to define data access.

    All class attributes that are Fields will be added to the 'fields'
    attribute on the class.

    """
    def __new__(mcs, name, bases, attrs):
        new_class = super(ModelMetaclass, mcs).__new__(mcs, name, bases, attrs)

        fields = {}
        # Pylint tries to do fancy inspection for class methods/properties, and
        # in this case, gets it wrong

        # Loop through all of the baseclasses of cls, in
        # the order that methods are resolved (Method Resolution Order / mro)
        # and find all of their defined fields.
        #
        # Only save the first such defined field (as expected for method resolution)
        for base_class in new_class.mro():  # pylint: disable=E1101
            # We can't use inspect.getmembers() here, because that would
            # call the fields property again, and generate an infinite loop.
            # Instead, we loop through all of the attribute names, exclude the
            # 'fields' attribute, and then retrieve the value
            for attr_name in dir(base_class):
                attr_value = getattr(base_class, attr_name)
                if isinstance(attr_value, Field):
                    fields.setdefault(attr_name, attr_value)

                    # Allow the field to know what its name is
                    attr_value._name = attr_name  # pylint: disable=protected-access

        new_class.fields = fields

        return new_class


class ScopedStorageMixin(object):
    """
    This mixin provides scope for Fields and the associated Scoped storage.
    """
    __metaclass__ = ModelMetaclass

    def __init__(self, field_data, scope_ids, *args, **kwargs):
        """
        Arguments:
            field_data (:class:`.FieldData`): Interface used by the XBlock
                fields to access their data from wherever it is persisted.

            scope_ids (:class:`.ScopeIds`): Identifiers needed to resolve
                scopes.
        """
        self._field_data = field_data
        self._field_data_cache = {}
        self._dirty_fields = {}
        self.scope_ids = scope_ids

        super(ScopedStorageMixin, self).__init__(*args, **kwargs)

    def save(self):
        """Save all dirty fields attached to this XBlock."""
        if not self._dirty_fields:
            # nop if _dirty_fields attribute is empty
            return
        try:
            fields_to_save = self._get_fields_to_save()
            # Throws KeyValueMultiSaveError if things go wrong
            self._field_data.set_many(self, fields_to_save)

        except KeyValueMultiSaveError as save_error:
            saved_fields = [field for field in self._dirty_fields if field.name in save_error.saved_field_names]
            for field in saved_fields:
                # should only find one corresponding field
                del self._dirty_fields[field]
            raise XBlockSaveError(saved_fields, self._dirty_fields.keys())

        # Remove all dirty fields, since the save was successful
        self._clear_dirty_fields()

    def _get_fields_to_save(self):
        """
        Create dictionary mapping between dirty fields and data cache values.
        A `field` is an instance of `Field`.
        """
        fields_to_save = {}
        for field in self._dirty_fields.keys():
            # If the field value isn't the same as the baseline we recorded
            # when it was read, then save it
            if field._is_dirty(self):  # pylint: disable=protected-access
                fields_to_save[field.name] = field.to_json(self._field_data_cache[field.name])
        return fields_to_save

    def _clear_dirty_fields(self):
        """
        Remove all dirty fields from an XBlock.
        """
        self._dirty_fields.clear()

    def __repr__(self):
        # `ScopedStorageMixin` obtains the `fields` attribute from the `ModelMetaclass`.
        # Since this is not understood by static analysis, silence this error.
        # pylint: disable=E1101
        attrs = []
        for field in self.fields.values():
            try:
                value = getattr(self, field.name)
            except Exception:  # pylint: disable=W0703
                # Ensure we return a string, even if unanticipated exceptions.
                attrs.append(" %s=???" % (field.name,))
            else:
                if isinstance(value, basestring):
                    value = value.strip()
                    if len(value) > 40:
                        value = value[:37] + "..."
                attrs.append(" %s=%r" % (field.name, value))
        return "<%s @%04X%s>" % (
            self.__class__.__name__,
            id(self) % 0xFFFF,
            ','.join(attrs)
        )


class ChildrenModelMetaclass(ModelMetaclass):
    """
    A metaclass that transforms the attribute `has_children = True` into a List
    field with a children scope.

    """
    def __new__(mcs, name, bases, attrs):
        if (attrs.get('has_children', False) or
                any(getattr(base, 'has_children', False) for base in bases)):
            attrs['children'] = ReferenceList(
                help='The ids of the children of this XBlock',
                scope=Scope.children)
        else:
            attrs['has_children'] = False

        return super(ChildrenModelMetaclass, mcs).__new__(mcs, name, bases, attrs)


class HierarchyMixin(ScopedStorageMixin):
    """
    This adds Fields for parents and children.
    """
    __metaclass__ = ChildrenModelMetaclass

    parent = Reference(help='The id of the parent of this XBlock', default=None, scope=Scope.parent)

    def __init__(self, *args, **kwargs):
        # A cache of the parent block, retrieved from .parent
        self._parent_block = None
        self._parent_block_id = None

        super(HierarchyMixin, self).__init__(*args, **kwargs)

    def get_parent(self):
        """Return the parent block of this block, or None if there isn't one."""
        if self._parent_block_id != self.parent:
            if self.parent is not None:
                self._parent_block = self.runtime.get_block(self.parent)
            else:
                self._parent_block = None
            self._parent_block_id = self.parent
        return self._parent_block
