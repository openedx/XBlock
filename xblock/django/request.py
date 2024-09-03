"""Helpers for WebOb requests and responses."""
from __future__ import annotations

import typing as t
from itertools import chain, repeat
from lazy import lazy

import webob
import webob.multidict
import django.core.files.uploadedfile
import django.http
import django.utils.datastructures


def webob_to_django_response(
    webob_response: webob.Response,
    streaming: bool = False
) -> django.http.HttpResponse | django.http.StreamingHttpResponse:
    """Returns a django response to the `webob_response`"""
    django_response: django.http.HttpResponse | django.http.StreamingHttpResponse
    if streaming:
        django_response = django.http.StreamingHttpResponse(
            webob_response.app_iter,
            content_type=webob_response.content_type,
            status=webob_response.status_code,
        )
    else:
        django_response = django.http.HttpResponse(
            webob_response.app_iter,
            content_type=webob_response.content_type,
            status=webob_response.status_code,
        )
    for name, value in webob_response.headerlist:
        django_response[name] = value
    return django_response


def querydict_to_multidict(
    query_dict: django.utils.datastructures.MultiValueDict,
    wrap: t.Callable[[t.Any], t.Any] | None = None
) -> webob.multidict.MultiDict:
    """
    Returns a new `webob.MultiDict` from a `django.http.QueryDict`.

    If `wrap` is provided, it's used to wrap the values.
    """
    wrap = wrap or (lambda val: val)
    return webob.multidict.MultiDict(chain.from_iterable(
        zip(repeat(key), (wrap(v) for v in vals))
        for key, vals in query_dict.lists()
    ))


class DjangoUploadedFile:
    """
    Looks like a cgi.FieldStorage, but wraps a Django UploadedFile.
    """
    def __init__(self, uploaded: django.core.files.uploadedfile.UploadedFile):
        # FieldStorage needs a file attribute.
        self.file: t.Any = uploaded

    @property
    def name(self) -> str:
        """The name of the input element used to upload the file."""
        return self.file.field_name

    @property
    def filename(self) -> str:
        """The name of the uploaded file."""
        return self.file.name


class DjangoWebobRequest(webob.Request):
    """
    An implementation of the webob request api, backed by a django request
    """
    # Note:
    # This implementation is close enough to webob.Request for it to work OK, but it does
    # make mypy complain that the type signatures are different, hence the 'type: ignore' pragmas.

    def __init__(self, request: django.http.HttpRequest):
        self._request = request
        super().__init__(self.environ)

    @lazy
    def environ(self) -> dict[str, str]:  # type: ignore[override]
        """
        Add path_info to the request's META dictionary.
        """
        environ = dict(self._request.META)

        environ['PATH_INFO'] = self._request.path_info

        return environ

    @property
    def GET(self) -> webob.multidict.MultiDict:  # type: ignore[override]
        """
        Returns a new `webob.MultiDict` from the request's GET query.
        """
        return querydict_to_multidict(self._request.GET)

    @property
    def POST(self) -> webob.multidict.MultiDict | webob.multidict.NoVars:  # type: ignore[override]
        if self.method not in ('POST', 'PUT', 'PATCH'):
            return webob.multidict.NoVars('Not a form request')

        # Webob puts uploaded files into the POST dictionary, so here we
        # combine the Django POST data and uploaded FILES data into a single
        # dict.
        return webob.multidict.NestedMultiDict(
            querydict_to_multidict(self._request.POST),
            querydict_to_multidict(self._request.FILES, wrap=DjangoUploadedFile),
        )

    @property
    def body(self) -> bytes:  # type: ignore[override]
        """
        Return the content of the request body.
        """
        return self._request.body

    @property  # type: ignore[misc]
    def body_file(self) -> django.http.HttpRequest:  # type: ignore[override]
        """
        Input stream of the request
        """
        return self._request


def django_to_webob_request(django_request: django.http.HttpRequest) -> webob.Request:
    """Returns a WebOb request to the `django_request`"""
    return DjangoWebobRequest(django_request)
