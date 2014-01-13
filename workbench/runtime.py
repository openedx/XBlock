"""The runtime machinery for the XBlock workbench.

Code in this file is a mix of Runtime layer and Workbench layer.

"""

import logging

try:
    import simplejson as json
except ImportError:
    import json

from django.template import loader as django_template_loader, \
    Context as DjangoContext

from xblock.fields import Scope, ScopeIds
from xblock.runtime import KvsFieldData, KeyValueStore, Runtime, NoSuchViewError, MemoryIdManager
from xblock.fragment import Fragment

from .util import make_safe_for_html

log = logging.getLogger(__name__)


class WorkbenchKeyValueStore(KeyValueStore):
    """A `KeyValueStore` for the Workbench to use.

    This is a simple `KeyValueStore` which stores everything in a dictionary.
    The key mapping is a little complicated to make it somewhat possible to
    read the dict when it is rendered in the browser.

    """
    def __init__(self, db_dict):
        super(WorkbenchKeyValueStore, self).__init__()
        self.db_dict = db_dict

    # Workbench-special methods.

    def clear(self):
        """Clear all data from the store."""
        self.db_dict.clear()

    def as_html(self):
        """Render the key value store to HTML."""
        html = json.dumps(self.db_dict, sort_keys=True, indent=4)
        return make_safe_for_html(html)

    # Implementation details.

    def _actual_key(self, key):
        """
        Constructs the full key name from the given `key`.

        The actual key consists of the scope, block scope id, and user_id.

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
        if key.user_id:
            key_list.append(key.user_id)
        return ".".join(key_list)

    # KeyValueStore methods.

    def get(self, key):
        return self.db_dict[self._actual_key(key)][key.field_name]

    def set(self, key, value):
        """Sets the key to the new value"""
        self.db_dict.setdefault(self._actual_key(key), {})[key.field_name] = value

    def delete(self, key):
        del self.db_dict[self._actual_key(key)][key.field_name]

    def has(self, key):
        return key.field_name in self.db_dict[self._actual_key(key)]

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

    def __init__(self, user_id=None):
        super(WorkbenchRuntime, self).__init__(ID_MANAGER, KvsFieldData(WORKBENCH_KVS))
        self.id_generator = ID_MANAGER
        self.user_id = user_id

    def render(self, block, view_name, context=None):
        try:
            return super(WorkbenchRuntime, self).render(block, view_name, context)
        except NoSuchViewError:
            return Fragment(u"<i>No such view: %s on %s</i>"
                            % (view_name, make_safe_for_html(repr(block))))

    # TODO: [rocha] runtime should not provide this, each xblock
    # should use whatever they want
    def render_template(self, template_name, **kwargs):
        """Loads the django template for `template_name`"""
        template = django_template_loader.get_template(template_name)
        return template.render(DjangoContext(kwargs))

    def wrap_child(self, block, view, frag, context):  # pylint: disable=W0613
        wrapped = Fragment()
        wrapped.add_javascript_url(self.resources_url("js/vendor/jquery.min.js"))
        wrapped.add_javascript_url(self.resources_url("js/vendor/jquery.cookie.js"))

        data = {}
        if frag.js_init_fn:
            wrapped.add_javascript_url(self.resources_url("js/runtime/%s.js" % frag.js_init_version))
            data['init'] = frag.js_init_fn
            data['runtime-version'] = frag.js_init_version
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

    def handler_url(self, block, handler_name, suffix='', query='', thirdparty=False):
        # Be sure this really is a handler.
        func = getattr(block, handler_name, None)
        if not func:
            raise ValueError("{!r} is not a function name".format(handler_name))
        if not getattr(func, "_is_xblock_handler", False):
            raise ValueError("{!r} is not a handler name".format(handler_name))

        url = "/{base}/{usage}/{handler}/{suffix}".format(
            base="unauth_handler" if thirdparty else "handler",
            usage=block.scope_ids.usage_id,
            handler=handler_name,
            suffix=suffix,
        )
        has_query = False
        if not thirdparty:
            url += "?student={student}".format(student=block.scope_ids.user_id)
            has_query = True
        if query:
            url += "&" if has_query else "?"
            url += query
        return url

    def resources_url(self, resource):
        return "/static/" + resource

    def local_resource_url(self, block, uri):
        return '/resource/%s/%s' % (block.scope_ids.block_type, uri)

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
WORKBENCH_KVS = WorkbenchKeyValueStore({})

# Our global id manager
ID_MANAGER = MemoryIdManager()


def reset_global_state():
    """
    Reset any global state in the workbench.

    This allows us to write properly isolated tests.

    """
    from .scenarios import init_scenarios       # avoid circularity.

    WORKBENCH_KVS.clear()
    ID_MANAGER.clear()
    init_scenarios()
