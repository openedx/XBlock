from xblock.core import XBlock, register_view
from xblock.widget import Widget

class DebuggingChildBlock(XBlock):
    """A simple gray box, to use as a child placeholder."""
    @register_view('student_view')
    def student_view(self, context):
        widget = Widget("<div class='debug_child'></div>")
        widget.add_css("""
            .debug_child {
                background-color: grey;
                width: 200px;
                height: 100px;
                margin: 10px;
            }
            """)
        widget.initialize_js("foo")
        return widget
