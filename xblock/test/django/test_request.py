"""
Test the xblock.django.request module, which provides helper functionality for
converting django requests to webob requests and webob responses to django
responses.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# Set up Django settings
from unittest import TestCase

# pylint: disable=wrong-import-position
try:
    # pylint: disable=import-error
    from django.test.client import RequestFactory
    from django.http.request import RawPostDataException
    from rest_framework.request import Request as DRFRequest
    from rest_framework.parsers import FormParser, JSONParser
    HAS_DJANGO = True
except ImportError:
    HAS_DJANGO = False

import ddt
import pytest
from webob import Response

from xblock import django  # pylint: disable=unused-import
from xblock.django.request import django_to_webob_request, webob_to_django_response
# pylint: enable=wrong-import-position


@pytest.mark.skipif(not HAS_DJANGO, reason='Django not available')
@ddt.ddt
class TestDjangoWebobRequest(TestCase):
    """
    Tests of the django_to_webob_request function
    """
    def setUp(self):
        self.request_factory = RequestFactory()

    def _django_request(self, data, content_type):
        return self.request_factory.post(
            '/xblock/handler/', data=data, content_type=content_type
        )

    def _drf_request(self, data, content_type):
        return DRFRequest(
            self._django_request(data, content_type), parsers=[FormParser(), JSONParser()]
        )

    def test_post_already_read_for_django_request(self):
        # Check that POST already having been read from doesn't
        # prevent access to the POST of the webob object
        dj_req = self.request_factory.post('dummy_url', data={'foo': 'bar'})

        # Read from POST before constructing the webob request
        self.assertEqual(dj_req.POST.getlist('foo'), ['bar'])  # pylint: disable=no-member

        webob_req = django_to_webob_request(dj_req)
        self.assertEqual(webob_req.POST.getall('foo'), ['bar'])

    def test_json_data_already_read_for_drf_request(self):

        drf_request = self._drf_request('{"key1": "value1"}', 'application/json')

        # drf_request.POST is empty when content_type is application_json.
        self.assertEqual(list(drf_request.POST), [])

        webob_request = django_to_webob_request(drf_request)

        # django_request.read() is called in drf_request.POST, so accessing body after that raises Exception.
        with pytest.raises(RawPostDataException):
            drf_request.body
        with pytest.raises(RawPostDataException):
            webob_request.body

        # json_data should return drf_request.data instead of parsing body again.
        webob_request.json_data

    @ddt.data(
        ('{"key1": "value1"}', 'application/json', True),
        ('{"key1" "value1"}', 'application/json', False),
        ('{"key1": "value1"}', 'application/x-www-form-urlencoded', True),  # Supported for backwards compatibility.
        ('key1=value1&key2=value2', 'application/x-www-form-urlencoded', False),
    )
    @ddt.unpack
    def test_json_data_with_django_request(self, data, content_type, success):

        webob_request = django_to_webob_request(
            self._django_request(data, content_type)
        )
        if success:
            self.assertEqual(webob_request.json_data['key1'], 'value1')
        else:
            with pytest.raises(ValueError):
                webob_request.json_data

    @ddt.data(
        ('{"key1": "value1"}', 'application/json', True),
        ('{"key1" "value1"}', 'application/json', False),
        ('{"key1": "value1"}', 'application/x-www-form-urlencoded', True),  # Supported for backwards compatibility.
        ('key1=value1&key2=value2', 'application/x-www-form-urlencoded', False),
    )
    @ddt.unpack
    def test_json_data_with_drf_request(self, data, content_type, success):
        webob_request = django_to_webob_request(
            self._drf_request(data, content_type)
        )
        if success:
            self.assertEqual(webob_request.json_data['key1'], 'value1')
        else:
            with pytest.raises(ValueError):
                webob_request.json_data


@pytest.mark.skipif(not HAS_DJANGO, reason='Django not available')
class TestDjangoWebobResponse(TestCase):
    """
    Tests of the webob_to_django_response function
    """
    def _as_django(self, *args, **kwargs):
        """
        Return a :class:`django.http.HttpResponse` created from a `webob.Response`
        initialized with `*args` and `**kwargs`
        """
        return webob_to_django_response(Response(*args, **kwargs))

    def test_status_code(self):
        self.assertEqual(self._as_django(status=200).status_code, 200)
        self.assertEqual(self._as_django(status=404).status_code, 404)
        self.assertEqual(self._as_django(status=500).status_code, 500)

    def test_content(self):
        self.assertEqual(self._as_django(body="foo").content, b"foo")
        self.assertEqual(self._as_django(app_iter=(c for c in "foo")).content, b"foo")
        self.assertEqual(self._as_django(body=b"foo", charset="utf-8").content, b"foo")

        encoded_snowman = "\N{SNOWMAN}".encode('utf-8')
        self.assertEqual(self._as_django(body=encoded_snowman, charset="utf-8").content, encoded_snowman)

    def test_headers(self):
        self.assertIn('X-Foo', self._as_django(headerlist=[('X-Foo', 'bar')]))
        self.assertEqual(self._as_django(headerlist=[('X-Foo', 'bar')])['X-Foo'], 'bar')

    def test_content_types(self):
        # JSON content type (no charset should be returned)
        self.assertEqual(
            self._as_django(content_type='application/json')['Content-Type'],
            'application/json'
        )

        # HTML content type (UTF-8 charset should be returned)
        self.assertEqual(
            self._as_django(content_type='text/html')['Content-Type'],
            'text/html; charset=UTF-8'
        )
