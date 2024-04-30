"""Helpers for WebOb requests and responses."""
from itertools import chain, repeat
from lazy import lazy

import webob
from django.http import StreamingHttpResponse, HttpResponse
from webob.multidict import MultiDict, NestedMultiDict, NoVars


def webob_to_django_response(webob_response, streaming=False):
    """Returns a django response to the `webob_response`"""
    if streaming:
        django_response = StreamingHttpResponse(
            webob_response.app_iter,
            content_type=webob_response.content_type,
            status=webob_response.status_code,
        )
    else:
        django_response = HttpResponse(
            webob_response.app_iter,
            content_type=webob_response.content_type,
            status=webob_response.status_code,
        )
    for name, value in webob_response.headerlist:
        django_response[name] = value
    return django_response


def querydict_to_multidict(query_dict, wrap=None):
    """
    Returns a new `webob.MultiDict` from a `django.http.QueryDict`.

    If `wrap` is provided, it's used to wrap the values.

    """
    wrap = wrap or (lambda val: val)
    return MultiDict(chain.from_iterable(
        zip(repeat(key), (wrap(v) for v in vals))
        for key, vals in query_dict.lists()
    ))


class DjangoUploadedFile:
    """
    Looks like a cgi.FieldStorage, but wraps a Django UploadedFile.
    """
    def __init__(self, uploaded):
        # FieldStorage needs a file attribute.
        self.file = uploaded

    @property
    def name(self):
        """The name of the input element used to upload the file."""
        return self.file.field_name

    @property
    def filename(self):
        """The name of the uploaded file."""
        return self.file.name


class DjangoWebobRequest(webob.Request):
    """
    An implementation of the webob request api, backed
    by a django request
    """
    def __init__(self, request):
        self._request = request
        super().__init__(self.environ)

    @lazy
    def environ(self):
        """
        Add path_info to the request's META dictionary.
        """
        environ = dict(self._request.META)

        environ['PATH_INFO'] = self._request.path_info

        return environ

    @property
    def GET(self):
        """
        Returns a new `webob.MultiDict` from the request's GET query.
        """
        return querydict_to_multidict(self._request.GET)

    @property
    def POST(self):
        if self.method not in ('POST', 'PUT', 'PATCH'):
            return NoVars('Not a form request')

        # Webob puts uploaded files into the POST dictionary, so here we
        # combine the Django POST data and uploaded FILES data into a single
        # dict.
        return NestedMultiDict(
            querydict_to_multidict(self._request.POST),
            querydict_to_multidict(self._request.FILES, wrap=DjangoUploadedFile),
        )

    @property
    def body(self):
        """
        Return the content of the request body.
        """
        return self._request.body

    @property
    def body_file(self):
        """
        Input stream of the request
        """
        return self._request


def django_to_webob_request(django_request):
    """Returns a WebOb request to the `django_request`"""
    return DjangoWebobRequest(django_request)
