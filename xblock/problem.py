"""Problem XBlock, and friends."""

from .core import XBlock, register_view, register_handler
from .widget import Widget


class ProblemBlock(XBlock):

    has_children = True

    # The content controls how the Inputs attach to Graders
    @register_view("student_view")
    def student_view(self, context):
        result = Widget("<p>A Problem:</p>")
        child_widgets = [self.runtime.render_child(child, context, "problem_view") for child in self.children]
        result.add_widgets_resources(child_widgets)
        result.add_content(self.runtime.render_template("vertical.html", children=child_widgets))
        return result


class InputBlock(XBlock):
    pass

class TextInputBlock(InputBlock):
    @register_view("student_view")
    def student_view(self, context):
        return Widget("<p>I can only appear inside problems.</p>")

    @register_view("problem_view")
    def problem_view(self, context):
        result = Widget("<input val='Type here'></input>")
        return result
