"""
Base classes for all XBlock-like objects. Used by all XBlock Runtimes.
"""
import copy
import functools
import inspect
import json
import logging
import os
import warnings
from collections import OrderedDict, defaultdict

import pkg_resources
from lxml import etree
from webob import Response

from xblock.exceptions import (
    DisallowedFileError,
    FieldDataDeprecationWarning,
    JsonHandlerError,
    KeyValueMultiSaveError,
    XBlockSaveError,
)
from xblock.fields import Field, List, Reference, ReferenceList, Scope, String
from xblock.internal import class_lazy
from xblock.plugin import Plugin
from xblock.validation import Validation

# OrderedDict is used so that namespace attributes are put in predictable order
# This allows for simple string equality assertions in tests and have no other effects
XML_NAMESPACES = OrderedDict([
    ("option", "http://code.edx.org/xblock/option"),
    ("block", "http://code.edx.org/xblock/block"),
])

# __all__ controls what classes end up in the docs.
__all__ = ['XBlock', 'XBlockAside']

UNSET = object()


class _AutoNamedFieldsMetaclass(type):
    """
    Builds classes such that their Field attributes know their own names.

    This allows XBlock API users to define fields without name redundancy, e.g. like this:

        class MyBlock(XBlock):
            my_field = Field(...)

    rather than this:

        class MyBlock(XBlock):
            my_field = Field(name="my_field", ...)
    """
    def __new__(mcs, name, bases, attrs):
        """
        Ensure __name__ is set on all Field attributes, both on the new class and on its bases.
        """
        def needs_name(obj):
            """
            Is this object a Field that hasn't had its name assigned yet?
            """
            return isinstance(obj, Field) and not obj.__name__

        # Iterate over the attrs before they're bound to the class
        # so that we don't accidentally trigger any __get__ methods
        for attr_name, attr in attrs.items():
            if needs_name(attr):
                attr.__name__ = attr_name

        # Iterate over all of the base classes, so that we can add
        # names to any mixins that don't include this metaclass, but that
        # do include Fields
        for base in bases:
            for attr_name, attr in inspect.getmembers(base, predicate=needs_name):
                attr.__name__ = attr_name

        return super().__new__(mcs, name, bases, attrs)


class Blocklike(metaclass=_AutoNamedFieldsMetaclass):
    """
    Shared base for XBlocks and XBlockAsides, providing these common capabilities:

    - services
    - fields
    - OLX
    - handlers
    - resources

    (see XBlock and XBlockAside classes for details)
    """
    resources_dir = ''
    public_dir = 'public'
    i18n_js_namespace = None

    @classmethod
    def get_resources_dir(cls):
        """
        Gets the resource directory for this XBlock-like class.
        """
        return cls.resources_dir

    @classmethod
    def get_public_dir(cls):
        """
        Gets the public directory for this XBlock-like class.
        """
        return cls.public_dir

    @classmethod
    def get_i18n_js_namespace(cls):
        """
        Gets the JavaScript translations namespace for this XBlock-like class.

        Returns:
            str: The JavaScript namespace for this XBlock-like class.
            None: If this doesn't have JavaScript translations configured.
        """
        return cls.i18n_js_namespace

    @classmethod
    def open_local_resource(cls, uri):
        """
        Open a local resource.

        The container calls this method when it receives a request for a
        resource on a URL which was generated by Runtime.local_resource_url().
        It will pass the URI from the original call to local_resource_url()
        back to this method. The XBlock-like must parse this URI and return an open
        file-like object for the resource.

        For security reasons, the default implementation will return only a
        very restricted set of file types, which must be located in a folder
        that defaults to "public".  The location used for public resources can
        be changed on a per-XBlock-like basis. XBlock-like authors who want to override
        this behavior will need to take care to ensure that the method only
        serves legitimate public resources. At the least, the URI should be
        matched against a whitelist regex to ensure that you do not serve an
        unauthorized resource.
        """

        if isinstance(uri, bytes):
            uri = uri.decode('utf-8')

        # If no resources_dir is set, then this XBlock cannot serve local resources.
        if cls.resources_dir is None:
            raise DisallowedFileError("This XBlock is not configured to serve local resources")

        # Make sure the path starts with whatever public_dir is set to.
        if not uri.startswith(cls.public_dir + '/'):
            raise DisallowedFileError(f"Only files from {cls.public_dir!r}/ are allowed: {uri!r}")

        # Disalow paths that have a '/.' component, as `/./` is a no-op and `/../`
        # can be used to recurse back past the entry point of this XBlock.
        if "/." in uri:
            raise DisallowedFileError("Only safe file names are allowed: %r" % uri)

        return pkg_resources.resource_stream(cls.__module__, os.path.join(cls.resources_dir, uri))

    @classmethod
    def json_handler(cls, func):
        """
        Wrap a handler to consume and produce JSON.

        Rather than a Request object, the method will now be passed the
        JSON-decoded body of the request. The request should be a POST request
        in order to use this method. Any data returned by the function
        will be JSON-encoded and returned as the response.

        The wrapped function can raise JsonHandlerError to return an error
        response with a non-200 status code.

        This decorator will return a 405 HTTP status code if the method is not
        POST.
        This decorator will return a 400 status code if the body contains
        invalid JSON.
        """
        @cls.handler
        @functools.wraps(func)
        def wrapper(self, request, suffix=''):
            """The wrapper function `json_handler` returns."""
            if request.method != "POST":
                return JsonHandlerError(405, "Method must be POST").get_response(allow=["POST"])
            try:
                request_json = json.loads(request.body.decode('utf-8'))
            except ValueError:
                return JsonHandlerError(400, "Invalid JSON").get_response()
            try:
                response = func(self, request_json, suffix)
            except JsonHandlerError as err:
                return err.get_response()
            if isinstance(response, Response):
                return response
            else:
                return Response(json.dumps(response), content_type='application/json', charset='utf8')
        return wrapper

    @classmethod
    def handler(cls, func):
        """
        A decorator to indicate a function is usable as a handler.

        The wrapped function must return a :class:`webob.Response` object.
        """
        func._is_xblock_handler = True      # pylint: disable=protected-access
        return func

    @classmethod
    def needs(cls, *service_names):
        """
        A class decorator to indicate that an XBlock-like class needs particular services.
        """
        def _decorator(cls_):
            for service_name in service_names:
                cls_._services_requested[service_name] = "need"  # pylint: disable=protected-access
            return cls_
        return _decorator

    @classmethod
    def wants(cls, *service_names):
        """
        A class decorator to indicate that a XBlock-like class wants particular services.
        """
        def _decorator(cls_):
            for service_name in service_names:
                cls_._services_requested[service_name] = "want"  # pylint: disable=protected-access
            return cls_
        return _decorator

    @classmethod
    def service_declaration(cls, service_name):
        """
        Find and return a service declaration.

        XBlock-like classes declare their service requirements with `@XBlock{Aside}.needs` and
        `@XBlock{Aside}.wants` decorators.  These store information on the class.
        This function finds those declarations for a block.

        Arguments:
            service_name (str): the name of the service requested.

        Returns:
            One of "need", "want", or None.
        """
        return cls._combined_services.get(service_name)  # pylint: disable=no-member

    @class_lazy
    def _services_requested(cls):  # pylint: disable=no-self-argument
        """
        A per-class dictionary to store the services requested by a particular XBlock.
        """
        return {}

    @class_lazy
    def _combined_services(cls):  # pylint: disable=no-self-argument
        """
        A dictionary that collects all _services_requested by all ancestors of this XBlock class.
        """
        # The class declares what services it desires. To deal with subclasses,
        # especially mixins, properly, we have to walk up the inheritance
        # hierarchy, and combine all the declared services into one dictionary.
        combined = {}
        for parent in reversed(cls.mro()):  # pylint: disable=no-member
            combined.update(getattr(parent, "_services_requested", {}))
        return combined

    @class_lazy
    def fields(cls):  # pylint: disable=no-self-argument
        """
        A dictionary mapping the attribute name to the Field object for all Field attributes of the class.
        """
        fields = {}
        # Loop through all of the baseclasses of cls, in
        # the order that methods are resolved (Method Resolution Order / mro)
        # and find all of their defined fields.
        #
        # Only save the first such defined field (as expected for method resolution)

        bases = cls.mro()  # pylint: disable=no-member
        local = bases.pop(0)

        # First, descend the MRO from the top down, updating the 'fields' dictionary
        # so that the dictionary always has the most specific version of fields in it
        for base in reversed(bases):
            fields.update(getattr(base, 'fields', {}))

        # For this class, loop through all attributes not named 'fields',
        # find those of type Field, and save them to the 'fields' dict
        for attr_name, attr_value in inspect.getmembers(local, lambda attr: isinstance(attr, Field)):
            fields[attr_name] = attr_value

        return fields

    @classmethod
    def parse_xml(cls, node, runtime, keys):
        """
        Use `node` to construct a new block.

        Arguments:
            node (:class:`~xml.etree.ElementTree.Element`): The xml node to parse into an xblock.

            runtime (:class:`.Runtime`): The runtime to use while parsing.

            keys (:class:`.ScopeIds`): The keys identifying where this block
                will store its data.
        """
        block = runtime.construct_xblock_from_class(cls, keys)

        # The base implementation: child nodes become child blocks.
        # Or fields, if they belong to the right namespace.
        for child in node:
            if child.tag is etree.Comment:
                continue
            qname = etree.QName(child)
            tag = qname.localname
            namespace = qname.namespace

            if namespace == XML_NAMESPACES["option"]:
                cls._set_field_if_present(block, tag, child.text, child.attrib)
            else:
                block.runtime.add_node_as_child(block, child)

        # Attributes become fields.
        for name, value in list(node.items()):  # lxml has no iteritems
            cls._set_field_if_present(block, name, value, {})

        # Text content becomes "content", if such a field exists.
        if "content" in block.fields and block.fields["content"].scope == Scope.content:
            text = node.text
            if text:
                text = text.strip()
                if text:
                    block.content = text

        return block

    @classmethod
    def _set_field_if_present(cls, block, name, value, attrs):
        """
        Sets the field block.name, if block have such a field.
        """
        if name in block.fields:
            value = (block.fields[name]).from_string(value)
            if "none" in attrs and attrs["none"] == "true":
                setattr(block, name, None)
            else:
                setattr(block, name, value)
        else:
            logging.warning("%s does not contain field %s", type(block), name)

    def __init__(self, scope_ids, field_data=None, *, runtime, **kwargs):
        """
        Arguments:

            scope_ids (:class:`.ScopeIds`): Identifiers needed to resolve
                scopes.

            field_data (:class:`.FieldData`): Interface used by XBlock-likes'
                fields to access their data from wherever it is persisted.
                DEPRECATED--supply a field-data Runtime service instead.

            runtime (:class:`.Runtime`): Use it to access the environment.
                It is available in XBlock code as ``self.runtime``.

        """
        self.runtime = runtime

        # This is used to store a directly passed field data
        # for backwards compatibility
        if field_data:
            warnings.warn(
                "Setting _field_data via the constructor is deprecated, please use a Runtime service",
                FieldDataDeprecationWarning,
                stacklevel=2
            )
            # Storing _field_data instead of _deprecated_per_instance_field_data allows subclasses to
            # continue to override this behavior (for instance, the way that edx-platform's XModule does
            # in order to proxy to XBlock).
            self._field_data = field_data
        else:
            self._deprecated_per_instance_field_data = None  # pylint: disable=invalid-name

        self._field_data_cache = {}
        self._dirty_fields = {}
        self.scope_ids = scope_ids

        super().__init__(**kwargs)

    def __repr__(self):
        attrs = []
        for field in self.fields.values():
            try:
                value = getattr(self, field.name)
            except Exception:  # pylint: disable=broad-except
                # Ensure we return a string, even if unanticipated exceptions.
                attrs.append(f" {field.name}=???")
            else:
                if isinstance(value, bytes):
                    value = value.decode('utf-8', errors='escape')
                if isinstance(value, str):
                    value = value.strip()
                    if len(value) > 40:
                        value = value[:37] + "..."
                attrs.append(f" {field.name}={value!r}")
        return "<{} @{:04X}{}>".format(
            self.__class__.__name__,
            id(self) % 0xFFFF,
            ','.join(attrs)
        )

    @property
    def usage_key(self):
        """
        A key identifying this particular usage of the XBlock-like, unique across all learning contexts in the system.

        Equivalent to to `.scope_ids.usage_id`.
        """
        return self.scope_ids.usage_id

    @property
    def context_key(self):
        """
        A key identifying the learning context (course, library, etc.) that contains this XBlock-like usage.

        Equivalent to `.scope_ids.usage_id.context_key`.

        Returns:
        * `LearningContextKey`, if `.scope_ids.usage_id` is a `UsageKey` instance.
        * `None`, otherwise.

        After https://github.com/openedx/XBlock/issues/708 is complete, we can assume that
        `.scope_ids.usage_id` is always a `UsageKey`, and that this method will
        always return a `LearningContextKey`.
        """
        return getattr(self.scope_ids.usage_id, "context_key", None)

    def index_dictionary(self):
        """
        Return a dict containing information that could be used to feed a search index.

        Values may be numeric, string, or dict.
        """
        display_name = getattr(self, "display_name", None)

        # Getting self.display_name.default wouldn't work as self.display_name is actually
        # a str after the class instance is created. So, we can only access the default value
        # of display_name field by accessing class variable of same name
        content_type = getattr(
            getattr(self.__class__, "display_name", None), "default", None
        )

        _index_dictionary = {}

        if display_name is not None:
            _index_dictionary.update({
                "content": {
                    "display_name": display_name
                }
            })

        if content_type is not None:
            _index_dictionary.update({
                "content_type": content_type
            })

        return _index_dictionary

    def handle(self, handler_name, request, suffix=''):
        """
        Handle `request` with this block's runtime.
        """
        return self.runtime.handle(self, handler_name, request, suffix)

    @property
    def _field_data(self):
        """
        Return the FieldData for this XBlock (either as passed in the constructor
        or from retrieving the 'field-data' service).
        """
        if self._deprecated_per_instance_field_data:
            return self._deprecated_per_instance_field_data
        else:
            return self.runtime.service(self, 'field-data')

    @_field_data.setter
    def _field_data(self, field_data):
        """
        Set _field_data. Deprecated.
        """
        warnings.warn("Setting _field_data is deprecated", FieldDataDeprecationWarning, stacklevel=2)
        self._deprecated_per_instance_field_data = field_data

    def save(self):
        """
        Save all dirty fields attached to this XBlock.
        """
        if not self._dirty_fields:
            # nop if _dirty_fields attribute is empty
            return

        fields_to_save = self._get_fields_to_save()
        if fields_to_save:
            self.force_save_fields(fields_to_save)
        self.runtime.save_block(self)

    def force_save_fields(self, field_names):
        """
        Save all fields that are specified in `field_names`, even if they are not dirty.
        """
        fields = [
            self.fields[field_name]  # pylint: disable=unsubscriptable-object
            for field_name in field_names
        ]
        fields_to_save_json = {}
        for field in fields:
            fields_to_save_json[field.name] = field.to_json(self._field_data_cache[field.name])

        try:
            # Throws KeyValueMultiSaveError if things go wrong
            self._field_data.set_many(self, fields_to_save_json)
        except KeyValueMultiSaveError as save_error:
            saved_fields = [field for field in fields
                            if field.name in save_error.saved_field_names]
            for field in saved_fields:
                # should only find one corresponding field
                fields.remove(field)
                # if the field was dirty, delete from dirty fields
                self._reset_dirty_field(field)
            msg = f'Error saving fields {save_error.saved_field_names}'
            raise XBlockSaveError(saved_fields, fields, msg)  # pylint: disable= raise-missing-from

        # Remove all dirty fields, since the save was successful
        for field in fields:
            self._reset_dirty_field(field)

    def _get_fields_to_save(self):
        """
        Get an xblock's dirty fields.
        """
        # If the field value isn't the same as the baseline we recorded
        # when it was read, then save it
        # pylint: disable=protected-access
        return [field.name for field in self._dirty_fields if field._is_dirty(self)]

    def _clear_dirty_fields(self):
        """
        Remove all dirty fields from an XBlock.
        """
        self._dirty_fields.clear()

    def _reset_dirty_field(self, field):
        """
        Resets dirty field value with the value from the field data cache.
        """
        if field in self._dirty_fields:
            self._dirty_fields[field] = copy.deepcopy(
                self._field_data_cache[field.name]
            )

    def add_xml_to_node(self, node):
        """
        For exporting, set data on `node` from ourselves.
        """
        # pylint: disable=E1101
        # Set node.tag based on our class name.
        node.tag = self.xml_element_name()
        node.set('xblock-family', self.entry_point)

        # Set node attributes based on our fields.
        for field_name, field in list(self.fields.items()):
            if field_name in ('children', 'parent', 'content'):
                continue
            if field.is_set_on(self) or field.force_export:
                self._add_field(node, field_name, field)

        # A content field becomes text content.
        text = self.xml_text_content()
        if text is not None:
            node.text = text

    def xml_element_name(self):
        """
        What XML element name should be used for this block?
        """
        return self.scope_ids.block_type

    def xml_text_content(self):
        """
        What is the text content for this block's XML node?
        """
        if 'content' in self.fields and self.content:  # pylint: disable=unsupported-membership-test
            return self.content
        else:
            return None

    def _add_field(self, node, field_name, field):
        """
        Add xml representation of field to node.

        Depending on settings, it either stores the value of field
        as an xml attribute or creates a separate child node.
        """
        value = field.to_string(field.read_from(self))
        text_value = "" if value is None else value

        # Is the field type supposed to serialize the fact that the value is None to XML?
        save_none_as_xml_attr = field.none_to_xml and value is None
        field_attrs = {"none": "true"} if save_none_as_xml_attr else {}

        if save_none_as_xml_attr or field.xml_node:
            # Field will be output to XML as an separate element.
            tag = etree.QName(XML_NAMESPACES["option"], field_name)
            elem = etree.SubElement(node, tag, field_attrs)
            if field.xml_node:
                # Only set the value if forced via xml_node;
                # in all other cases, the value is None.
                # Avoids an unnecessary XML end tag.
                elem.text = text_value
        else:
            # Field will be output to XML as an attribute on the node.
            node.set(field_name, text_value)


class XBlockMixin(Blocklike):
    """
    Base class for custom XBlock mixins.

    To provide custom attributes to all XBlock instances in a Runtime, extend this class and
    supply it to the Runtime's `mixins` parameter.
    """


class _HasChildrenMetaclass(_AutoNamedFieldsMetaclass):
    """
    Adds a ``children`` XBlock ReferenceList field to classes where ``has_children == True``.
    """
    def __new__(mcs, name, bases, attrs):
        if (attrs.get('has_children', False) or any(getattr(base, 'has_children', False) for base in bases)):
            attrs['children'] = ReferenceList(
                help='The ids of the children of this XBlock',
                scope=Scope.children)
        else:
            attrs['has_children'] = False

        return super().__new__(mcs, name, bases, attrs)


@Blocklike.needs("field-data")
class XBlock(Plugin, Blocklike, metaclass=_HasChildrenMetaclass):
    """
    Base class for XBlocks. Derive from this class to create new type of XBlock.

    Subclasses of XBlocks can:

    - Name one or more **views**, i.e. methods which render the block to HTML.
    - Access the **parents** of their instances.
    - Access and manage the **children** of their instances.
    - Request **services** from the runtime, for their instances to use.
    - Define scoped **fields**, which instances will use to store content, settings, and data.
    - Define how instances are serialized to and deserialized from **OLX** (Open Learning XML).
    - Mark methods as **handlers** for AJAX requests.
    - Be installed into a platform as an entry-point **plugin**.

    Note: Don't override the ``__init__`` method when deriving from this class.
    """

    entry_point = 'xblock.v1'

    name = String(help="Short name for the block", scope=Scope.settings)
    tags = List(help="Tags for this block", scope=Scope.settings)

    parent = Reference(help='The id of the parent of this XBlock', default=None, scope=Scope.parent)

    # These are dynamically managed by the awful hackery of _HasChildrenMetaclass.
    # We just declare their types here to make static analyzers happy.
    # Note that children is only defined iff has_children is defined and True.
    has_children: bool
    children: ReferenceList

    @class_lazy
    def _class_tags(cls):  # pylint: disable=no-self-argument
        """
        Collect the tags from all base classes.
        """
        class_tags = set()

        for base in cls.mro()[1:]:  # pylint: disable=no-member
            class_tags.update(getattr(base, '_class_tags', set()))

        return class_tags

    @staticmethod
    def tag(tags):
        """
        Returns a function that adds the words in `tags` as class tags to this class.
        """
        def dec(cls):
            """Add the words in `tags` as class tags to this class."""
            # Add in this class's tags
            cls._class_tags.update(tags.replace(",", " ").split())  # pylint: disable=protected-access
            return cls
        return dec

    @classmethod
    def load_tagged_classes(cls, tag, fail_silently=True):
        """
        Produce a sequence of all XBlock classes tagged with `tag`.

        fail_silently causes the code to simply log warnings if a
        plugin cannot import. The goal is to be able to use part of
        libraries from an XBlock (and thus have it installed), even if
        the overall XBlock cannot be used (e.g. depends on Django in a
        non-Django application). There is diagreement about whether
        this is a good idea, or whether we should see failures early
        (e.g. on startup or first page load), and in what
        contexts. Hence, the flag.
        """
        for name, class_ in cls.load_classes(fail_silently):
            if tag in class_._class_tags:  # pylint: disable=protected-access
                yield name, class_

    @classmethod
    def parse_xml(cls, node, runtime, keys):
        """
        Use `node` to construct a new block.

        Arguments:
            node (:class:`~xml.etree.ElementTree.Element`): The xml node to parse into an xblock.

            runtime (:class:`.Runtime`): The runtime to use while parsing.

            keys (:class:`.ScopeIds`): The keys identifying where this block
                will store its data.
        """
        block = runtime.construct_xblock_from_class(cls, keys)

        # The base implementation: child nodes become child blocks.
        # Or fields, if they belong to the right namespace.
        for child in node:
            if child.tag is etree.Comment:
                continue
            qname = etree.QName(child)
            tag = qname.localname
            namespace = qname.namespace

            if namespace == XML_NAMESPACES["option"]:
                cls._set_field_if_present(block, tag, child.text, child.attrib)
            else:
                block.runtime.add_node_as_child(block, child)

        # Attributes become fields.
        for name, value in list(node.items()):  # lxml has no iteritems
            cls._set_field_if_present(block, name, value, {})

        # Text content becomes "content", if such a field exists.
        if "content" in block.fields and block.fields["content"].scope == Scope.content:
            text = node.text
            if text:
                text = text.strip()
                if text:
                    block.content = text

        return block

    def __init__(
        self,
        runtime,
        field_data=None,
        scope_ids=UNSET,
        *args,  # pylint: disable=keyword-arg-before-vararg
        **kwargs
    ):
        """
        Arguments:

            runtime (:class:`.Runtime`): Use it to access the environment.
                It is available in XBlock code as ``self.runtime``.

            field_data (:class:`.FieldData`): Interface used by the XBlock
                fields to access their data from wherever it is persisted.
                Deprecated.

            scope_ids (:class:`.ScopeIds`): Identifiers needed to resolve
                scopes.
        """
        if scope_ids is UNSET:
            raise TypeError('scope_ids are required')

        # A cache of the parent block, retrieved from .parent
        self._parent_block = None
        self._parent_block_id = None
        self._child_cache = {}

        for_parent = kwargs.pop('for_parent', None)
        if for_parent is not None:
            self._parent_block = for_parent
            self._parent_block_id = for_parent.scope_ids.usage_id

        # Provide backwards compatibility for external access through _field_data
        super().__init__(runtime=runtime, scope_ids=scope_ids, field_data=field_data, *args, **kwargs)

    def render(self, view, context=None):
        """Render `view` with this block's runtime and the supplied `context`"""
        return self.runtime.render(self, view, context)

    def validate(self):
        """
        Ask this xblock to validate itself. Subclasses are expected to override this
        method, as there is currently only a no-op implementation. Any overriding method
        should call super to collect validation results from its superclasses, and then
        add any additional results as necessary.
        """
        return Validation(self.scope_ids.usage_id)

    def ugettext(self, text):
        """
        Translates message/text and returns it in a unicode string.
        Using runtime to get i18n service.
        """
        runtime_service = self.runtime.service(self, "i18n")
        runtime_ugettext = runtime_service.ugettext
        return runtime_ugettext(text)

    def add_xml_to_node(self, node):
        """
        For exporting, set data on etree.Element `node`.
        """
        super().add_xml_to_node(node)
        # Add children for each of our children.
        self.add_children_to_node(node)

    def get_parent(self):
        """Return the parent block of this block, or None if there isn't one."""
        if not self.has_cached_parent:
            if self.parent is not None:
                self._parent_block = self.runtime.get_block(self.parent)
            else:
                self._parent_block = None
            self._parent_block_id = self.parent
        return self._parent_block

    @property
    def has_cached_parent(self):
        """Return whether this block has a cached parent block."""
        return self.parent is not None and self._parent_block_id == self.parent

    def get_child(self, usage_id):
        """Return the child identified by ``usage_id``."""
        if usage_id in self._child_cache:
            return self._child_cache[usage_id]

        child_block = self.runtime.get_block(usage_id, for_parent=self)
        self._child_cache[usage_id] = child_block
        return child_block

    def get_children(self, usage_id_filter=None):
        """
        Return instantiated XBlocks for each of this blocks ``children``.
        """
        if not self.has_children:
            return []

        return [
            self.get_child(usage_id)
            for usage_id in self.children
            if usage_id_filter is None or usage_id_filter(usage_id)
        ]

    def clear_child_cache(self):
        """
        Reset the cache of children stored on this XBlock.
        """
        self._child_cache.clear()

    def add_children_to_node(self, node):
        """
        Add children to etree.Element `node`.
        """
        if self.has_children:
            for child_id in self.children:
                child = self.runtime.get_block(child_id)
                self.runtime.add_block_as_child_node(child, node)

    @classmethod
    def supports(cls, *functionalities):
        """
        A view decorator to indicate that an xBlock view has support for the
        given functionalities.

        Arguments:
            functionalities: String identifiers for the functionalities of the view.
                For example: "multi_device".
        """
        def _decorator(view):
            """
            Internal decorator that updates the given view's list of supported
            functionalities.
            """
            # pylint: disable=protected-access
            if not hasattr(view, "_supports"):
                view._supports = set()
            for functionality in functionalities:
                view._supports.add(functionality)
            return view
        return _decorator

    def has_support(self, view, functionality):
        """
        Returns whether the given view has support for the given functionality.

        An XBlock view declares support for a functionality with the
        @XBlock.supports decorator. The decorator stores information on the view.

        Note: We implement this as an instance method to allow xBlocks to
        override it, if necessary.

        Arguments:
            view (object): The view of the xBlock.
            functionality (str): A functionality of the view.
                For example: "multi_device".

        Returns:
            True or False
        """
        return hasattr(view, "_supports") and functionality in view._supports  # pylint: disable=protected-access


@Blocklike.needs("field-data")
class XBlockAside(Plugin, Blocklike):
    """
    Base class for XBlock-like objects that are rendered alongside :class:`.XBlock` views.

    Subclasses of XBlockAside can:

    - Specify which XBlock views they are to be **injected** into.
    - Request **services** from the runtime, for their instances to use.
    - Define scoped **fields**, which instances will use to store content, settings, and data.
    - Define how instances are serialized to and deserialized from **OLX** (Open Learning XML).
    - Mark methods as **handlers** for AJAX requests.
    - Be installed into a platform as an entry-point **plugin**.
    """

    entry_point = "xblock_asides.v1"

    @classmethod
    def aside_for(cls, view_name):
        """
        A decorator to indicate a function is the aside view for the given view_name.

        Aside views should have a signature like::

            @XBlockAside.aside_for('student_view')
            def student_aside(self, block, context=None):
                ...
                return Fragment(...)

        """
        # pylint: disable=protected-access
        def _decorator(func):
            if not hasattr(func, '_aside_for'):
                func._aside_for = []

            func._aside_for.append(view_name)  # pylint: disable=protected-access
            return func
        return _decorator

    @classmethod
    def should_apply_to_block(cls, block):  # pylint: disable=unused-argument
        """
        Return True if the aside should be applied to a given block. This can be overridden
        if some aside should only wrap blocks with certain properties.
        """
        return True

    @class_lazy
    def _combined_asides(cls):  # pylint: disable=no-self-argument
        """
        A dictionary mapping XBlock view names to the aside method that
        decorates them (or None, if there is no decorator for the specified view).
        """
        # The method declares what views it decorates. We rely on `dir`
        # to handle subclasses and overrides.
        combined_asides = defaultdict(None)
        for _view_name, view_func in inspect.getmembers(cls, lambda attr: hasattr(attr, '_aside_for')):
            aside_for = getattr(view_func, '_aside_for', [])
            for view in aside_for:
                combined_asides[view] = view_func.__name__
        return combined_asides

    def aside_view_declaration(self, view_name):
        """
        Find and return a function object if one is an aside_view for the given view_name

        Aside methods declare their view provision via @XBlockAside.aside_for(view_name)
        This function finds those declarations for a block.

        Arguments:
            view_name (str): the name of the view requested.

        Returns:
            either the function or None
        """
        if view_name in self._combined_asides:  # pylint: disable=unsupported-membership-test
            return getattr(self, self._combined_asides[view_name])  # pylint: disable=unsubscriptable-object
        else:
            return None

    def needs_serialization(self):
        """
        Return True if the aside has any data to serialize to XML.

        If all of the aside's data is empty or a default value, then the aside shouldn't
        be serialized as XML at all.
        """
        return any(field.is_set_on(self) for field in self.fields.values())
