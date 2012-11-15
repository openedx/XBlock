from django.shortcuts import render_to_response

from xmodule.xmodule import XModule, register_view

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

def index(request):
    xmodules = XModule.load_classes()
    return render_to_response('index.html', {
        'xmodules': xmodules
    })

def module(request, module_name):
    module = XModule.load_class(module_name)
    content = course_settings = student_state = user_preferences = {}
    runtime = DebuggerRuntime()

    module = module(runtime, content, course_settings, user_preferences, student_state)

    return render_to_response('module.html', {
        'module': module,
        'student_view': XModule.render(module, 'student_view'),
    })
