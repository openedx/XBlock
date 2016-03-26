"""
Test the xblock.django.request module, which provides helper functionality for
converting django requests to webob requests and webob responses to django
responses.
"""

# Set up Django settings
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xblock.test.settings")

# Django isn't always available, so skip tests if it isn't.
from nose.plugins.skip import SkipTest
try:
    from django.test.client import RequestFactory  # pylint: disable=import-error
    HAS_DJANGO = True
except ImportError:
    HAS_DJANGO = False

from unittest import TestCase
from webob import Response

from xblock.django.request import django_to_webob_request, webob_to_django_response


class TestDjangoWebobRequest(TestCase):
    """
    Tests of the django_to_webob_request function
    """
    def setUp(self):
        if not HAS_DJANGO:
            raise SkipTest("Django not available")

        self.req_factory = RequestFactory()

    def test_post_already_read(self):
        # Check that POST already having been read from doesn't
        # prevent access to the POST of the webob object
        dj_req = self.req_factory.post('dummy_url', data={'foo': 'bar'})

        # Read from POST before constructing the webob request
        self.assertEquals(dj_req.POST.getlist('foo'), ['bar'])  # pylint: disable=no-member

        webob_req = django_to_webob_request(dj_req)
        self.assertEquals(webob_req.POST.getall('foo'), ['bar'])


class TestDjangoWebobResponse(TestCase):
    """
    Tests of the webob_to_django_response function
    """

    def setUp(self):
        if not HAS_DJANGO:
            raise SkipTest("Django not available")

    def _as_django(self, *args, **kwargs):
        """
        Return a :class:`django.http.HttpResponse` created from a `webob.Response`
        initialized with `*args` and `**kwargs`
        """
        return webob_to_django_response(Response(*args, **kwargs))

    def test_status_code(self):
        self.assertEquals(self._as_django(status=200).status_code, 200)
        self.assertEquals(self._as_django(status=404).status_code, 404)
        self.assertEquals(self._as_django(status=500).status_code, 500)

    def test_content(self):
        self.assertEquals(self._as_django(body=u"foo").content, "foo")
        self.assertEquals(self._as_django(app_iter=(c for c in u"foo")).content, "foo")
        self.assertEquals(self._as_django(body="foo", charset="utf-8").content, "foo")

        encoded_snowman = u"\N{SNOWMAN}".encode('utf-8')
        self.assertEquals(self._as_django(body=encoded_snowman, charset="utf-8").content, encoded_snowman)

    def test_headers(self):
        self.assertIn('X-Foo', self._as_django(headerlist=[('X-Foo', 'bar')]))
        self.assertEquals(self._as_django(headerlist=[('X-Foo', 'bar')])['X-Foo'], 'bar')

    def test_content_types(self):
        # JSON content type (no charset should be returned)
        self.assertEquals(
            self._as_django(content_type='application/json')['Content-Type'],
            'application/json'
        )

        # HTML content type (UTF-8 charset should be returned)
        self.assertEquals(
            self._as_django(content_type='text/html')['Content-Type'],
            'text/html; charset=UTF-8'
        )
