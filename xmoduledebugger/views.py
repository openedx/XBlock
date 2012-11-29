import json

from StringIO import StringIO

from webob import Request
from webob.multidict import MultiDict

from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render_to_response
from django.core.cache import get_cache, cache
from django.http import HttpResponse
from django.template import loader as django_template_loader, Context as DjangoContext

from xmodule.core import XModule, register_view, MissingXModuleRegistration, ModuleScope
from xmodule.widget import Widget
#from xmodule.structure_module import Usage

from .util import call_once_property

class DebuggingChildModule(XModule):
    @register_view('student_view')
    def student_view(self, context):
        widget = Widget("<div class='debug_child'></div>")
        widget.add_css("""
            .debug_child {
                background-color: grey;
                width: 200px;
                height: 100px;
                margin: 10px;
            }
            """)
        widget.initialize_js("foo")
        return widget

def create_xmodule(module_name):
    module_cls = XModule.load_class(module_name)
    runtime = DebuggerRuntime(module_cls, "student1234", "usage5678")
    db = DbView(module_cls, "student1234", "usage5678")
    return module_cls(runtime, db)

class RuntimeBase(object):
    def wrap_child(self, widget, context):
        return widget

class DebuggerRuntime(RuntimeBase):
    def __init__(self, module_cls, student_id, usage_id):
        self.widget_id = 0
        self.module_cls = module_cls
        self.student_id = student_id
        self.usage_id = usage_id

    @call_once_property
    def children(self):
        num_children = 3
        return [create_xmodule('debugchild') for _ in range(num_children)]

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
            data['module-type'] = self.module_cls.plugin_name
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
        return "/%s/%s" % (self.module_cls.plugin_name, url)

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
    def __init__(self, module_type, student_id, usage_id):
        self.module_type = module_type
        self.student_id = student_id
        self.usage_id = usage_id

    def query(self, student=False, module=ModuleScope.ALL):
        key = []
        if module == ModuleScope.ALL:
            pass
        elif module == ModuleScope.USAGE:
            key.append(self.usage_id)
        elif module == ModuleScope.DEFINITION:
            key.append("DEFINITION?")
        elif module == ModuleScope.TYPE:
            key.append(self.module_type.__name__)
        if student:
            key.append(self.student_id)
        key = ".".join(key)
        return DATABASE.setdefault(key, {})


class Context(object):
    def __init__(self):
        self._view_name = None

#---- Views -----

def index(request):
    xmodules = XModule.load_classes()
    return render_to_response('index.html', {
        'xmodules': xmodules
    })


def module(request, module_name):
    module = create_xmodule(module_name)
    context = Context()

    try:
        widget = module.render(context, 'student_view')
    except MissingXModuleRegistration as e:
        widget = Widget("No View Found: %s" % (e.args,))

    return render_to_response('module.html', {
        'module': module,
        'body': widget.html(),
        'head_html': widget.head_html(),
    })

def settings(request):

    modules = {
        'edx/test/verticala': XModule.load_class('vertical')(DebuggerRuntime(), {}, {}, {}, {}),
        'edx/test/verticalb': XModule.load_class('vertical')(DebuggerRuntime(), {}, {}, {}, {}),
    }

    course_usages = Usage('course', 'edx/test/course', {
        'graded': True,
        'start_date': '1/2/12',
    }, [
        Usage('verticala', 'edx/test/verticala', {}, []),
        Usage('verticalb', 'edx/test/verticalb', {}, [])
    ]).as_json()

    course = XModule.load_class('course')(DebuggerRuntime(), {
            'policy_list': [{'class': 'cascade', 'params': {'keys': ['graded']}}],
            'usage_tree': course_usages,
        }, {}, {}, {})

    return render_to_response('settings.html', {
        'base_tree': json.dumps(course.usage_tree.as_json(), indent=4),
        'applied_tree': json.dumps(course.apply_policies(User()).as_json(), indent=4),
    })


def handler(request, module_name, handler):
    module = create_xmodule(module_name)
    request = django_to_webob_request(request)
    request.path_info_pop()
    request.path_info_pop()
    result = module.handle(handler, request)
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
