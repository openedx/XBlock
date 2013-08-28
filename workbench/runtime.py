"""The runtime machinery for the XBlock workbench.

Code in this file is a mix of Runtime layer and Workbench layer.

"""

import itertools

try:
    import simplejson as json
except ImportError:
    import json

import logging

from django.template import loader as django_template_loader, \
    Context as DjangoContext

from xblock.fields import Scope, ScopeIds
from xblock.runtime import DbModel, KeyValueStore, Runtime, NoSuchViewError
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
        self.id = "usage_%d" % next(self._ids)  # pylint: disable=C0103
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
        runtime_initial = WorkbenchRuntime()
        block = runtime_initial.create_block(self)
        if self.initial_state:
            for name, value in self.initial_state.items():
                setattr(block, name, value)

        block.children = [child.id for child in self.children]
        if self.parent is not None:
            block.parent = self.parent.id

        # We've initialized this instance, keep track.
        self._inited.add(self.id)

        # Explicitly save all of the initial state we've just written
        block.save()

        # Also do this recursively down the tree.
        for child in self.children:
            child.store_initial_state()

    def __repr__(self):
        return "<{0.__class__.__name__} {0.id} {0.block_name} {0.def_id} {0.children!r}>".format(self)

    @classmethod
    def find_usage(cls, usage_id):
        """Looks up the `usage_id` from our global index of all usages."""
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
    def __init__(self, db_dict):
        self.db_dict = db_dict

    def clear(self):
        """Clear all data from the store."""
        self.db_dict.clear()

    def actual_key(self, key):
        """
        Constructs the full key name from the given `key`.

        The actual key consists of the scope, block scope id, and student_id.

        """
        key_list = []
        if key.scope == Scope.children:
            key_list.append('children')
        elif key.scope == Scope.parent:
            key_list.append('parent')
        else:
            key_list.append(["usage", "definition", "type", "all"][key.scope.block])

        if key.block_scope_id is not None:
            key_list.append(key.block_scope_id)
        if key.student_id:
            key_list.append(key.student_id)
        return ".".join(key_list)

    def get(self, key):
        return self.db_dict[self.actual_key(key)][key.field_name]

    def set(self, key, value):
        """Sets the key to the new value"""
        self.db_dict.setdefault(self.actual_key(key), {})[key.field_name] = value

    def delete(self, key):
        del self.db_dict[self.actual_key(key)][key.field_name]

    def has(self, key):
        return key.field_name in self.db_dict[self.actual_key(key)]

    def as_html(self):
        """Just for our Workbench!"""
        html = json.dumps(self.db_dict, sort_keys=True, indent=4)
        return make_safe_for_html(html)

    def set_many(self, update_dict):
        """
        Sets many fields to new values in one call.

        `update_dict`: A dictionary of keys: values.
        This method sets the value of each key to the specified new value.
        """
        for key, value in update_dict.items():
            # We just call `set` directly here, because this is an in-memory representation
            # thus we don't concern ourselves with bulk writes.
            self.set(key, value)


class WorkbenchRuntime(Runtime):
    """
    Access to the workbench runtime environment for XBlocks.

    A pre-configured instance of this class will be available to XBlocks as
    `self.runtime`.

    """

    def __init__(self, student_id=None):
        super(WorkbenchRuntime, self).__init__()
        self.student_id = student_id

    def create_block(self, usage):
        """
        Create an XBlock instance in this runtime.

        The `usage` is used to find the XBlock class and data.

        """
        keys = ScopeIds(self.student_id, usage.block_name, usage.def_id, usage.id)
        block = self.construct_block(usage.block_name, MODEL, keys)
        return block

    def render(self, block, context, view_name):
        try:
            return super(WorkbenchRuntime, self).render(block, context, view_name)
        except NoSuchViewError:
            return Fragment(u"<i>No such view: %s on %s</i>"
                            % (view_name, make_safe_for_html(repr(block))))

    # TODO: [rocha] runtime should not provide this, each xblock
    # should use whatever they want
    def render_template(self, template_name, **kwargs):
        """Loads the django template for `template_name`"""
        template = django_template_loader.get_template(template_name)
        return template.render(DjangoContext(kwargs))

    def wrap_child(self, block, frag, context):  # pylint: disable=W0613
        wrapped = Fragment()
        wrapped.add_javascript_url("/static/js/vendor/jquery.min.js")
        wrapped.add_javascript_url("/static/js/vendor/jquery.cookie.js")

        data = {}
        if frag.js_init:
            func, version = frag.js_init
            wrapped.add_javascript_url("/static/js/runtime/%s.js" % version)
            data['init'] = func
            data['runtime-version'] = version
            data['usage'] = block.scope_ids.usage_id
            data['block-type'] = block.scope_ids.block_type

        if block.name:
            data['name'] = block.name

        html = u"<div class='xblock'%s>%s</div>" % (
            "".join(" data-%s='%s'" % item for item in data.items()),
            frag.body_html(),
        )
        wrapped.add_content(html)
        wrapped.add_frag_resources(frag)
        return wrapped

    def handler_url(self, block, url):
        return "/handler/{0}/{1}/?student={2}".format(
            block.scope_ids.usage_id,
            url,
            block.scope_ids.student_id
        )

    def get_block(self, block_id):
        return self.create_block(Usage.find_usage(block_id))

    def query(self, block):
        return _BlockSet(self, [block])


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
        # Allow this method to access _class_tags for each block
        # pylint: disable=W0212
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


# Our global state (the "database").
MEMORY_KVS = MemoryKeyValueStore({})
MODEL = DbModel(MEMORY_KVS)
