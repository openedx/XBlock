import json

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
    runtime = DebuggerRuntime()
    db = DbView(module_cls, "student1234", "usage5678")
    module = module_cls(runtime, db)
    return module

class RuntimeBase(object):
    def wrap_child(self, widget, context):
        return widget

class DebuggerRuntime(RuntimeBase):
    def __init__(self):
        self.widget_id = 0

    @call_once_property
    def children(self):
        child_class = 'DebuggingChildModule'
        num_children = 3
        return [create_xmodule(child_class) for _ in range(num_children)]

    def cache(self, cache_name):
        try:
            return get_cache(cache_name)
        except:
            return cache

    def render_template(self, template_name, **kwargs):
        return django_template_loader.get_template(template_name).render(DjangoContext(kwargs))

    def wrap_child(self, module, widget, context):
        wrapped = Widget()
        data = {}
        if widget.js_init:
            fn, version = widget.js_init
            wrapped.add_javascript_url("/static/js/runtime/%s.js" % version)
            data['init'] = fn
            data['runtime-version'] = version
            data['module-type'] = module.__class__.__name__
        html = "<div id='widget_%d' class='wrapper'%s>%s</div>" % (
            self.widget_id,
            "".join(" data-%s='%s'" % item for item in data.items()),
            widget.html(),
        )
        wrapped.add_javascript_url("//ajax.googleapis.com/ajax/libs/jquery/1.8.3/jquery.min.js")
        wrapped.add_javascript_url("//cdnjs.cloudflare.com/ajax/libs/jquery-cookie/1.2/jquery.cookie.js")
        wrapped.add_javascript("""
            $(function() {
                $('.wrapper').each(function(idx, elm) {
                    var version = $(elm).data('runtime-version');
                    var runtime = window['runtime_' + version](elm);
                    var init_fn = window[$(elm).data('init')];
                    init_fn(runtime, elm);
                })
            });
            """)
        self.widget_id += 1
        wrapped.add_content(html)
        wrapped.add_widget_resources(widget)
        return wrapped

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
    module_cls = XModule.load_class(module_name)
    runtime = DebuggerRuntime()
    db = DbView(module_cls, "student1234", "usage5678")

    module = module_cls(runtime, db)
    result = module.handle(handler, json.loads(request.body))
    return webob_to_django_response(result)


def webob_to_django_response(webob_response):
    django_response = HttpResponse(
        webob_response.app_iter,
        content_type=webob_response.content_type
    )
    for name, value in webob_response.headerlist:
        django_response[name] = value
    return django_response
