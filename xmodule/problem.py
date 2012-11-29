"""Problem XModule, and friends."""

from .core import XModule, register_view, register_handler
from .widget import Widget


class ProblemModule(XModule):
    # The content controls how the Inputs attach to Graders
    @register_view("student_view")
    def student_view(self, context):
        result = Widget("Hey There!")
        return result


class InputModule(XModule):
    pass

class TextInputModule(InputModule):
    # Maybe name this differently, so that Problems draw their inputs specially?
    @register_view("student_view")
    def student_view(self, context):
        result = Widget("<input val='Type here'></input>")
        return result


