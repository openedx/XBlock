"""Structure-oriented XBlocks."""

from .core import XBlock
from .widget import Widget

class VerticalBlock(XBlock):
    """A simple container."""
    has_children = True

    @XBlock.view('student_view')
    def render_student(self, context):
        result = Widget()
        # TODO: self.runtime.children is actual children here, not ids...
        child_widgets = [self.runtime.render_child(child, context) for child in self.children]
        result.add_widgets_resources(child_widgets)
        result.add_content(self.runtime.render_template("vertical.html", children=child_widgets))
        return result
