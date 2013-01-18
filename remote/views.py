"""Run a block in a remote location."""

import json
import webob

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from debugger.runtime import Usage, create_xblock
from debugger.request import webob_to_django_response, django_to_webob_request

# TODO: These Django views are awfully similar to the debugger's DJango views.
# This isn't surprising.  Should we refactor?

@csrf_exempt
@require_POST
def view(request, usage_id, view_name):
    payload = json.loads(request.raw_post_data)
    usage = Usage.find_usage(usage_id)
    block = create_xblock(usage, payload['student_id'])
    frag = block.runtime.render(block, {}, view_name)
    return HttpResponse(json.dumps(frag.to_pods()), content_type='application/json')

@csrf_exempt
@require_POST
def handler_direct(request, usage_id, handler_name):
    usage = Usage.find_usage(usage_id)
    block = create_xblock(usage, request.META['HTTP_X_EDX_STUDENTID'])
    request = django_to_webob_request(request)
    for _ in xrange(4):
        request.path_info_pop()
    response = block.runtime.handle(block, handler_name, request)
    return webob_to_django_response(response)

@csrf_exempt
@require_POST
def handler_tunneled(request, usage_id, handler_name):
    payload = json.loads(request.REQUEST.get("json"))
    usage = Usage.find_usage(usage_id)
    block = create_xblock(usage, payload['student_id'])
    remote_request = webob.Request.from_bytes(request.FILES['request.http'].read())
    response = block.runtime.handle(block, handler_name, remote_request)
    return webob_to_django_response(response)
