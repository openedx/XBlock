"""Test the workbench views."""

import json

from django.test.client import Client
from django.test import TestCase

from mock import patch
from nose.tools import assert_raises

from workbench import scenarios
from workbench.runtime import Usage
from xblock.core import XBlock, String, Scope
from xblock.fragment import Fragment


class TestMultipleViews(TestCase):
    """Test that we can request multiple views from an XBlock."""

    class MultiViewXBlock(XBlock):
        """A bare-bone XBlock with two views."""
        def student_view(self, context):
            return Fragment(u"This is student view!")

        def another_view(self, context):
            return Fragment(u"This is another view!")

    @patch('xblock.core.XBlock.load_class', return_value=MultiViewXBlock)
    def test_multiple_views(self, mock_load_classes):
        c = Client()

        # The default view is student_view
        response = c.get("/view/multiview/")
        self.assertIn("This is student view!", response.content)

        # We can ask for student_view directly
        response = c.get("/view/multiview/student_view/")
        self.assertIn("This is student view!", response.content)

        # We can also ask for another view.
        response = c.get("/view/multiview/another_view/")
        self.assertIn("This is another view!", response.content)


class XBlockWithHandlerAndStudentState(XBlock):

    the_data = String(default="def", scope=Scope.user_state)

    def student_view(self, context):
        body = u"The data: %r." % self.the_data
        body += u":::%s:::" % self.runtime.handler_url("update_the_data")
        return Fragment(body)

    @XBlock.json_handler
    def update_the_data(self, data):
        self.the_data = self.the_data + "x"
        return {'the_data': self.the_data}


@patch('xblock.core.XBlock.load_class', return_value=XBlockWithHandlerAndStudentState)
def test_xblock_with_handler_and_student_state(mock_load_class):
    c = Client()

    # Initially, the data is the default.
    response = c.get("/view/xblockwithhandlerandstudentstate/")
    assert "The data: 'def'." in response.content
    parsed = response.content.split(':::')
    assert len(parsed) == 3
    handler_url = parsed[1]

    # Now change the data.
    response = c.post(handler_url, "{}", "text/json")
    the_data = json.loads(response.content)['the_data']
    assert the_data == "defx"

    # Change it again.
    response = c.post(handler_url, "{}", "text/json")
    the_data = json.loads(response.content)['the_data']
    assert the_data == "defxx"


class XBlockWithoutHandlerAndStudentState(XBlock):

    the_data = String(default="def", scope=Scope.user_state)

    def student_view(self, context):
        body = u"The data: %r." % self.the_data
        body += u":::%s:::" % self.runtime.handler_url("update_the_data")
        return Fragment(body)


@patch('xblock.core.XBlock.load_class', return_value=XBlockWithoutHandlerAndStudentState)
def test_xblock_with_fallback_handler_and_student_state(mock_load_class):
    c = Client()

    # Initially, the data is the default.
    response = c.get("/view/xblockwithouthandlerandstudentstate/")
    assert "The data: 'def'." in response.content
    parsed = response.content.split(':::')
    assert len(parsed) == 3
    handler_url = parsed[1]

    # Now try changing the data. We don't have a handler so this should fail.
    assert_raises(Exception,  c.post, handler_url, "{}", "text/json")
