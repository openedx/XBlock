"""A proxy for a remoted XBlock."""

import json
import requests

from wsgiproxy.app import WSGIProxyApp

from xblock.core import XBlock
from xblock.fragment import Fragment

class RemoteBlockProxy(XBlock):

    def set_remote(self, server):
        self.server = server

    @XBlock.fallback_view
    def view(self, view_name, context):
        payload = {
            'student_id': self.runtime.student_id,
        }
        url = "%s/remote/view/%s/%s" % (self.server, self.runtime.usage.id, view_name)
        headers = {'Content-type': 'application/json'}
        r = requests.post(url, data=json.dumps(payload), headers=headers)
        if r.status_code != 200:
            frag = Fragment(u"Oops: %s" % r.status_code)
        else:
            frag = Fragment.from_pods(r.json())
        return frag

    @XBlock.fallback_handler
    def handler(self, handler_name, request):
        app = WSGIProxyApp(self.server)
        path_prefix = "/remote/handler/%s/%s" % (self.runtime.usage.id, handler_name)
        request.path_info = path_prefix + request.path_info
        request.headers['X-edX-StudentId'] = self.runtime.student_id
        response = request.get_response(app)
        return response
