"""Core definitions for XBlocks."""

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
Scope.student_state = Scope(student=True, block=BlockScope.USAGE)
Scope.settings = Scope(student=True, block=BlockScope.USAGE)
Scope.student_preferences = Scope(student=True, block=BlockScope.TYPE)
Scope.student_info = Scope(student=True, block=BlockScope.ALL)


class ModelType(object):
    sequence = 0

    def __init__(self, help=None, default=None, scope=Scope.content):
        self._seq = self.sequence
        self._name = "unknown"
        self.help = help
        self.default = default
        self.scope = scope
        ModelType.sequence += 1

    @property
    def name(self):
        return self._name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance._model_data.get(self.name, self.default)

    def __set__(self, instance, value):
        instance._model_data[self.name] = value

    def __delete__(self, instance):
        del instance._model_data[self.name]

    def __repr__(self):
        return "<{0.__class__.__name} {0.__name__}>".format(self)

    def __lt__(self, other):
        return self._seq < other._seq

Int = Float = Boolean = Object = List = String = Any = ModelType


class XBlockMetaclass(type):
    def __new__(cls, name, bases, attrs):
        # Find registered methods
        reg_methods = {}
        for value in attrs.itervalues():
            for reg_type, names in getattr(value, "_method_registrations", {}).iteritems():
                for n in names:
                    reg_methods[reg_type + n] = value
        attrs['registered_methods'] = reg_methods

        if attrs.get('has_children', False):
            attrs['children'] = ModelType(help='The children of this XBlock', default=[], scope=None)
            @call_once_property
            def child_map(self):
                return dict((child.name, child) for child in self.children)
            attrs['child_map'] = child_map

        fields = []
        for n, v in attrs.items():
            if isinstance(v, ModelType):
                v._name = n
                fields.append(v)
        fields.sort()
        attrs['fields'] = fields

        return super(XBlockMetaclass, cls).__new__(cls, name, bases, attrs)

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

    name = String(help="Short name for the block", scope=Scope.content)

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
