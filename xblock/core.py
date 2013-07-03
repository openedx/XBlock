"""Implementation of the XBlock facility.

This code is in the Runtime layer, because it is authored once by edX
and used by all runtimes.

"""
import copy
import functools
import inspect
# Disable pylint from catching the ImportError because we handle it.
# pylint: disable=F0401
try:
    import simplesjson as json
except ImportError:
    import json
# pylint: enable=F0401
from collections import namedtuple
from webob import Response

from .plugin import Plugin


class KeyValueMultiSaveError(Exception):
    """
    Raised to indicated an error in saving multiple fields in a KeyValueStore
    """
    def __init__(self, saved_field_names):
        """
        Create a new KeyValueMultiSaveError

        `saved_field_names` - an iterable of field names that were
        successfully saved before the exception occured
        """
        super(KeyValueMultiSaveError, self).__init__()
        self.saved_field_names = saved_field_names


class XBlockSaveError(Exception):
    """
    Raised to indicated an error in saving an XBlock
    """
    def __init__(self, saved_fields, dirty_fields):
        """
        Create a new XBlockSaveError

        `saved_fields` - a set of fields that were successfully
        saved before the error occured
        `dirty_fields` - a set of fields that were left dirty after the save
        """
        super(XBlockSaveError, self).__init__()
        self.saved_fields = saved_fields
        self.dirty_fields = dirty_fields


class BlockScope(object):
    """Enumeration defining BlockScopes"""
    USAGE, DEFINITION, TYPE, ALL = xrange(4)


class Sentinel(object):
    """
    Class for implementing sentinel objects (only equal to themselves).
    """
    def __init__(self, name):
        """
        `name` is the name used to identify the sentinel (which will
            be displayed as the __repr__) of the sentinel.
        """
        self.name = name

    def __repr__(self):
        return self.name

# Allow this tuple to be named as if it were a class
# pylint: disable=C0103
ScopeBase = namedtuple('ScopeBase', 'user block')
# pylint: enable=C0103


class Scope(ScopeBase):
    """
    Defines five types of Scopes to be used: `content`, `settings`,
    `user_state`, `preferences`, and `user_info`.

    The `content` scope is used to save data for all users, for one particular
    block, across all runs of a course. An example might be an XBlock that
    wishes to tabulate user "upvotes", or HTML content ti display literally on
    the page (this example being the reason this scope is named `content`).

    The `settings` scope is used to save data for all users, for one particular block,
    for one specific run of a course. This is like the `content` scope, but scoped to
    one run of a course. An example might be a due date for a problem.

    The `user_state` scope is used to save data for one user, for one block, for one run
    of a course. An example might be how many points a user scored on one specific problem.

    The `preferences` scope is used to save data for one user, for all instances of one
    specific TYPE of block, across the entire platform. An example might be that a user
    can set their preferred default speed for the video player. This default would apply
    to all instances of the video player, across the whole platform, but only for that student.

    The `user_info` scope is used to save data for one user, across the entire platform. An
    example might be a user's time zone or language preference.

    """

    content = ScopeBase(user=False, block=BlockScope.DEFINITION)
    settings = ScopeBase(user=False, block=BlockScope.USAGE)
    user_state = ScopeBase(user=True, block=BlockScope.USAGE)
    preferences = ScopeBase(user=True, block=BlockScope.TYPE)
    user_info = ScopeBase(user=True, block=BlockScope.ALL)

    children = Sentinel('Scope.children')
    parent = Sentinel('Scope.parent')

# define a placeholder ('nil') value to indicate when nothing has been stored
# in the cache ("None" may be a valid value in the cache, so we cannot use it).
NO_CACHE_VALUE = object()


class ModelType(object):
    """
    A field class that can be used as a class attribute to define what data the
    class will want to refer to.

    When the class is instantiated, it will be available as an instance
    attribute of the same name, by proxying through to self._model_data on
    the containing object.

    Parameters:
      `help` : documentation of field class, suitable for presenting in a GUI
               (defaults to None)
      `default` : static value to default to if not otherwise specified
                  (defaults to None)
      `scope` : the scope in which this field class is used (defaults to
                Scope.content)
      `display_name` : the display name for the field class, suitable for
                       presenting in a GUI (defaults to name of class)
      `values` : for field classes with a known set of valid values, provides
                 the ability to explicitly specify the valid values. This can
                 be specified as either a static return value, or a function
                 that generates the valid values. For example formats, see the
                 values property definition.
    """

    # We're OK redefining built-in `help`
    # pylint: disable=W0622
    def __init__(self, help=None, default=None, scope=Scope.content,
                 display_name=None, values=None):
        self._name = "unknown"
        self.help = help
        self._default = default
        self.scope = scope
        self._display_name = display_name
        self._values = values
    # pylint: enable=W0622

    @property
    def default(self):
        """Returns the static value that this defaults to."""
        return self._default

    @property
    def name(self):
        """
        Returns the `_name` of this object. Set to 'unknown'.
        Not to be confused with `display_name`.
        """
        return self._name

    @property
    def values(self):
        """
        Returns the valid values for this class. This is useful
        for representing possible values in a UI.

        Example formats:
            `[1, 2, 3]` : a finite set of elements
            `[{"display_name": "Always", "value": "always"},
              {"display_name": "Past Due", "value": "past_due"}]` :
                a finite set of elements where the display names differ from
                the values
            `{"min" : 0 , "max" : 10, "step": .1}` :
                a range for floating point numbers with increment .1

        If this field class does not define a set of valid values, this method
        will return None.
        """
        if callable(self._values):
            return self._values()
        else:
            return self._values

    @property
    def display_name(self):
        """
        Returns the display name for this class, suitable for use in a GUI.

        If no display name has been set, returns the name of the class.
        """
        return self._display_name if self._display_name is not None else self.name

    def _get_cached_value(self, instance):
        """
        Return a value from the instance's cache, or a marker value if either the cache
        doesn't exist or the value is not found in the cache.
        """
        return getattr(instance, '_model_data_cache', {}).get(self.name, NO_CACHE_VALUE)

    def _set_cached_value(self, instance, value):
        """Store a value in the instance's cache, creating the cache if necessary."""
        # Allow this method to access the `_model_data_cache` of `instance`
        # pylint: disable=W0212
        if not hasattr(instance, '_model_data_cache'):
            instance._model_data_cache = {}
        instance._model_data_cache[self.name] = value

    def _del_cached_value(self, instance):
        """Remove a value from the instance's cache, if the cache exists."""
        # Allow this method to access the `_model_data_cache` of `instance`
        # pylint: disable=W0212
        if hasattr(instance, '_model_data_cache') and self.name in instance._model_data_cache:
            del instance._model_data_cache[self.name]

    def _mark_dirty(self, instance):
        """Set this field to dirty on the instance."""
        # Allow this method to access the `_dirty_fields` of `instance`
        # pylint: disable=W0212
        instance._dirty_fields.add(self)

    def __get__(self, instance, owner):
        """
        Gets the value of this instance. Prioritizes the cached value over
        obtaining the value from the _model_data. Thus if a cached value
        exists, that is the value that will be returned.
        """
        # Allow this method to access the `_model_data_cache` of `instance`
        # pylint: disable=W0212
        if instance is None:
            return self

        value = self._get_cached_value(instance)
        if value is NO_CACHE_VALUE:
            try:
                value = self.from_json(instance._model_data[self.name])
                self._set_cached_value(instance, value)
            except KeyError:
                # Defaults are always copied, in case the provided default value
                # is mutable (e.g list or dict).  Defaults are also cached.
                value = copy.deepcopy(self.default)
                self._set_cached_value(instance, value)

        return value

    def __set__(self, instance, value):
        """
        Sets the `instance` to the given `value`.
        Setting a value does not update the underlying data store; the
        new value is kept in the cache and the instance is marked as
        dirty until `save` is explicitly called.
        """
        # Mark the field as dirty and update the cache:
        self._mark_dirty(instance)
        self._set_cached_value(instance, value)

    def __delete__(self, instance):
        """
        Deletes `instance` from the underlying data store.
        Deletes are not cached; they are performed immediately.
        """
        # Allow this method to access the `_model_data_cache` and `_dirty_fields` of `instance`
        # pylint: disable=W0212

        # Try to perform the deletion on the model_data, and accept
        # that it's okay if the key is not present.  (It may never
        # have been persisted at all.)
        try:
            del instance._model_data[self.name]
        except KeyError:
            pass

        # We also need to clear this item from the dirty fields, to prevent
        # an erroneous write of its value on implicit save. OK if it was
        # not in the dirty fields to begin with.
        try:
            instance._dirty_fields.remove(self)
        except KeyError:
            pass

        # Since we know that the model_data no longer contains the value, we can
        # avoid the possible database lookup that a future get() call would
        # entail by setting the cached value now to its default value.
        self._set_cached_value(instance, copy.deepcopy(self.default))

    def __repr__(self):
        return "<{0.__class__.__name__} {0._name}>".format(self)

    def to_json(self, value):
        """
        Return value in the form of nested lists and dictionaries (suitable
        for passing to json.dumps).

        This is called during field writes to convert the native python
        type to the value stored in the database
        """
        return value

    def from_json(self, value):
        """
        Return value as a native full featured python type (the inverse of to_json)

        Called during field reads to convert the stored value into a full featured python
        object
        """
        return value

    def read_from(self, model):
        """
        Retrieve the value for this field from the specified model object
        """
        return self.__get__(model, model.__class__)

    def read_json(self, model):
        """
        Retrieve the serialized value for this field from the specified model object
        """
        return self.to_json(self.read_from(model))

    def write_to(self, model, value):
        """
        Set the value for this field to value on the supplied model object
        """
        self.__set__(model, value)

    def delete_from(self, model):
        """
        Delete the value for this field from the supplied model object
        """
        self.__delete__(model)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name


class Integer(ModelType):
    """
    A model type that contains an integer.

    The value, as stored, can be None, '' (which will be treated as None), a Python integer,
    or a value that will parse as an integer, ie., something for which int(value) does not throw an Error.

    Note that a floating point value will convert to an integer, but a string containing a floating point
    number ('3.48') will throw an Error.
    """
    def from_json(self, value):
        if value is None or value == '':
            return None
        return int(value)


class Float(ModelType):
    """
    A model type that contains a float.

    The value, as stored, can be None, '' (which will be treated as None), a Python float,
    or a value that will parse as an float, ie., something for which float(value) does not throw an Error.
    """
    def from_json(self, value):
        if value is None or value == '':
            return None
        return float(value)


class Boolean(ModelType):
    """
    A field class for representing a boolean.

    The stored value can be either a Python bool, a string, or any value that will then be converted
    to a bool in the from_json method.

    Examples:
        True -> True
        'true' -> True
        'TRUE' -> True
        'any other string' -> False
        [] -> False
        ['123'] -> True
        None - > False

    This class has the 'values' property defined.
    """
    # We're OK redefining built-in `help`
    # pylint: disable=W0622
    def __init__(self, help=None, default=None, scope=Scope.content, display_name=None):
        super(Boolean, self).__init__(help, default, scope, display_name,
                                      values=({'display_name': "True", "value": True},
                                              {'display_name': "False", "value": False}))
    # pylint: enable=W0622

    def from_json(self, value):
        if isinstance(value, basestring):
            return value.lower() == 'true'
        else:
            return bool(value)


class Dict(ModelType):
    """
    A field class for representing a Python dict.

    The stored value must be either be None or a dict.
    """
    @property
    def default(self):
        if self._default is None:
            return {}
        else:
            return self._default

    def from_json(self, value):
        if value is None or isinstance(value, dict):
            return value
        else:
            raise TypeError('Value stored in a Dict must be None or a dict.')


class List(ModelType):
    """
    A field class for representing a list.

    The stored value can either be None or a list.
    """
    @property
    def default(self):
        if self._default is None:
            return []
        else:
            return self._default

    def from_json(self, value):
        if value is None or isinstance(value, list):
            return value
        else:
            raise TypeError('Value stored in an Object must be None or a list.')


class String(ModelType):
    """
    A field class for representing a string.

    The stored value can either be None or a basestring instance.
    """
    def from_json(self, value):
        if value is None or isinstance(value, basestring):
            return value
        else:
            raise TypeError('Value stored in a String must be None or a String.')


class Any(ModelType):
    """
    A field class for representing any piece of data; type is not enforced.

    All methods are inherited directly from `ModelType`.
    """
    pass


class ModelMetaclass(type):
    """
    A metaclass to be used for classes that want to use ModelTypes as class attributes
    to define data access.

    All class attributes that are ModelTypes will be added to the 'fields' attribute on
    the instance.

    Additionally, any namespaces registered in the `xblock.namespace` will be added to
    the instance.
    """
    def __new__(mcs, name, bases, attrs):
        # Allow this method to access `_name`
        # pylint: disable=W0212
        fields = set()
        for vname, value in attrs.items() + sum([inspect.getmembers(base) for base in bases], []):
            if isinstance(value, ModelType):
                value._name = vname
                fields.add(value)

        attrs['fields'] = list(fields)
        return super(ModelMetaclass, mcs).__new__(mcs, name, bases, attrs)


class NamespacesMetaclass(type):
    """
    A metaclass to be used for classes that want to include namespaced fields in their
    instances.

    Any namespaces registered in the `xblock.namespace` will be added to
    the instance
    """
    def __new__(mcs, name, bases, attrs):
        namespaces = []
        for ns_name, namespace in Namespace.load_classes():
            if issubclass(namespace, Namespace):
                attrs[ns_name] = NamespaceDescriptor(namespace)
                namespaces.append(ns_name)
        attrs['namespaces'] = namespaces

        return super(NamespacesMetaclass, mcs).__new__(mcs, name, bases, attrs)


class ChildrenModelMetaclass(type):
    """
    A ModelMetaclass that transforms the attribute `has_children = True`
    into a List field with an empty scope.
    """
    def __new__(mcs, name, bases, attrs):
        if (attrs.get('has_children', False) or
                any(getattr(base, 'has_children', False) for base in bases)):
            attrs['children'] = List(help='The ids of the children of this XBlock',
                                     scope=Scope.children)
        else:
            attrs['has_children'] = False

        return super(ChildrenModelMetaclass, mcs).__new__(mcs, name, bases, attrs)


class NamespaceDescriptor(object):
    """
    Holds the descriptor for namespaces. Used by `NamespacesMetaclass` to
    define new namespaces.
    """
    def __init__(self, namespace):
        self._namespace = namespace

    def __get__(self, instance, owner):
        return self._namespace(instance)


class Namespace(Plugin):
    """
    A baseclass that sets up machinery for ModelType fields that makes those fields be called
    with the container as the field instance
    """
    __metaclass__ = ModelMetaclass

    entry_point = 'xblock.namespace'

    def __init__(self, container):
        self._container = container

    def __getattribute__(self, name):
        container = super(Namespace, self).__getattribute__('_container')
        namespace_attr = getattr(type(self), name, None)

        if namespace_attr is None or not isinstance(namespace_attr, ModelType):
            return super(Namespace, self).__getattribute__(name)

        return namespace_attr.__get__(container, type(container))

    def __setattr__(self, name, value):
        try:
            container = super(Namespace, self).__getattribute__('_container')
        except AttributeError:
            super(Namespace, self).__setattr__(name, value)
            return

        namespace_attr = getattr(type(self), name, None)

        if namespace_attr is None or not isinstance(namespace_attr, ModelType):
            return super(Namespace, self).__setattr__(name, value)

        return namespace_attr.__set__(container, value)

    def __delattr__(self, name):
        container = super(Namespace, self).__getattribute__('_container')
        namespace_attr = getattr(type(self), name, None)

        if namespace_attr is None or not isinstance(namespace_attr, ModelType):
            return super(Namespace, self).__detattr__(name)

        return namespace_attr.__delete__(container)


class TagCombiningMetaclass(type):
    """
    Collects and combines `._class_tags` from all base classes and
    puts them together in one `.class_tags` attribute.
    """
    def __new__(mcs, name, bases, attrs):
        # Allow this method to access the `_class_tags`
        # pylint: disable=W0212
        class_tags = set([])
        # Collect the tags from all base classes.
        for base in bases:
            try:
                class_tags.update(base._class_tags)
            except AttributeError:
                # Base classes may have no ._class_tags, that's ok.
                pass
        attrs['_class_tags'] = class_tags
        return super(TagCombiningMetaclass, mcs).__new__(mcs, name, bases, attrs)


class XBlockMetaclass(
        ChildrenModelMetaclass,
        NamespacesMetaclass,
        ModelMetaclass,
        TagCombiningMetaclass,
):
    """
    Metaclass that combines the four base XBlock metaclasses:
    * `ChildrenModelMetaclass`
    * `NamespacesMetaclass`
    * `ModelMetaclass`
    * `TagCombiningMetaclass`
    """
    pass


# -- Base Block


class XBlock(Plugin):
    """Base class for XBlocks.

    Derive from this class to create a new kind of XBlock.  There are no
    required methods, but you will probably need at least one view.

    Don't provide the ``__init__`` method when deriving from this class.

    """

    __metaclass__ = XBlockMetaclass

    entry_point = 'xblock.v1'

    parent = String(help='The id of the parent of this XBlock', default=None, scope=Scope.parent)
    name = String(help="Short name for the block", scope=Scope.settings)
    tags = List(help="Tags for this block", scope=Scope.settings)

    _class_tags = set()

    @classmethod
    def json_handler(cls, func):
        """Wrap a handler to consume and produce JSON.

        Rather than a Request object, the method will now be passed the
        JSON-decoded body of the request.  Any data returned by the function
        will be JSON-encoded and returned as the response.

        """
        @functools.wraps(func)
        def wrapper(self, request):
            """The wrapper function `json_handler` returns."""
            request_json = json.loads(request.body)
            response_json = json.dumps(func(self, request_json))
            return Response(response_json, content_type='application/json')
        return wrapper

    @classmethod
    def tag(cls, tags):
        """Returns a function that adds the words in `tags` as class tags to this class."""
        def dec(cls):
            """Add the words in `tags` as class tags to this class."""
            # Add in this class's tags
            cls._class_tags.update(tags.replace(",", " ").split())
            return cls
        return dec

    @classmethod
    def load_tagged_classes(cls, tag):
        """Produce a sequence of all XBlock classes tagged with `tag`."""
        # Allow this method to access the `_class_tags`
        # pylint: disable=W0212
        for name, class_ in cls.load_classes():
            if tag in class_._class_tags:
                yield name, class_

    # Ignore unused argument: `usage_factory` complaint.
    # pylint: disable=W0613
    @classmethod
    def preprocess_input(cls, node, usage_factory):
        """The class can adjust a parsed Usage tree."""
        return node
    # pylint: enable=W0613

    # Ignore unused argument: `usage_factory` complaint.
    # pylint: disable=W0613
    @classmethod
    def postprocess_input(cls, node, usage_factory):
        """The class can adjust a parsed Usage tree."""
        return node
    # pylint: enable=W0613

    def save(self):
        """Save all dirty fields attached to this XBlock."""
        if not self._dirty_fields:
            # nop if _dirty_fields attribute is empty
            return
        # `XBlock` obtains the `_model_data_cache` attribute from TODO [sarina/dkh]
        # Since this is not understood by static analysis, silence this error.
        # pylint: disable=E1101
        try:
            # Create dictionary mapping between dirty fields and data cache values
            # A `field` is an instance of `ModelType`
            fields_to_save = {field.name: field.to_json(self._model_data_cache[field.name])
                              for field in self._dirty_fields}
            # Throws KeyValueMultiSaveError if things go wrong
            self._model_data.update(fields_to_save)

        except KeyValueMultiSaveError as save_error:
            saved_fields = [field for field in self._dirty_fields if field.name in save_error.saved_field_names]

            for field in saved_fields:
                # should only find one corresponding field
                self._dirty_fields.remove(field)
            raise XBlockSaveError(saved_fields, self._dirty_fields)

        # Remove all dirty fields, since the save was successful
        self._clear_dirty_fields()

    def _clear_dirty_fields(self):
        """
        Remove all dirty fields from an XBlock
        """
        self._dirty_fields.clear()

    def __init__(self, runtime, model_data):
        """
        `runtime` is an instance of :class:`xblock.core.Runtime`. Use it to
        access the environment.  It is available in XBlock code as
        ``self.runtime``.

        `model_data` is a dictionary-like interface to runtime storage.
        XBlock uses it to implement your storage fields.

        """
        self.runtime = runtime
        self._model_data = model_data
        self._dirty_fields = set()

    def __repr__(self):
        # `XBlock` obtains the `fields` attribute from the `ModelMetaclass`.
        # Since this is not understood by static analysis, silence this error.
        # pylint: disable=E1101
        attrs = []
        for field in self.fields:
            value = getattr(self, field.name)
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
