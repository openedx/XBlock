"""Structure-oriented XBlocks."""

from xblock.core import XBlock
from xblock.fragment import Fragment


class Sequence(XBlock):
    """
    XBlock that models edx-platform style sequentials.

    WARNING: This is an experimental module, subject to future change or removal.
    """
    has_children = True

    def student_view(self, context=None):
        """Provide default student view."""
        frag = Fragment()
        child_frags = self.runtime.render_children(self, context)
        frag.add_frags_resources(child_frags)

        frag.add_content(self.runtime.render_template("sequence.html", children=child_frags))

        frag.add_css_url('http://code.jquery.com/ui/1.9.2/themes/base/jquery-ui.css')
        frag.add_javascript_url('http://ajax.googleapis.com/ajax/libs/jqueryui/1.9.2/jquery-ui.min.js')

        # mess things up
        frag.add_javascript("""
            function Sequence(runtime, element) {
              $(element).children('.tabs').tabs();
            };
            """)
        frag.initialize_js('Sequence')
        return frag


class VerticalBlock(XBlock):
    """A simple container."""
    has_children = True

    def student_view(self, context=None):
        """Provide default student view."""
        result = Fragment()
        child_frags = self.runtime.render_children(self, context=context)
        result.add_frags_resources(child_frags)
        result.add_css("""
            .vertical {
                border: solid 1px #888; padding: 3px;
            }
            """)
        result.add_content(self.runtime.render_template("vertical.html", children=child_frags))
        return result


class SidebarBlock(XBlock):
    """A slightly-different vertical."""
    has_children = True

    def student_view(self, context=None):
        """Provide default student view."""
        result = Fragment()
        child_frags = self.runtime.render_children(self, context)
        result.add_frags_resources(child_frags)
        result.add_css("""
            .sidebar {
                border: solid 1px #888;
                padding: 10px;
                background: #ccc;
            }
            """)
        html = []
        html.append(u"<div class='sidebar'>")
        for child in child_frags:
            html.append(child.body_html())
        html.append(u"</div>")
        result.add_content("".join(html))
        return result
