"""Test the workbench views."""

from django.test.client import Client
from django.test import TestCase

from mock import patch

from workbench import scenarios
from workbench.runtime import Usage
from xblock.core import XBlock
from xblock.fragment import Fragment


class TestMultipleViews(TestCase):
    """Test that we can request multiple views from an XBlock."""

    class MultiViewXBlock(XBlock):
        """A bare-bone XBlock with two views."""
        def student_view(self, context):
            return Fragment(u"This is student view!")

        def another_view(self, context):
            return Fragment(u"This is another view!")


    def setUp(self):
        scenarios.SCENARIOS.append(
            scenarios.Scenario("a test multi-view scenario", Usage("multiview"))
        )
        self.scenario_number = len(scenarios.SCENARIOS) - 1

    def tearDown(self):
        scenarios.SCENARIOS.pop()

    @patch('xblock.core.XBlock.load_class', return_value=MultiViewXBlock)
    def test_multiple_views(self, mock_load_classes):
        c = Client()

        # The default view is student_view
        response = c.get("/scenario/%d/" % self.scenario_number)
        self.assertIn("This is student view!", response.content)

        # We can ask for student_view directly
        response = c.get("/scenario/%d/student_view/" % self.scenario_number)
        self.assertIn("This is student view!", response.content)

        # We can also ask for another view.
        response = c.get("/scenario/%d/another_view/" % self.scenario_number)
        self.assertIn("This is another view!", response.content)
