"""Implementation of the XBlock facility.

This code is in the Runtime layer, because it is authored once by edX
and used by all runtimes.

"""

import functools
import json

from collections import namedtuple
from webob import Response

from .plugin import Plugin
from .util import call_once_property

class BlockScope(object):
    USAGE, DEFINITION, TYPE, ALL = xrange(4)


class Scope(namedtuple('ScopeBase', 'student block')):
    pass

Scope.content = Scope(student=False, block=BlockScope.DEFINITION)
Scope.settings = Scope(student=False, block=BlockScope.USAGE)
Scope.student_state = Scope(student=True, block=BlockScope.USAGE)
Scope.student_preferences = Scope(student=True, block=BlockScope.TYPE)
Scope.student_info = Scope(student=True, block=BlockScope.ALL)


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
        self.default = default
        self.computed_default = computed_default
        self.scope = scope
        ModelType.sequence += 1

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

    def __lt__(self, other):
        return self._seq < other._seq

    def to_json(self, value):
        return value

    def from_json(self, value):
        return value

Integer = Float = Boolean = Object = List = String = Any = ModelType


class ModelMetaclass(type):
    """
    A metaclass to be used for classes that want to use ModelTypes as class attributes
    to define data access.

    All class attributes that are ModelTypes will be added to the 'fields' attribute on
    the instance.

    Additionally, any namespaces registered in the `xblock.namespace` will be added to
    the instance
    """
    def __new__(cls, name, bases, attrs):
        fields = []
        for n, v in attrs.items():
            if isinstance(v, ModelType):
                v._name = n
                fields.append(v)
        fields.sort()
        attrs['fields'] = fields

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


class ParentModelMetaclass(type):
    """
    A ModelMetaclass that transforms the attribute `has_children = True`
    into a List field with an empty scope.
    """
    def __new__(cls, name, bases, attrs):
        if attrs.get('has_children', False):
            attrs['children'] = List(help='The children of this XBlock', default=[], scope=Scope.settings)
        else:
            attrs['has_children'] = False

        return super(ParentModelMetaclass, cls).__new__(cls, name, bases, attrs)


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

class MethodRegistrationMetaclass(type):
    def __new__(cls, name, bases, attrs):
        # Find registered methods
        reg_methods = {}
        for value in attrs.itervalues():
            for reg_type, names in getattr(value, "_method_registrations", {}).iteritems():
                for n in names:
                    reg_methods[reg_type + n] = value
        attrs['registered_methods'] = reg_methods

        return super(MethodRegistrationMetaclass, cls).__new__(cls, name, bases, attrs)


class XBlockMetaclass(MethodRegistrationMetaclass,
                      ParentModelMetaclass,
                      NamespacesMetaclass,
                      ModelMetaclass):
    pass


# -- Caching tools

def _set_cache_info(f, **kwargs):
    if not hasattr(f, '_cache'):
        f._cache = {}
    f._cache.update(kwargs)

def varies_on_model(*attrs):
    # key = (getattr(self, attr) for attr in attrs)
    def _dec(f):
        _set_cache_info(f, model=attrs)
        return f
    return _dec

def varies_on_children(f):
    # not sure how to do this yet...
    # _set_cache_info(f, children=True)
    return f

def varies_on_block(type):
    """Use 'usage', 'definition', or 'none'."""
    def _dec(f):
        _set_cache_info(f, id=type)
        return f
    return _dec

def expires(hours=0, minutes=0, seconds=0):
    # cache expiration
    def _dec(f):
        _set_cache_info(f, seconds=hours*3600+minutes*60+seconds)
        return f
    return _dec


# -- Base Block


class XBlock(Plugin):
    __metaclass__ = XBlockMetaclass

    entry_point = 'xblock.v1'

    name = String(help="Short name for the block", scope=Scope.settings)

    @classmethod
    def _register_method(cls, registration_type, name):
        def wrapper(fn):
            if not hasattr(fn, '_method_registrations'):
                setattr(fn, '_method_registrations', {})
            fn._method_registrations.setdefault(registration_type, []).append(name)
            return fn
        return wrapper

    @classmethod
    def view(cls, name):
        return cls._register_method('view', name)

    @classmethod
    def handler(cls, name):
        return cls._register_method('handler', name)

    @classmethod
    def json_handler(cls, name):
        def wrap(fn):
            @XBlock.handler(name)
            @functools.wraps(fn)
            def wrapper(self, request):
                request_json = json.loads(request.body)
                response_json = json.dumps(fn(self, request_json))
                return Response(response_json, content_type='application/json')

            return wrapper
        return wrap

    def __init__(self, runtime, usage, model_data):
        self.runtime = runtime
        self.usage = usage
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
