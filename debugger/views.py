import itertools
import json

from collections import defaultdict, MutableMapping, namedtuple
from StringIO import StringIO

from webob import Request
from webob.multidict import MultiDict

from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render_to_response
from django.core.cache import get_cache, cache
from django.http import HttpResponse
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
    return create_xblock(usage.block_name, student_id, usage.id, usage.def_id, usage.child_specs)

def create_xblock(block_name, student_id, usage_id, def_id, child_specs):
    block_cls = XBlock.load_class(block_name)
    runtime = DebuggerRuntime(block_cls, student_id, usage_id)
    dbview = DbView(block_cls, student_id, usage_id, def_id)
    block = block_cls(runtime, usage_id, DbModel(block_cls, student_id, child_specs, dbview))
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

class Placeholder(object):
    def __init__(self, name='generic'):
        self.name = name

    def __getattr__(self, name):
        raise Exception("Tried to use %s on %r %s instance" % (name, self.name, self.__class__.__name__))


DATABASE = {}

class DbView(Placeholder):
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

#---- Data -----

# Build the scenarios, which are named trees of usages.

Scenario = namedtuple("Scenario", "description usage")

SCENARIOS = []
default_children = [Usage("debugchild", "dbgdefn", []) for _ in xrange(3)]

for name, cls in XBlock.load_classes():
    SCENARIOS.append(Scenario("class "+name, Usage(name, "defn999", default_children)))

SCENARIOS.append(Scenario("Problem with an input",
    Usage("problem", "x", [
        Usage("textinput", "x", []),
        Usage("textinput", "x", []),
    ])
))

#---- Views -----

def index(request):
    return render_to_response('index.html', {
        'scenarios': [(i, scenario.description) for i, scenario in enumerate(SCENARIOS)]
    })


def show_scenario(request, scenario_id):
    scenario = SCENARIOS[int(scenario_id)]
    usage = scenario.usage
    block = create_xblock_from_usage(usage, "student99")
    context = Context()

    try:
        widget = block.render(context, 'student_view')
    except MissingXBlockRegistration as e:
        widget = Widget("No View Found: %s" % (e.args,))

    return render_to_response('block.html', {
        'database': DATABASE,
        'block': block,
        'body': widget.html(),
        'head_html': widget.head_html(),
    })


def settings(request):

    blocks = {
        'edx/test/verticala': XBlock.load_class('vertical')(DebuggerRuntime(), {}, {}, {}, {}),
        'edx/test/verticalb': XBlock.load_class('vertical')(DebuggerRuntime(), {}, {}, {}, {}),
    }

    course_usages = Usage('course', 'edx/test/course', {
        'graded': True,
        'start_date': '1/2/12',
    }, [
        Usage('verticala', 'edx/test/verticala', {}, []),
        Usage('verticalb', 'edx/test/verticalb', {}, [])
    ]).as_json()

    course = XBlock.load_class('course')(DebuggerRuntime(), {
            'policy_list': [{'class': 'cascade', 'params': {'keys': ['graded']}}],
            'usage_tree': course_usages,
        }, {}, {}, {})

    return render_to_response('settings.html', {
        'base_tree': json.dumps(course.usage_tree.as_json(), indent=4),
        'applied_tree': json.dumps(course.apply_policies(User()).as_json(), indent=4),
    })


def handler(request, usage_id, handler):
    usage = Usage.find_usage(usage_id)
    block = create_xblock_from_usage(usage, "student99")
    request = django_to_webob_request(request)
    request.path_info_pop()
    request.path_info_pop()
    result = block.handle(handler, request)
    return webob_to_django_response(result)


def webob_to_django_response(webob_response):
    django_response = HttpResponse(
        webob_response.app_iter,
        content_type=webob_response.content_type
    )
    for name, value in webob_response.headerlist:
        django_response[name] = value
    return django_response


def django_to_webob_request(django_request):
    environ = {}
    environ.update(django_request.META)

    webob_request = Request(django_request.META)
    webob_request.body = django_request.body
    return webob_request
