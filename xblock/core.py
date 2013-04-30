"""Implementation of the XBlock facility.

This code is in the Runtime layer, because it is authored once by edX
and used by all runtimes.

"""
import copy
import functools
import inspect
try:
    import simplesjson as json
except ImportError:
    import json

from collections import namedtuple
from webob import Response

from .plugin import Plugin


class BlockScope(object):
    USAGE, DEFINITION, TYPE, ALL = xrange(4)


class Scope(namedtuple('ScopeBase', 'user block')):
    pass


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


Scope.content = Scope(user=False, block=BlockScope.DEFINITION)
Scope.settings = Scope(user=False, block=BlockScope.USAGE)
Scope.user_state = Scope(user=True, block=BlockScope.USAGE)
Scope.preferences = Scope(user=True, block=BlockScope.TYPE)
Scope.user_info = Scope(user=True, block=BlockScope.ALL)
Scope.children = Sentinel('Scope.children')
Scope.parent = Sentinel('Scope.parent')

# define a placeholder ('nil') value to indicate when nothing has been stored in
# the cache.  ("None" may be a valid value in the cache, so we cannot use it.)
NO_CACHE_VALUE = object()


class ModelType(object):
    """
    A field class that can be used as a class attribute to define what data the class will want
    to refer to.

    When the class is instantiated, it will be available as an instance attribute of the same
    name, by proxying through to self._model_data on the containing object.

    Parameters:
      `help` : documentation of field class, suitable for presenting in a GUI (defaults to None)
      `default` : static value to default to if not otherwise specified (defaults to None)
      `scope` : the scope in which this field class is used (defaults to Scope.content)
      `computed_default` : provides the ability to specify a function for computing a default value (defaults to None)
      `display_name` : the display name for the field class, suitable for presenting in a GUI (defaults to name of class)
      `values` : for field classes with a finite number of valid values, provides the ability to specify the set of
               valid values. This can be specified as either a static return value, or a function that generates
               the valid values.
    """

    def __init__(self, help=None, default=None, scope=Scope.content, computed_default=None, display_name=None,
                 values=None):
        self._name = "unknown"
        self.help = help
        self._default = default
        self.computed_default = computed_default
        self.scope = scope
        self._display_name = display_name
        self._values = values

    @property
    def default(self):
        return self._default

    @property
    def name(self):
        return self._name

    @property
    def values(self):
        """
        Returns the valid values for this class.

        If this field class does not define a finite number of valid values, this method will return None.
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
        if not hasattr(instance, '_model_data_cache'):
            instance._model_data_cache = {}
        instance._model_data_cache[self.name] = value

    def _del_cached_value(self, instance):
        """Remove a value from the instance's cache, if the cache exists."""
        if hasattr(instance, '_model_data_cache') and self.name in instance._model_data_cache:
            del instance._model_data_cache[self.name]

    def _use_computed_default(self):
        """Returns boolean indicating if a default value can/should be computed"""
        # Check self._default to see if a default was provided (and not
        # self.default, since that property may be redefined).
        return self._default is None and self.computed_default is not None

    def __get__(self, instance, owner):
        if instance is None:
            return self

        value = self._get_cached_value(instance)
        if value is NO_CACHE_VALUE:
            try:
                value = self.from_json(instance._model_data[self.name])
                self._set_cached_value(instance, value)
            except KeyError:
                # Computed defaults are not stored in cache, but are
                # always recomputed.  Regular defaults are always copied,
                # in case the provided default value is mutable (e.g list or
                # dict).  Regular defaults are also cached.
                if self._use_computed_default():
                    value = self.computed_default(instance)
                else:
                    value = copy.deepcopy(self.default)
                    self._set_cached_value(instance, value)

        return value

    def __set__(self, instance, value):
        # Update both the persistent store and the cache:
        instance._model_data[self.name] = self.to_json(value)
        self._set_cached_value(instance, value)

    def __delete__(self, instance):
        # Try to perform the deletion on the model_data, and accept
        # that it's okay if the key is not present.  (It may never
        # have been persisted at all.)
        try:
            del instance._model_data[self.name]
        except KeyError:
            pass

        # Since we know that the model_data no longer contains the value, we can
        # avoid the possible database lookup that a future get() call would
        # entail by setting the cached value now to its default value.
        # However, we should not store cached values for computed defaults, so
        # we just clear the cache in that case.
        if self._use_computed_default():
            self._del_cached_value(instance)
        else:
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
    pass


class Float(ModelType):
    pass


class Boolean(ModelType):
    pass


class Object(ModelType):
    @property
    def default(self):
        if self._default is None:
            return {}
        else:
            return self._default


class List(ModelType):
    @property
    def default(self):
        if self._default is None:
            return []
        else:
            return self._default


class String(ModelType):
    pass


class Any(ModelType):
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
    def __new__(cls, name, bases, attrs):
        fields = set()
        for n, v in attrs.items() + sum([inspect.getmembers(base) for base in bases], []):
            if isinstance(v, ModelType):
                v._name = n
                fields.add(v)

        attrs['fields'] = list(fields)
        return super(ModelMetaclass, cls).__new__(cls, name, bases, attrs)


class NamespacesMetaclass(type):
    """
    A metaclass to be used for classes that want to include namespaced fields in their
    instances.

    Any namespaces registered in the `xblock.namespace` will be added to
    the instance
    """
    def __new__(cls, name, bases, attrs):
        namespaces = []
        for ns_name, namespace in Namespace.load_classes():
            if issubclass(namespace, Namespace):
                attrs[ns_name] = NamespaceDescriptor(namespace)
                namespaces.append(ns_name)
        attrs['namespaces'] = namespaces

        return super(NamespacesMetaclass, cls).__new__(cls, name, bases, attrs)


class ChildrenModelMetaclass(type):
    """
    A ModelMetaclass that transforms the attribute `has_children = True`
    into a List field with an empty scope.
    """
    def __new__(cls, name, bases, attrs):
        if (attrs.get('has_children', False) or
            any(getattr(base, 'has_children', False) for base in bases)):
            attrs['children'] = List(help='The ids of the children of this XBlock', scope=Scope.children)
        else:
            attrs['has_children'] = False

        return super(ChildrenModelMetaclass, cls).__new__(cls, name, bases, attrs)


class NamespaceDescriptor(object):
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
    def __new__(cls, name, bases, attrs):
        class_tags = set([])
        # Collect the tags from all base classes.
        for base in bases:
            try:
                class_tags.update(base._class_tags)
            except AttributeError:
                # Base classes may have no ._class_tags, that's ok.
                pass
        attrs['_class_tags'] = class_tags
        return super(TagCombiningMetaclass, cls).__new__(cls, name, bases, attrs)


class XBlockMetaclass(
    ChildrenModelMetaclass,
    NamespacesMetaclass,
    ModelMetaclass,
    TagCombiningMetaclass,
    ):
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

    parent = Object(help='The id of the parent of this XBlock', default=None, scope=Scope.parent)
    name = String(help="Short name for the block", scope=Scope.settings)
    tags = List(help="Tags for this block", scope=Scope.settings)

    _class_tags = set()

    @classmethod
    def json_handler(cls, fn):
        """Wrap a handler to consume and produce JSON.

        Rather than a Request object, the method will now be passed the
        JSON-decoded body of the request.  Any data returned by the function
        will be JSON-encoded and returned as the response.

        """
        @functools.wraps(fn)
        def wrapper(self, request):
            request_json = json.loads(request.body)
            response_json = json.dumps(fn(self, request_json))
            return Response(response_json, content_type='application/json')
        return wrapper

    @classmethod
    def tag(cls, tags):
        """Add the words in `tags` as class tags to this class."""
        def dec(cls):
            # Add in this class's tags
            cls._class_tags.update(tags.replace(",", " ").split())
            return cls
        return dec

    @classmethod
    def load_tagged_classes(cls, tag):
        """Produce a sequence of all XBlock classes tagged with `tag`."""
        for name, class_ in cls.load_classes():
            if tag in class_._class_tags:
                yield name, class_

    @classmethod
    def preprocess_input(cls, node, usage_factory):
        """The class can adjust a parsed Usage tree."""
        return node

    @classmethod
    def postprocess_input(cls, node, usage_factory):
        """The class can adjust a parsed Usage tree."""
        return node

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

    def __repr__(self):
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
