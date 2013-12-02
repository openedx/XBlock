"""TODO: Write a description of what this XBlock is."""

import pkg_resources

from xblock.core import XBlock
from xblock.fields import Scope, Integer
from xblock.fragment import Fragment


class {{cookiecutter.class_name}}(XBlock):
    """
    A testing block that checks the behavior of the container.
    """

    # Fields are defined on the class.  You can access them in your code as
    # self.<fieldname>.

    count = Integer(
        default=0, scope=Scope.user_state,
        help="A simple counter, to show something happening",
    )

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def student_view(self, context=None):
        """
        The primary view of the {{cookiecutter.class_name}}, shown to students
        when viewing courses.
        """
        html = self.resource_string("static/html/{{cookiecutter.short_name}}.html")
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/{{cookiecutter.short_name}}.css"))
        frag.add_javascript(self.resource_string("static/js/src/{{cookiecutter.short_name}}.js"))
        frag.initialize_js('{{cookiecutter.class_name}}')
        return frag

    @XBlock.json_handler
    def increment_count(self, data, suffix=''):
        """
        An example handler, which increments the data.
        """
        # Just to show data coming in...
        assert data['hello'] == 'world'

        self.count += 1
        return {"count": self.count}

    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("{{cookiecutter.class_name}}",
             """<vertical_demo>
                <{{cookiecutter.short_name}}/>
                <{{cookiecutter.short_name}}/>
                <{{cookiecutter.short_name}}/>
                </vertical_demo>
             """
            )
        ]
