import inspect
import itertools
from collections import MutableMapping

from django.template import loader as django_template_loader, Context as DjangoContext
from django.core.cache import cache

from xblock.core import XBlock, register_view, MissingXBlockRegistration, BlockScope, Scope, ModelType
from xblock.widget import Widget

from .util import call_once_property

class Usage(object):
    # Not the real way we'll store usages!
    ids = itertools.count()
    usage_index = {}

    def __init__(self, block_name, def_id, child_specs):
        self.id = "usage_%d" % next(self.ids)
        self.block_name = block_name
        self.def_id = def_id
        self.child_specs = child_specs
        self.usage_index[self.id] = self

    def __repr__(self):
        return "<{0.__class__.__name__} {0.id} {0.block_name} {0.def_id} {0.child_specs!r}>".format(self)

    @classmethod
    def find_usage(cls, usage_id):
        return cls.usage_index[usage_id]

class KeyValueStore(object):
    """The abstract interface for Key Value Stores."""
    def get(key, name):
        pass

    def set(key, name, value):
        pass

    def delete(key, name):
        pass


DATABASE = {}

class MemoryKeyValueStore(KeyValueStore):
    """Use an in-memory database for a key-value store."""
    def __init__(self, d):
        self.d = d

    def get(self, key, name):
        return self.d[key][name]

    def set(self, key, name, value):
        self.d.setdefault(key, {})[name] = value

    def delete(self, key, name):
        del self.d[key][name]

MEMORY_KVS = MemoryKeyValueStore(DATABASE)

def create_xblock(usage, student_id):
    block_cls = XBlock.load_class(usage.block_name)
    runtime = DebuggerRuntime(block_cls, student_id, usage)
    block = block_cls(runtime, usage, DbModel(MEMORY_KVS, block_cls, student_id, usage))
    return block


class DbModel(MutableMapping):
    def __init__(self, kvs, block_cls, student_id, usage):
        self._kvs = kvs
        self._student_id = student_id
        self._block_cls = block_cls
        self._usage = usage

    def __repr__(self):
        return "<{0.__class__.__name__} {0._block_cls!r}>".format(self)

    def __str__(self):
        return str(dict(self.iteritems()))

    @call_once_property
    def _children(self):
        """Instantiate the children."""
        return [
            create_xblock(cs, self._student_id) 
            for cs in self._usage.child_specs
            ]

    def _getfield(self, name):
        if not hasattr(self._block_cls, name) or not isinstance(getattr(self._block_cls, name), ModelType):
            raise KeyError(name)

        return getattr(self._block_cls, name)

    def _key(self, name):
        key = []
        field = self._getfield(name)
        block = field.scope.block
        if block == BlockScope.ALL:
            pass
        elif block == BlockScope.USAGE:
            key.append(self._usage.id)
        elif block == BlockScope.DEFINITION:
            key.append(self._usage.def_id)
        elif block == BlockScope.TYPE:
            key.append(self.block_type.__name__)
        if field.scope.student:
            key.append(self._student_id)
        key = ".".join(key)
        return key

    def __getitem__(self, name):
        if name == 'children':
            return self._children
        return self._kvs.get(self._key(name), name)

    def __setitem__(self, name, value):
        self._kvs.set(self._key(name), name, value)

    def __delitem__(self, name):
        self._kvs.delete(self._key(name), name)

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.keys())

    def keys(self):
        return [field.name for field in self._block_cls.fields]


class RuntimeBase(object):
    """Methods all runtimes need."""
    def __init__(self):
        self._view_name = None

    def find_xblock_method(self, block, registration_type, name):
        for _, fn in inspect.getmembers(block, inspect.ismethod):
            fn_name = getattr(fn, '_' + registration_type, None)
            if fn_name == name:
                return fn
        raise MissingXBlockRegistration(block.__class__, registration_type, name)

    def render(self, block, context, view_name):
        self._view_name = view_name
        view_fn = self.find_xblock_method(block, 'view', view_name)

        cache_info = getattr(view_fn, "_cache", {})
        key = "view.%s.%s" % (block.__class__.__name__, view_name)
        id_type = cache_info.get('id', 'definition')
        if id_type == 'usage':
            key += ".%s" % block.usage.id
        elif id_type == 'definition':
            key += ".%s" % block.usage.def_id
        for name in cache_info.get('model', ()):
            key += ".%s=%r" % (name, getattr(block, name))
        widget = cache.get(key)
        if widget is None:
            widget = view_fn(context)
            seconds = cache_info.get('seconds', 0)
            if seconds:
                cache.set(key, widget, seconds)
        self._view_name = None
        return self.wrap_child(widget, context)

    def render_child(self, block, context, view_name=None):
        return block.runtime.render(block, context, view_name or self._view_name)

    def wrap_child(self, widget, context):
        return widget

    def handle(self, block, handler_name, data):
        return self.find_xblock_method(block, 'handler', handler_name)(data)

class DebuggerRuntime(RuntimeBase):
    def __init__(self, block_cls, student_id, usage):
        super(DebuggerRuntime, self).__init__()
        self.block_cls = block_cls
        self.student_id = student_id
        self.usage = usage

    def render_template(self, template_name, **kwargs):
        return django_template_loader.get_template(template_name).render(DjangoContext(kwargs))

    def wrap_child(self, widget, context):
        wrapped = Widget()
        data = {}
        if widget.js_init:
            fn, version = widget.js_init
            wrapped.add_javascript_url("/static/js/runtime/%s.js" % version)
            data['init'] = fn
            data['runtime-version'] = version
            data['usage'] = self.usage.id
            data['block-type'] = self.block_cls.plugin_name

        html = "<div class='wrapper'%s>%s</div>" % (
            "".join(" data-%s='%s'" % item for item in data.items()),
            widget.html(),
        )
        wrapped.add_javascript_url("/static/js/vendor/jquery.min.js")
        wrapped.add_javascript_url("/static/js/vendor/jquery.cookie.js")
        wrapped.add_javascript("""
            $(function() {
                $('.wrapper').each(function(idx, elm) {
                    var version = $(elm).data('runtime-version');
                    if (version !== undefined) {
                        var runtime = window['runtime_' + version](elm);
                        var init_fn = window[$(elm).data('init')];
                        init_fn(runtime, elm);
                    }
                })
            });
            """)
        wrapped.add_content(html)
        wrapped.add_widget_resources(widget)
        return wrapped

    def handler_url(self, url):
        return "/%s/%s" % (self.usage.id, url)

class User(object):
    id = None
    groups = []
