from pkg_resources import resource_string
from collections import namedtuple
from webob import Response
from .widget import Widget
from .plugin import Plugin
from .util import call_once_property


def register_view(name):
    return _register_method('view', name)


def register_handler(name):
    return _register_method('handler', name)


def _register_method(registration_type, name):
    def wrapper(fn):
        if not hasattr(fn, '_method_registrations'):
            setattr(fn, '_method_registrations', {})
        fn._method_registrations.setdefault(registration_type, []).append(name)
        return fn
    return wrapper


class MissingXBlockRegistration(Exception):
    pass


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

Int = Float = Boolean = Object = List = String = ModelType


class XBlockMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if attrs.get('has_children', False):
            attrs['children'] = ModelType(help='The children of this XBlock', default=[], scope=None)

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

    def __init__(self, runtime, usage, model_data):
        self.runtime = runtime
        self.usage = usage
        self._model_data = model_data

    def __repr__(self):
        return "<%s @%04X%s>" % (
            self.__class__.__name__,
            id(self) % 0xFFFF,
            ','.join(" %s=%s" % (field.name, getattr(self, field.name)) for field in self.fields)
        )


#-- specific blocks --------

class HelloWorldBlock(XBlock):
    """A simple block: just show some fixed content."""
    @register_view('student_view')
    def student_view(self, context):
        return Widget("Hello, world!")


class VerticalBlock(XBlock):
    """A simple container."""
    has_children = True

    @register_view('student_view')
    def render_student(self, context):
        result = Widget()
        # TODO: self.runtime.children is actual children here, not ids...
        child_widgets = [self.runtime.render_child(child, context) for child in self.children]
        result.add_widgets_resources(child_widgets)
        result.add_content(self.runtime.render_template("vertical.html", children=child_widgets))
        return result


class StaticXBlockMetaclass(XBlockMetaclass):
    def __new__(cls, name, bases, attrs):
        if 'content' in attrs and 'view_names' in attrs and attrs['view_names']:
            @call_once_property
            def _content(self):
                return resource_string(self.__class__.__module__, 'content/' + attrs['content'])

            attrs['_content'] = _content

            def view(self, context):
                widget = Widget(self._content)

                for url, mime_type in attrs.get('urls', []):
                    widget.add_resource_url(self.runtime.handler_url('static') + '/' + url, mime_type)

                if hasattr(self, 'initialize_js'):
                    widget.initialize_js(self.initialize_js)

                return widget

            for view_name in attrs['view_names']:
                view = register_view(view_name)(view)

            attrs['_view'] = view

        attrs['_mime_types_map'] = dict(attrs.get('urls', []))

        @register_handler('static')
        def static_handler(self, request):
            path = request.path_info[1:]
            mime_type = self._mime_types_map[path]
            return Response(body=resource_string(self.__class__.__module__, 'content/' + path), content_type=mime_type)

        attrs['static_handler'] = static_handler

        return super(StaticXBlockMetaclass, cls).__new__(cls, name, bases, attrs)


class StaticXBlock(XBlock):
    __metaclass__ = StaticXBlockMetaclass
