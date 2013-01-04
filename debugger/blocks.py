"""An XBlock to use as a child when you don't care what child to show.

This code is in the Debugger layer.

"""

from xblock.core import XBlock
from xblock.fragment import Fragment

from .util import make_safe_for_html

class DebuggingChildBlock(XBlock):
    """A simple gray box, to use as a child placeholder."""
    @XBlock.fallback_view
    def any_view(self, view_name, context):
        frag = Fragment("<div class='debug_child'>%s<br>%s</div>" % (make_safe_for_html(repr(self)), view_name))
        frag.add_css("""
            .debug_child {
                background-color: grey;
                width: 300px;
                height: 100px;
                margin: 10px;
                padding: 5px 10px;
                font-size: 75%;
            }
            """)
        return frag
