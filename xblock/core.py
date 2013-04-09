"""Implementation of the XBlock facility.

This code is in the Runtime layer, because it is authored once by edX
and used by all runtimes.

"""

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


class ModelType(object):
    """
    A field class that can be used as a class attribute to define what data the class will want
    to refer to.

    When the class is instantiated, it will be available as an instance attribute of the same
    name, by proxying through to self._model_data on the containing object.
    """
    sequence = 0

    def __init__(self, help=None, default=None, scope=Scope.content, computed_default=None):
        self._seq = ModelType.sequence
        self._name = "unknown"
        self.help = help
        self._default = default
        self.computed_default = computed_default
        self.scope = scope
        ModelType.sequence += 1

    @property
    def default(self):
        return self._default

    @property
    def name(self):
        return self._name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        try:
            return self.from_json(instance._model_data[self.name])
        except KeyError:
            if self.default is None and self.computed_default is not None:
                return self.computed_default(instance)

            return self.default

    def __set__(self, instance, value):
        instance._model_data[self.name] = self.to_json(value)

    def __delete__(self, instance):
        del instance._model_data[self.name]

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

    def __cmp__(self, other):
        return cmp((self._seq, self.name), (other._seq, other.name))

    def __eq__(self, other):
        return self.name == other.name


class Integer(ModelType): pass
class Float(ModelType): pass
class Boolean(ModelType): pass

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

class String(ModelType): pass
class Any(ModelType): pass


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

        attrs['fields'] = sorted(fields)
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
