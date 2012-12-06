"""The runtime machinery for the XBlock debugger.

Code in this file is a mix of Runtime layer and Debugger layer.

"""

import itertools
import json
import logging
import new
from collections import MutableMapping, namedtuple

from django.template import loader as django_template_loader, Context as DjangoContext
from django.core.cache import cache

from xblock.core import XBlock, BlockScope, Scope, ModelType
from xblock.widget import Widget

from .util import call_once_property, make_safe_for_html

log = logging.getLogger(__name__)


class Usage(object):
    # TODO: Not the real way we'll store usages!
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

    # Keys are structured to retain information about the scope of the data.
    # Stores can use this information however they like to store and retrieve
    # data.
    Key = namedtuple("Key", "student_id, block_scope, block_scope_id, field_name")

    def get(key):
        pass

    def set(key, value):
        pass

    def delete(key):
        pass


class MemoryKeyValueStore(KeyValueStore):
    """Use a simple in-memory database for a key-value store."""
    def __init__(self, d):
        self.d = d

    def actual_key(self, key):
        k = []
        k.append(["usage", "definition", "type", "all"][key.block_scope])
        if key.block_scope_id is not None:
            k.append(key.block_scope_id)
        if key.student_id:
            k.append(key.student_id)
        return ".".join(k)

    def get(self, key):
        return self.d[self.actual_key(key)][key.field_name]

    def set(self, key, value):
        self.d.setdefault(self.actual_key(key), {})[key.field_name] = value

    def delete(self, key):
        del self.d[self.actual_key(key)][key.field_name]

    def as_html(self):
        """Just for our Debugger!"""
        html = json.dumps(self.d, sort_keys=True, indent=4)
        return make_safe_for_html(html)

class DbModel(MutableMapping):
    """A dictionary-like interface to the fields on a block."""

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
        field = self._getfield(name)
        block = field.scope.block
        if block == BlockScope.ALL:
            block_id = None
        elif block == BlockScope.USAGE:
            block_id = self._usage.id
        elif block == BlockScope.DEFINITION:
            block_id = self._usage.def_id
        elif block == BlockScope.TYPE:
            block_id = self.block_type.__name__
        if field.scope.student:
            student_id = self._student_id
        else:
            student_id = None
        key = KeyValueStore.Key(
            student_id=student_id,
            block_scope=block,
            block_scope_id=block_id,
            field_name=name
            )
        return key

    def __getitem__(self, name):
        if name == 'children':
            return self._children
        return self._kvs.get(self._key(name))

    def __setitem__(self, name, value):
        self._kvs.set(self._key(name), value)

    def __delitem__(self, name):
        self._kvs.delete(self._key(name))

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.keys())

    def keys(self):
        return [field.name for field in self._block_cls.fields]


MEMORY_KVS = MemoryKeyValueStore({})

def create_xblock(usage, student_id):
    block_cls = XBlock.load_class(usage.block_name)
    runtime = DebuggerRuntime(block_cls, student_id, usage)
    block = block_cls(runtime, usage, DbModel(MEMORY_KVS, block_cls, student_id, usage))
    for name, value in usage.initial_state.items():
        setattr(block, name, value)
    return block


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

    # TODO: [rocha] runtime should not provide this, each xblock
    # should use whatever they want
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

        html = "<div class='xblock'%s>%s</div>" % (
            "".join(" data-%s='%s'" % item for item in data.items()),
            widget.html(),
        )
        wrapped.add_content(html)

        wrapped.add_javascript_url("/static/js/vendor/jquery.min.js")
        wrapped.add_javascript_url("/static/js/vendor/jquery.cookie.js")
        wrapped.add_javascript(RUNTIME_JS);
        wrapped.add_widget_resources(widget)
        return wrapped

    def handler_url(self, url):
        return "/%s/%s" % (self.usage.id, url)

    # TODO: [rocha] other name options: gather
    def collect(self, key, block=None):
        block_cls = block.__class__ if block else self.block_cls
        usage = block.usage if block else self.usage

        data_model = AnalyticsDbModel(MEMORY_KVS, block_cls, self.student_id, usage)
        value = data_model.get(key)
        children = data_model.get('children', [])

        result = {
            'class': block_cls.__name__,
            'value': value,
            'children': [self.collect(key, b) for b in children]
        }

        return result

    # TODO: [rocha] other name options: scatter, share
    def publish(self, key, value):
        data = AnalyticsDbModel(MEMORY_KVS, self.block_cls, self.student_id, self.usage)
        data[key] = value


class User(object):
    id = None
    groups = []


class AnalyticsDbModel(DbModel):
    def _key(self, name):
        key = super(AnalyticsDbModel, self)._key('analytics.{0}'.format(name))
        return key

    def _getfield(self, name):
        return ModelType(scope=Scope.student_state)


RUNTIME_JS = """
$(function() {
    $.fn.immediateDescendents = function(selector) {
        return this.children().map(function(idx, element) {
            if ($(element).is(selector)) {
                return element;
            } else {
                return $(element).immediateDescendents(selector).toArray();
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
        return $(element).immediateDescendents('.xblock').map(function(idx, elem) {
            return initializeBlock(elem);
        }).toArray();
    }

    initializeBlocks($('body'));
});
"""
