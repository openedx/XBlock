"""A proxy for a remoted XBlock."""

import json
import requests
import webob

from wsgiproxy.app import WSGIProxyApp

from xblock.core import XBlock
from xblock.fragment import Fragment

from debugger.request import requests_to_webob_response


class DirectRemoteBlockProxy(XBlock):
    """The XBlock proxy in the local server for the direct protocol."""

    def set_remote(self, server):
        self.server = server

    @XBlock.fallback_view
    def view(self, view_name, context):
        payload = {
            'student_id': self.runtime.student_id,
        }
        url = "%s/remote/view_direct/%s/%s" % (self.server, self.runtime.usage.id, view_name)
        headers = {'Content-type': 'application/json'}
        r = requests.post(url, data=json.dumps(payload), headers=headers)
        if r.status_code == 200:
            frag = Fragment.from_pods(r.json())
        else:
            frag = Fragment(u"Oops: %s" % r.status_code)
        return frag

    @XBlock.fallback_handler
    def handler(self, handler_name, request):
        app = WSGIProxyApp(self.server)
        path_prefix = "/remote/handler_direct/%s/%s" % (self.runtime.usage.id, handler_name)
        request.path_info = path_prefix + request.path_info
        request.headers['X-edX-StudentId'] = self.runtime.student_id
        response = request.get_response(app)
        return response


class TunneledRemoteBlockProxy(DirectRemoteBlockProxy):
    """The XBlock proxy in the local server for the tunneled protocol."""

    # (The view is the same, ugh, but doesn't inherit)
    @XBlock.fallback_view
    def view2(self, view_name, context):
        return self.view(view_name, context)

    @XBlock.fallback_handler
    def handler(self, handler_name, request):
        url = "%s/remote/handler_tunneled/%s/%s" % (self.server, self.runtime.usage.id, handler_name)
        payload = {
            'json': json.dumps({
                'student_id': self.runtime.student_id,
            }),
        }
        files = {'request.http': request.as_bytes()}
        r = requests.post(url, data=payload, files=files)
        if r.status_code == 200:
            response = requests_to_webob_response(r)
        else:
            # TODO: hard to know what the Javascript is looking for in this case...
            response = webob.Response("Couldn't proxy handler to remote server: %d" % r.status_code)
        return response

# Choose the way you want to remote the block..
RemoteBlockProxy = TunneledRemoteBlockProxy
