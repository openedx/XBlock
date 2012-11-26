import json

from django.shortcuts import render_to_response
from django.core.cache import get_cache, cache

from xmodule.core import XModule, register_view, MissingXModuleView
#from xmodule.structure_module import Usage

class DebuggingChildModule(XModule):
    @register_view('student_view')
    def student_view(self):
        return "<div class='debug_child'></div>"

def debug_child():
    return DebuggingChildModule(DebuggerRuntime(), {}, {}, {}, {})

class DebuggerRuntime(object):
    @property
    def children(self):
        return [debug_child(), debug_child()]

    def cache(self, cache_name):
        try:
            return get_cache(cache_name)
        except:
            return cache

class User(object):
    id = None
    groups = []

class Placeholder(object):
    def __init__(self, name='generic'):
        self.name = name

    def __getattr__(self, name):
        raise Exception("Tried to use %s on %r %s instance" % (name, self.name, self.__class__.__name__))

class Database(Placeholder):
    pass

def index(request):
    xmodules = XModule.load_classes()
    return render_to_response('index.html', {
        'xmodules': xmodules
    })

def module(request, module_name):
    module_cls = XModule.load_class(module_name)
    runtime = DebuggerRuntime()
    db = Database()

    module = module_cls(runtime, db)

    try:
        student_view = XModule.render(module, 'student_view')
    except MissingXModuleView:
        student_view = "No View Found"

    return render_to_response('module.html', {
        'module': module,
        'student_view': student_view
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

