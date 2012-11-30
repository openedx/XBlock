import itertools
from collections import defaultdict, MutableMapping

from django.template import loader as django_template_loader, Context as DjangoContext

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

    @classmethod
    def find_usage(cls, usage_id):
        return cls.usage_index[usage_id]


def create_xblock_from_usage(usage, student_id):
    block_cls = XBlock.load_class(usage.block_name)
    runtime = DebuggerRuntime(block_cls, student_id, usage.id)
    dbview = DbView(block_cls, student_id, usage.id, usage.def_id)
    block = block_cls(runtime, usage.id, DbModel(block_cls, student_id, usage.child_specs, dbview))
    return block

class DbModel(MutableMapping):
    def __init__(self, block_cls, student_id, child_specs, dbview):
        self._student_id = student_id
        self._block_cls = block_cls
        self._child_specs = child_specs
        self._db = dbview

    @call_once_property
    def _children(self):
        """Instantiate the children."""
        return [
            create_xblock_from_usage(cs, self._student_id) 
            for cs in self._child_specs
            ]

    def _getfield(self, name):
        if not hasattr(self._block_cls, name) or not isinstance(getattr(self._block_cls, name), ModelType):
            raise KeyError(name)

        return getattr(self._block_cls, name)

    def _getview(self, name):
        field = self._getfield(name)
        return self._db.query(student=field.scope.student, block=field.scope.block)

    def __getitem__(self, name):
        if name == 'children':
            return self._children

        field = self._getfield(name)
        return self._getview(name)[name]

    def __setitem__(self, name, value):
        self._getview(name)[name] = value

    def __delitem__(self, name):
        del self._getview(name)[name]

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.keys())

    def keys(self):
        return [field.name for field in self._block_cls.fields]

    def __repr__(self):
        return 'DbModel(%r, %r)' % (self._block_cls, self._db)

    def __str__(self):
        return str(dict(self.iteritems()))

class RuntimeBase(object):
    def wrap_child(self, widget, context):
        return widget

class DebuggerRuntime(RuntimeBase):
    def __init__(self, block_cls, student_id, usage_id):
        self.widget_id = 0
        self.block_cls = block_cls
        self.student_id = student_id
        self.usage_id = usage_id

    def cache(self, cache_name):
        try:
            return get_cache(cache_name)
        except:
            return cache

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
            data['usage'] = self.usage_id
            data['block-type'] = self.block_cls.plugin_name
        html = "<div id='widget_%d' class='wrapper'%s>%s</div>" % (
            self.widget_id,
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
        self.widget_id += 1
        wrapped.add_content(html)
        wrapped.add_widget_resources(widget)
        return wrapped

    def handler_url(self, url):
        return "/%s/%s" % (self.usage_id, url)

class User(object):
    id = None
    groups = []


DATABASE = {}

class DbView(object):
    def __init__(self, block_type, student_id, usage_id, definition_id):
        super(DbView, self).__init__()
        self.block_type = block_type
        self.student_id = student_id
        self.definition_id = definition_id
        self.usage_id = usage_id

    def query(self, student=False, block=BlockScope.ALL):
        key = []
        if block == BlockScope.ALL:
            pass
        elif block == BlockScope.USAGE:
            key.append(self.usage_id)
        elif block == BlockScope.DEFINITION:
            key.append(self.definition_id)
        elif block == BlockScope.TYPE:
            key.append(self.block_type.__name__)
        if student:
            key.append(self.student_id)
        key = ".".join(key)
        return DATABASE.setdefault(key, {})


class Context(object):
    def __init__(self):
        self._view_name = None

