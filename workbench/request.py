"""Helpers for WebOb requests and responses."""

import webob


def webob_to_django_response(webob_response):
    from django.http import HttpResponse
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

    webob_request = webob.Request(django_request.META)
    webob_request.body = django_request.body
    return webob_request


def requests_to_webob_response(r):
    response = webob.Response()
    response.status = r.status_code
    response.body = r.content
    for hname, hvalue in r.headers.iteritems():
        response.headers[hname] = hvalue
    return response
