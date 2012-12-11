"""Structure-oriented XBlocks."""

from .core import XBlock
from .widget import Widget

class Sequence(XBlock):
    has_children = True

    @XBlock.view('student_view')
    def render_student(self, context):
        widget = Widget()
        child_widgets = [self.runtime.render_child(child, context) for child in self.children]
        widget.add_widgets_resources(child_widgets)

        progress_per_child = [self.runtime.collect('progress', block) for block in self.children]

        # TODO: [rocha] calculate total progress per child
        from pprint import pprint
        pprint(progress_per_child)

        widget.add_content(self.runtime.render_template("sequence.html", children=child_widgets))

        widget.add_css_url('http://code.jquery.com/ui/1.9.2/themes/base/jquery-ui.css')
        widget.add_javascript_url('http://ajax.googleapis.com/ajax/libs/jqueryui/1.9.2/jquery-ui.min.js')

        # mess things up
        widget.add_javascript("""
            function Sequence(runtime, element) {
              $(element).children('.tabs').tabs();
            };
            """)
        widget.initialize_js('Sequence')
        return widget


class VerticalBlock(XBlock):
    """A simple container."""
    has_children = True

    @XBlock.view('student_view')
    def render_student(self, context):
        result = Widget()
        # TODO: self.runtime.children is actual children here, not ids...
        child_widgets = [self.runtime.render_child(child, context) for child in self.children]
        result.add_widgets_resources(child_widgets)
        result.add_css("""
            .vertical {
                border: solid 1px #888; padding: 3px;
            }
            """)
        result.add_content(self.runtime.render_template("vertical.html", children=child_widgets))
        return result
