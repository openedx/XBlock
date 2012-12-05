"""Content-oriented XBlocks."""

from .core import XBlock
from .widget import Widget

class HelloWorldBlock(XBlock):
    """A simple block: just show some fixed content."""
    @XBlock.view('student_view')
    def student_view(self, context):
        return Widget("Hello, world!")
