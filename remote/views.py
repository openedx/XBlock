"""Run a block in a remote location."""

import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from debugger.runtime import Usage, create_xblock


@csrf_exempt
@require_POST
def view(request, usage_id, view_name):
    payload = json.loads(request.raw_post_data)
    usage = Usage.find_usage(usage_id)
    block = create_xblock(usage, payload['student_id'], force_local=True)
    frag = block.runtime.render(block, {}, view_name)
    return HttpResponse(json.dumps(frag.to_pods()), content_type='application/json')

@csrf_exempt
@require_POST
def handler(request, usage_id, handler_name):
    payload = json.loads(request.raw_post_data)
    usage = Usage.find_usage(usage_id)
    block = create_xblock(usage, payload['student_id'], force_local=True)
    TODO(FINISH, THIS)
