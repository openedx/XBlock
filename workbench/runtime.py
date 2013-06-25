"""The runtime machinery for the XBlock workbench.

Code in this file is a mix of Runtime layer and Workbench layer.

"""

import functools
import itertools

try:
    import simplejson as json
except ImportError:
    import json

import logging

from django.template import loader as django_template_loader, Context as DjangoContext

from xblock.core import XBlock, Scope, ModelType
from xblock.runtime import DbModel, KeyValueStore, Runtime
from xblock.fragment import Fragment

from .util import make_safe_for_html

log = logging.getLogger(__name__)


class Usage(object):
    """Content usages

    Usages represent uses of content in courses.  They are the basic static
    building block for course content.

    TODO: Not the real way we'll store usages!

    """

    # An infinite stream of ids, for giving each Usage an id.
    _ids = itertools.count()

    # Maps ids to Usages, a dict of all instances created, ever.
    _usage_index = {}

    # The set of Usage ids that have been initialized by store_initial_state.
    _inited = set()

    def __init__(self, block_name, children=None, initial_state=None, def_id=None):
        self.id = "usage_%d" % next(self._ids)
        self.parent = None
        self.block_name = block_name
        self.def_id = def_id or ("def_%d" % next(self._ids))
        self.children = children or []
        self.initial_state = initial_state or {}

        # Update our global index of all usages.
        self._usage_index[self.id] = self

        # Create the parent references as we construct children.
        for child in self.children:
            child.parent = self

    def store_initial_state(self):
        """Ensure that the initial state of this Usage is created.

        This method is called before using the Usage.  It will use the
        `initial_state` argument to the Usage to populate XBlock
        attributes, and then recursively do the same for its children.

        All this work is only done once for each Usage no matter how often
        this function is called.

        """
        # If we've already created the initial state, there's nothing to do.
        if self.id in self._inited:
            return

        # Create an XBlock from this usage, and use it to create the initial
        # state. This block is created just so we can use the block to set
        # attributes, which will cause the data to be written through the
        # fields. This isolates us from the storage mechanism: however the
        # block saves its attributes, that's how the initial state will be
        # saved.
        block = create_xblock(self)
        if self.initial_state:
            for name, value in self.initial_state.items():
                setattr(block, name, value)

        block.children = [child.id for child in self.children]
        if self.parent is not None:
            block.parent = self.parent.id

        # We've initialized this instance, keep track.
        self._inited.add(self.id)

        # Also do this recursively down the tree.
        for child in self.children:
            child.store_initial_state()

    def __repr__(self):
        return "<{0.__class__.__name__} {0.id} {0.block_name} {0.def_id} {0.children!r}>".format(self)

    @classmethod
    def find_usage(cls, usage_id):
        return cls._usage_index[usage_id]


    @classmethod
    def reinitialize_all(cls):
        """
        Reset all the inited flags, so that Usages will be initialized again.

        Used to isolate tests from each other.

        """
        cls._inited.clear()


class MemoryKeyValueStore(KeyValueStore):
    """Use a simple in-memory database for a key-value store."""
    def __init__(self, d):
        self.d = d

    def clear(self):
        """Clear all data from the store."""
        self.d.clear()

    def actual_key(self, key):
        k = []
        if key.scope == Scope.children:
            k.append('children')
        elif key.scope == Scope.parent:
            k.append('parent')
        else:
            k.append(["usage", "definition", "type", "all"][key.scope.block])

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

    def has(self, key):
        return key.field_name in self.d[self.actual_key(key)]

    def as_html(self):
        """Just for our Workbench!"""
        html = json.dumps(self.d, sort_keys=True, indent=4)
        return make_safe_for_html(html)

    def update(self, update_dict):
        for key, value in update_dict:
            self.set(key, value)


MEMORY_KVS = MemoryKeyValueStore({})


def create_xblock(usage, student_id=None):
    """Create an XBlock instance.

    This will be invoked to create new instances for every request.

    """
    block_cls = XBlock.load_class(usage.block_name)
    runtime = WorkbenchRuntime(block_cls, student_id, usage)
    model = DbModel(MEMORY_KVS, block_cls, student_id, usage)
    block = block_cls(runtime, model)
    return block


class WorkbenchRuntime(Runtime):
    def __init__(self, block_cls, student_id, usage):
        super(WorkbenchRuntime, self).__init__()

        self.block_cls = block_cls
        self.student_id = student_id
        self.usage = usage

    def render(self, block, context, view_name):
        self._view_name = view_name

        view_fn = getattr(block, view_name, None)
        if view_fn is None:
            view_fn = getattr(block, "fallback_view", None)
            if view_fn is None:
                return Fragment(u"<i>No such view: %s on %s</i>" % (view_name, make_safe_for_html(repr(block))))
            view_fn = functools.partial(view_fn, view_name)

        frag = view_fn(context)

        self._view_name = None
        return self.wrap_child(block, frag, context)

    # TODO: [rocha] runtime should not provide this, each xblock
    # should use whatever they want
    def render_template(self, template_name, **kwargs):
        return django_template_loader.get_template(template_name).render(DjangoContext(kwargs))

    def wrap_child(self, block, frag, context):
        wrapped = Fragment()
        wrapped.add_javascript_url("/static/js/vendor/jquery.min.js")
        wrapped.add_javascript_url("/static/js/vendor/jquery.cookie.js")

        data = {}
        if frag.js_init:
            fn, version = frag.js_init
            wrapped.add_javascript_url("/static/js/runtime/%s.js" % version)
            data['init'] = fn
            data['runtime-version'] = version
            data['usage'] = self.usage.id
            data['block-type'] = self.block_cls.plugin_name

        if block.name:
            data['name'] = block.name

        html = u"<div class='xblock'%s>%s</div>" % (
            "".join(" data-%s='%s'" % item for item in data.items()),
            frag.body_html(),
        )
        wrapped.add_content(html)
        wrapped.add_frag_resources(frag)
        return wrapped

    def handler_url(self, url):
        return "/handler/%s/%s/?student=%s" % (self.usage.id, url, self.student_id)

    def get_block(self, block_id):
        return create_xblock(Usage.find_usage(block_id), self.student_id)

    def query(self, block):
        return _BlockSet(self, [block])

    # TODO: [rocha] other name options: gather
    def collect(self, key, block=None):
        block_cls = block.__class__ if block else self.block_cls

        data_model = AnalyticsDbModel(MEMORY_KVS, block_cls, self.student_id, self.usage)
        value = data_model.get(key)
        children = []
        for child_id in data_model.get('children', []):
            child = self.get_block(child_id)
            children.append(child.runtime.collect(key, child))

        result = {
            'class': block_cls.__name__,
            'value': value,
            'children': children,
        }

        return result

    # TODO: [rocha] other name options: scatter, share
    def publish(self, key, value):
        data = AnalyticsDbModel(MEMORY_KVS, self.block_cls, self.student_id, self.usage)
        data[key] = value


class _BlockSet(object):
    def __init__(self, runtime, blocks):
        self.runtime = runtime
        self.blocks = blocks

    def __iter__(self):
        return iter(self.blocks)

    def parent(self):
        them = set()
        for block in self.blocks:
            if block.parent:
                parent = self.runtime.get_block(block.parent)
                them.add(parent)
        return _BlockSet(self.runtime, them)

    def children(self):
        them = set()
        for block in self.blocks:
            for child_id in getattr(block, "children", ()):
                child = self.runtime.get_block(child_id)
                them.add(child)
        return _BlockSet(self.runtime, them)

    def descendants(self):
        them = set()
        def recur(block):
            for child_id in getattr(block, "children", ()):
                child = self.runtime.get_block(child_id)
                them.add(child)
                recur(child)

        for block in self.blocks:
            recur(block)

        return _BlockSet(self.runtime, them)

    def tagged(self, tag):
        them = set()
        for block in self.blocks:
            if block.name == tag:
                them.add(block)
            if block.tags and tag in block.tags:
                them.add(block)
            elif tag in block._class_tags:
                them.add(block)
        return _BlockSet(self.runtime, them)

    def attr(self, attr_name):
        for block in self.blocks:
            if hasattr(block, attr_name):
                yield getattr(block, attr_name)


class AnalyticsDbModel(DbModel):
    def _key(self, name):
        key = super(AnalyticsDbModel, self)._key('analytics.{0}'.format(name))
        return key

    def _getfield(self, name):
        return ModelType(scope=Scope.user_state)
