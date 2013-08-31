"""Test the workbench views."""

import functools
import json

from django.test.client import Client

from mock import patch
from nose.tools import assert_equal, assert_in, assert_raises, assert_true  # pylint: disable=E0611

from xblock.core import XBlock, String, Scope
from xblock.fragment import Fragment
from xblock.runtime import NoSuchHandlerError

from workbench import scenarios
from workbench.runtime import USAGE_STORE


def temp_scenario(temp_class, scenario_name='test_scenario'):
    """Create a temporary scenario that uses `temp_class`."""
    def _decorator(func):                               # pylint: disable=C0111
        @functools.wraps(func)
        @patch('xblock.core.XBlock.load_class', return_value=temp_class)
        def _inner(_mock):                              # pyline: disable=C0111
            # Create a scenario, just one tag for our mocked class.
            scenarios.add_xml_scenario(
                scenario_name, "Temporary scenario",
                "<%s/>" % temp_class.__name__
            )
            try:
                return func(*args, **kwargs)
            finally:
                scenarios.remove_scenario(scenario_name)
        return _inner
    return _decorator


class MultiViewXBlock(XBlock):
    """A bare-bone XBlock with two views."""
    def student_view(self, context):  # pylint: disable=W0613
        """A view, with the default name."""
        return Fragment(u"This is student view!")

    def another_view(self, context):  # pylint: disable=W0613
        """A secondary view for this block."""
        return Fragment(u"This is another view!")


@temp_scenario(MultiViewXBlock, "multiview")
def test_multiple_views():
    client = Client()

    # The default view is student_view
    response = client.get("/view/multiview/")
    assert_in("This is student view!", response.content)

    # We can ask for student_view directly
    response = client.get("/view/multiview/student_view/")
    assert_in("This is student view!", response.content)

    # We can also ask for another view.
    response = client.get("/view/multiview/another_view/")
    assert_in("This is another view!", response.content)


class XBlockWithHandlerAndStudentState(XBlock):
    """A bare-bone XBlock with one view and one json handler."""
    the_data = String(default="def", scope=Scope.user_state)

    def student_view(self, context):  # pylint: disable=W0613
        """Provide the default view."""
        body = u"The data: %r." % self.the_data
        body += u":::%s:::" % self.runtime.handler_url(self, "update_the_data")
        return Fragment(body)

    @XBlock.json_handler
    def update_the_data(self, _data):
        """Mock handler that updates the student state."""
        self.the_data = self.the_data + "x"
        return {'the_data': self.the_data}


@temp_scenario(XBlockWithHandlerAndStudentState, 'testit')
def test_xblock_with_handler():
    # Tests an XBlock that provides a handler, and has some simple
    # student state
    client = Client()

    # Initially, the data is the default.
    response = client.get("/view/testit/")
    assert_true("The data: 'def'." in response.content)
    parsed = response.content.split(':::')
    assert_equal(len(parsed), 3)
    handler_url = parsed[1]

    # Now change the data.
    response = client.post(handler_url, "{}", "text/json")
    the_data = json.loads(response.content)['the_data']
    assert_equal(the_data, "defx")

    # Change it again.
    response = client.post(handler_url, "{}", "text/json")
    the_data = json.loads(response.content)['the_data']
    assert_equal(the_data, "defxx")


@temp_scenario(XBlock)
def test_xblock_without_handler():
    # Test that an XBlock without a handler raises an Exception
    # when we try to hit a handler on it
    client = Client()

    # Pick a random usage_id from the USAGE_STORE because we
    # need to ensure the usage is a valid id
    usage_id = USAGE_STORE._all.keys()[0]
    # Plug that usage_id into a mock handler URL
    # /handler/[usage_id]/[handler_name]
    handler_url = "/handler/" + usage_id + "/does_not_exist/?student=student_doesntexist"

    # The default XBlock implementation doesn't provide
    # a handler, so this call should raise an exception
    # (from xblock.runtime.Runtime.handle)
    with assert_raises(NoSuchHandlerError):
        client.post(handler_url, '{}', 'text/json')


@temp_scenario(XBlock)
def test_xblock_invalid_handler_url():
    # Test that providing an invalid handler url will give a 404
    # when we try to hit a handler on it
    client = Client()

    handler_url = "/handler/obviously/a/fake/handler"
    result = client.post(handler_url, '{}', 'text/json')
    assert_equal(result.status_code, 404)


class XBlockWithoutStudentView(XBlock):
    """
    Test WorkbechRuntime.render caught `NoSuchViewError` exception path
    """
    the_data = String(default="def", scope=Scope.user_state)


@temp_scenario(XBlockWithoutStudentView, 'xblockwithoutstudentview')
def test_xblock_no_student_view():
    # Try to get a response. Will try to render via WorkbenchRuntime.render;
    # since no view is provided in the XBlock, will return a Fragment that
    # indicates there is no view available.
    client = Client()
    response = client.get("/view/xblockwithoutstudentview/")
    assert_true('No such view' in response.content)
