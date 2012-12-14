"""The runtime machinery for the XBlock debugger.

Code in this file is a mix of Runtime layer and Debugger layer.

"""

import itertools
import json
import logging
import new

from django.template import loader as django_template_loader, Context as DjangoContext
from django.core.cache import cache

from xblock.core import XBlock, Scope, ModelType
from xblock.runtime import DbModel, KeyValueStore
from xblock.widget import Widget

from .util import make_safe_for_html

log = logging.getLogger(__name__)


class Usage(object):
    # TODO: Not the real way we'll store usages!
    ids = itertools.count()
    usage_index = {}

    def __init__(self, block_name, def_id, child_specs, initial_state={}):
        self.id = "usage_%d" % next(self.ids)
        self.block_name = block_name
        self.def_id = def_id or ("def_%d" % next(self.ids))
        self.child_specs = child_specs
        self.usage_index[self.id] = self
        self.initial_state = initial_state

    def __repr__(self):
        return "<{0.__class__.__name__} {0.id} {0.block_name} {0.def_id} {0.child_specs!r}>".format(self)

    @classmethod
    def find_usage(cls, usage_id):
        return cls.usage_index[usage_id]


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


MEMORY_KVS = MemoryKeyValueStore({})


initialized_usages = set()


def create_xblock(usage, student_id):
    """Create an XBlock instance.

    This will be invoked to create new instances for every request.

    """
    block_cls = XBlock.load_class(usage.block_name)
    runtime = DebuggerRuntime(block_cls, student_id, usage)
    block = block_cls(runtime, usage, DbModel(MEMORY_KVS, block_cls, student_id, usage))
    if usage.id not in initialized_usages:
        for name, value in usage.initial_state.items():
            setattr(block, name, value)
        initialized_usages.add(usage.id)
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
        wrapped.add_javascript_url("/static/js/vendor/jquery.min.js")
        wrapped.add_javascript_url("/static/js/vendor/jquery.cookie.js")

        data = {}
        if widget.js_init:
            fn, version = widget.js_init
            wrapped.add_javascript_url("/static/js/runtime/%s.js" % version)
            data['init'] = fn
            data['runtime-version'] = version
            data['usage'] = self.usage.id
            data['block-type'] = self.block_cls.plugin_name

        if block.name:
            data['name'] = block.name

        html = "<div class='xblock'%s>%s</div>" % (
            "".join(" data-%s='%s'" % item for item in data.items()),
            widget.html(),
        )
        wrapped.add_content(html)
        wrapped.add_widget_resources(widget)
        return wrapped

    def handler_url(self, url):
        return "/handler/%s/%s/?student=%s" % (self.usage.id, url, self.student_id)

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
