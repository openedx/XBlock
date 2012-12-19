"""Django views implementing the XBlock debugger.

This code is in the Debugger layer.

"""

import json
import logging
import mimetypes
import pkg_resources
from StringIO import StringIO

from webob import Request

from django.shortcuts import render_to_response
from django.http import HttpResponse, Http404

from xblock.core import XBlock

from .runtime import Usage, create_xblock, MEMORY_KVS
from .scenarios import SCENARIOS

# --- Set up an in-memory logger

def setup_logging():
    global LOG_STREAM
    LOG_STREAM = StringIO()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(LOG_STREAM)
    handler.setFormatter(logging.Formatter("<p>%(asctime)s %(name)s %(levelname)s: %(message)s</p>"))
    root_logger.addHandler(handler)

setup_logging()

log = logging.getLogger(__name__)

# We don't really have authentication and multiple students, just accept their
# id on the URL.
def get_student_id(request):
    student_id = int(request.GET.get('student', '99'))
    return student_id

#---- Views -----

def index(request):
    return render_to_response('index.html', {
        'scenarios': [(i, scenario.description) for i, scenario in enumerate(SCENARIOS)]
    })


def show_scenario(request, scenario_id):
    student_id = get_student_id(request)
    log.info("Start show_scenario %s for %s", scenario_id, student_id)
    scenario = SCENARIOS[int(scenario_id)]
    usage = scenario.usage
    block = create_xblock(usage, "student%s" % student_id)
    widget = block.runtime.render(block, {}, 'student_view')
    log.info("End show_scenario %s", scenario_id)
    return render_to_response('block.html', {
        'block': block,
        'body': widget.html(),
        'database': MEMORY_KVS,
        'head_html': widget.head_html(),
        'log': LOG_STREAM.getvalue(),
        'student_id': student_id,
        'usage': usage,
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
    student_id = get_student_id(request)
    log.info("Start handler %s/%s for %s", usage_id, handler, student_id)
    usage = Usage.find_usage(usage_id)
    block = create_xblock(usage, "student%s" % student_id)
    request = django_to_webob_request(request)
    request.path_info_pop()
    request.path_info_pop()
    result = block.runtime.handle(block, handler, request)
    log.info("End handler %s/%s", usage_id, handler)
    return webob_to_django_response(result)


def package_resource(request, package, resource):
    if ".." in resource:
        raise Http404
    try:
        content = pkg_resources.resource_string(package, "static/" + resource)
    except IOError:
        raise Http404
    mimetype, encoding = mimetypes.guess_type(resource)
    return HttpResponse(content, mimetype=mimetype)


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
