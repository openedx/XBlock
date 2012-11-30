"""Problem XModule, and friends."""

from .core import XModule, ModelBase, Children, register_view, register_handler
from .widget import Widget


class ProblemModule(XModule):
    class Model(ModelBase):
        children = Children()

    # The content controls how the Inputs attach to Graders
    @register_view("student_view")
    def student_view(self, context):
        result = Widget("<p>A Problem:</p>")
        child_widgets = [child.render(context) for child in self.children]
        result.add_widgets_resources(child_widgets)
        result.add_content(self.runtime.render_template("vertical.html", children=child_widgets))
        return result


class InputModule(XModule):
    pass

class TextInputModule(InputModule, XModule):
    # Maybe name this differently, so that Problems draw their inputs specially?
    @register_view("student_view")
    def student_view(self, context):
        result = Widget("<input val='Type here'></input>")
        return result
