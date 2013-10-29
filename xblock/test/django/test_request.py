"""
Test the xblock.django.request module, which provides helper functionality for
converting django requests to webob requests and webob responses to django
responses.
"""

from django.test.client import RequestFactory
from nose.tools import assert_equals  # pylint: disable=no-name-in-module

from xblock.django.request import django_to_webob_request


class TestDjangoWebobRequest(object):
    """
    Tests of the django_to_webob_request function
    """
    def setUp(self):
        self.req_factory = RequestFactory()

    def test_post_already_read(self):
        # Check that POST already having been read from doesn't
        # prevent access to the POST of the webob object

        dj_req = self.req_factory.post('dummy_url', data={'foo': 'bar'})

        # Read from POST before constructing the webob request
        assert_equals(dj_req.POST.getlist('foo'), ['bar'])  # pylint: disable=no-member

        webob_req = django_to_webob_request(dj_req)
        assert_equals(webob_req.POST.getall('foo'), ['bar'])
