"""An XBlock to use as a child when you don't care what child to show.

This code is in the Debugger layer.

"""

from xblock.core import XBlock
from xblock.fragment import Fragment

class DebuggingChildBlock(XBlock):
    """A simple gray box, to use as a child placeholder."""
    @XBlock.view('student_view')
    def student_view_method(self, context):
        frag = Fragment("<div class='debug_child'></div>")
        frag.add_css("""
            .debug_child {
                background-color: grey;
                width: 200px;
                height: 100px;
                margin: 10px;
            }
            """)
        return frag
