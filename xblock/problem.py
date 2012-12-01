"""Problem XBlock, and friends."""

from .core import XBlock, register_view, register_handler
from .widget import Widget


class ProblemBlock(XBlock):

    has_children = True

    # The content controls how the Inputs attach to Graders
    @register_view("student_view")
    def student_view(self, context):
        result = Widget("<p>A Problem:</p>")
        child_widgets = [self.runtime.render_child(child, context) for child in self.children]
        result.add_widgets_resources(child_widgets)
        result.add_content(self.runtime.render_template("vertical.html", children=child_widgets))
        return result


class InputBlock(XBlock):
    pass

class TextInputBlock(InputBlock):
    # Maybe name this differently, so that Problems draw their inputs specially?
    @register_view("student_view")
    def student_view(self, context):
        result = Widget("<input val='Type here'></input>")
        return result
