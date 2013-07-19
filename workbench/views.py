"""Django views implementing the XBlock workbench.

This code is in the Workbench layer.

"""

import logging
import mimetypes
import pkg_resources
from StringIO import StringIO

from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.views.decorators.csrf import ensure_csrf_cookie

from .runtime import Usage, create_xblock, MEMORY_KVS
from .scenarios import SCENARIOS, Scenario
from .request import webob_to_django_response, django_to_webob_request


LOG_STREAM = None


def setup_logging():
    """Sets up an in-memory logger."""
    # Allow us to use `global` within this function.
    # pylint: disable=W0603
    global LOG_STREAM
    LOG_STREAM = StringIO()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    log_handler = logging.StreamHandler(LOG_STREAM)
    log_handler.setFormatter(logging.Formatter("<p>%(asctime)s %(name)s %(levelname)s: %(message)s</p>"))
    root_logger.addHandler(log_handler)

setup_logging()

log = logging.getLogger(__name__)


# We don't really have authentication and multiple students, just accept their
# id on the URL.
def get_student_id(request):
    """Get the student_id from the given request."""
    student_id = request.GET.get('student', 'student_1')
    return student_id


#---- Views -----

def index(_request):
    """Render `index.html`"""
    the_scenarios = sorted(SCENARIOS.items())
    return render_to_response('index.html', {
        'scenarios': [(desc, scenario.description) for desc, scenario in the_scenarios]
    })


@ensure_csrf_cookie
def show_scenario(request, scenario_id, view_name='student_view', template='block.html'):
    """
    Render the given `scenario_id` for the given `view_name`, on the provided `template`.

    `view_name` defaults to 'student_view'.
    `template` defaults to 'block.html'.

    """
    student_id = get_student_id(request)
    log.info("Start show_scenario %r for student %s", scenario_id, student_id)

    try:
        scenario = SCENARIOS[scenario_id]
    except KeyError:
        # Hmm, someone wants a class scenario auto-generated.
        description = "Auto-generated for %s" % scenario_id
        usage = Usage(scenario_id, [])
        scenario = Scenario(description, usage)
        SCENARIOS[scenario_id] = scenario

    usage = scenario.usage
    usage.store_initial_state()
    block = create_xblock(usage, student_id)
    frag = block.runtime.render(block, {}, view_name)
    log.info("End show_scenario %s", scenario_id)
    return render_to_response(template, {
        'scenario': scenario,
        'block': block,
        'body': frag.body_html(),
        'database': MEMORY_KVS,
        'head_html': frag.head_html(),
        'foot_html': frag.foot_html(),
        'log': LOG_STREAM.getvalue(),
        'student_id': student_id,
        'usage': usage,
    })


def handler(request, usage_id, handler_slug):
    """Provide a handler for the request."""
    student_id = get_student_id(request)
    log.info("Start handler %s/%s for student %s", usage_id, handler_slug, student_id)
    usage = Usage.find_usage(usage_id)
    block = create_xblock(usage, student_id)
    request = django_to_webob_request(request)
    request.path_info_pop()
    request.path_info_pop()
    result = block.runtime.handle(block, handler_slug, request)
    log.info("End handler %s/%s", usage_id, handler_slug)
    return webob_to_django_response(result)


def package_resource(_request, package, resource):
    """
    Wrapper for `pkg_resources` that tries to access a resource and, if it
    is not found, raises an Http404 error.
    """
    if ".." in resource:
        raise Http404
    try:
        content = pkg_resources.resource_string(package, "static/" + resource)
    except IOError:
        raise Http404
    mimetype, _ = mimetypes.guess_type(resource)
    return HttpResponse(content, mimetype=mimetype)
