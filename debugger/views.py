import itertools
import json
import logging

from collections import defaultdict, MutableMapping, namedtuple
from StringIO import StringIO

from webob import Request
from webob.multidict import MultiDict

from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render_to_response
from django.core.cache import get_cache, cache
from django.http import HttpResponse

from xblock.core import XBlock, MissingXBlockRegistration, Scope
from xblock.widget import Widget


from .runtime import Usage, create_xblock, MEMORY_KVS

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

#---- Data -----

# Build the scenarios, which are named trees of usages.

Scenario = namedtuple("Scenario", "description usage")

SCENARIOS = []
default_children = [Usage("debugchild", "dbgdefn", []) for _ in xrange(3)]

for name, cls in XBlock.load_classes():
    SCENARIOS.append(Scenario(name, Usage(name, "defn999", default_children)))

SCENARIOS.extend([
    Scenario("problem with two inputs",
        Usage("problem", "x", [
            Usage("textinput", "x", []),
            Usage("textinput", "x", []),
        ]),
    ),
    Scenario("three thumbs at once",
        Usage("vertical", "x", [
            Usage("thumbs", "def1", []),
            Usage("thumbs", "def2", []),
            Usage("thumbs", "def3", []),
        ])
    ),
    Scenario("problem with thumbs and textbox",
        Usage("problem", "p1", [
            Usage("thumbs", "x", []),
            Usage("textinput", "textin", [], {'input_type': 'int'}),
            Usage("equality", "e1", [], {'message': 'Upvotes match downvotes'}),
            Usage("equality", "e2", [], {'message': 'Number of upvotes matches entered string'}),
            Usage("equality", "e3", [], {'message': 'Number of upvotes is 3'}),
        ], {
            'children_names': ['thumb', 'votecount', 'votes_equal', 'votes_named', 'votes_specified'],
            'checker_arguments': {
                'votes_equal': {
                    'left': {'_type': 'reference', 'ref_name': 'thumb.upvotes'},
                    'right': {'_type': 'reference', 'ref_name': 'thumb.downvotes'},
                },
                'votes_named': {
                    'left': {'_type': 'reference', 'ref_name': 'thumb.upvotes'},
                    'right': {'_type': 'reference', 'ref_name': 'votecount.student_input'},
                },
                'votes_specified': {
                    'left': {'_type': 'reference', 'ref_name': 'thumb.upvotes'},
                    'right': 3,
                }
            }
        }),
    ),
])

#---- Views -----

def index(request):
    return render_to_response('index.html', {
        'scenarios': [(i, scenario.description) for i, scenario in enumerate(SCENARIOS)]
    })


def show_scenario(request, scenario_id):
    log.info("Start show_scenario %s", scenario_id)
    scenario = SCENARIOS[int(scenario_id)]
    usage = scenario.usage
    block = create_xblock(usage, "student99")

    try:
        widget = block.runtime.render(block, {}, 'student_view')
    except MissingXBlockRegistration as e:
        widget = Widget("No View Found: %s" % (e.args,))

    log.info("End show_scenario %s", scenario_id)
    return render_to_response('block.html', {
        'database': MEMORY_KVS,
        'block': block,
        'body': widget.html(),
        'head_html': widget.head_html(),
        'usage': usage,
        'log': LOG_STREAM.getvalue(),
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
    log.info("Start handler %s/%s", usage_id, handler)
    usage = Usage.find_usage(usage_id)
    block = create_xblock(usage, "student99")
    request = django_to_webob_request(request)
    request.path_info_pop()
    request.path_info_pop()
    result = block.runtime.handle(block, handler, request)
    log.info("End handler %s/%s", usage_id, handler)
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
