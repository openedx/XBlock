import itertools
import json
import logging
import new
from collections import MutableMapping

from django.template import loader as django_template_loader, Context as DjangoContext
from django.core.cache import cache

from xblock.core import XBlock, BlockScope, Scope, ModelType
from xblock.widget import Widget

from .util import call_once_property

log = logging.getLogger(__name__)


def make_safe_for_html(html):
    html = html.replace("&", "&amp;")
    html = html.replace(" ", "&nbsp;")
    html = html.replace("<", "&lt;")
    html = html.replace("\n", "<br>")
    return html

class Usage(object):
    # Not the real way we'll store usages!
    ids = itertools.count()
    usage_index = {}

    def __init__(self, block_name, def_id, child_specs, initial_state={}):
        self.id = "usage_%d" % next(self.ids)
        self.block_name = block_name
        self.def_id = def_id
        self.child_specs = child_specs
        self.usage_index[self.id] = self
        self.initial_state = initial_state

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

    def as_html(self):
        """Just for our Debugger!"""
        html = json.dumps(self.d, sort_keys=True, indent=4)
        return make_safe_for_html(html)

MEMORY_KVS = MemoryKeyValueStore({})

def create_xblock(usage, student_id):
    block_cls = XBlock.load_class(usage.block_name)
    runtime = DebuggerRuntime(block_cls, student_id, usage)
    block = block_cls(runtime, usage, DbModel(MEMORY_KVS, block_cls, student_id, usage))
    for name, value in usage.initial_state.items():
        setattr(block, name, value)
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
        # TODO: Maybe this should be a method on XBlock?
        try:
            fn = block.registered_methods[registration_type + name]
        except KeyError:
            return None
        return new.instancemethod(fn, block, block.__class__)

    def render(self, block, context, view_name):
        self._view_name = view_name
        for try_name in [view_name, "default"]:
            view_fn = self.find_xblock_method(block, 'view', try_name)
            if view_fn:
                break
        else:
            return Widget("<i>No such view: %s on %s</i>" % (view_name, make_safe_for_html(repr(block))))

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
        else:
            log.debug("Cache hit: %s", key)
        self._view_name = None
        return self.wrap_child(block, widget, context)

    def render_child(self, block, context, view_name=None):
        return block.runtime.render(block, context, view_name or self._view_name)

    def wrap_child(self, block, widget, context):
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

    def wrap_child(self, block, widget, context):
        wrapped = Widget()
        data = {}
        if widget.js_init:
            fn, version = widget.js_init
            wrapped.add_javascript_url("/static/js/runtime/%s.js" % version)
            data['init'] = fn
            data['runtime-version'] = version
            data['usage'] = self.usage.id
            data['block-type'] = self.block_cls.plugin_name

        data['name'] = block.name

        html = "<div class='wrapper'%s>%s</div>" % (
            "".join(" data-%s='%s'" % item for item in data.items()),
            widget.html(),
        )
        wrapped.add_javascript_url("/static/js/vendor/jquery.min.js")
        wrapped.add_javascript_url("/static/js/vendor/jquery.cookie.js")
        wrapped.add_javascript("""
            $(function() {
                $.fn.immediateDescendents = function(selector) {
                    return this.children().map(function(idx, elm) {
                        if ($(elm).is(selector)) {
                            return elm;
                        } else {
                            return $(elm).immediateDescendents(selector).toArray();
                        }
                    });
                };

                function initializeBlock(element) {
                        var children = initializeBlocks($(element));

                        var version = $(element).data('runtime-version');
                        if (version === undefined) {
                            return null;
                        }

                        var runtime = window['runtime_' + version](element, children);
                        var init_fn = window[$(element).data('init')];
                        var js_block = init_fn(runtime, element) || {};
                        js_block.element = element;
                        js_block.name = $(element).data('name');
                        return js_block;
                }

                function initializeBlocks(element) {
                    return $(element).immediateDescendents('.wrapper').map(function(idx, elm) {
                        return initializeBlock(elm);
                    }).toArray();
                }

                initializeBlocks($('body'));
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
