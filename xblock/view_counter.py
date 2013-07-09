""" Simple View Counting XBlock"""
from xblock.core import XBlock, Scope, Integer
from xblock.fragment import Fragment


class ViewCounter(XBlock):
    """
    A simple XBlock that implements a simple view counter
    """
    views = Integer(help="the number of times this block has been viewed",
                    default=0,
                    scope=Scope.content)

    def student_view(self, _context):
        """
        Render out the template.

        """
        self.views += 1
        html = VIEW_COUNTER_TEMPLATE.format(views=self.views)
        frag = Fragment(html)
        return frag


VIEW_COUNTER_TEMPLATE = u"""
<span class="views">{views}</span>
"""
