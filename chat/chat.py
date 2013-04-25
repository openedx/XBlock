"""
An XBlock presenting a Candy.js chat widget.

Author: Nate Hardison <nate@edx.org>
"""

from xblock.fragment import Fragment
from xblock.structure import VerticalBlock

from django.conf import settings
from django.template.loader import render_to_string

import logging
log = logging.getLogger(__name__)

class ChatBlock(VerticalBlock):
    """
    An XBlock providing a Candy.js chat widget.
    """

    # TODO: how can we leverage the "context" object that gets passed in?
    def student_view(self, context):
        context = settings.CHAT

        # The Candy.js plugin needs to know where we've stored its static
        # assets, so we pass the path in the context to our JS template.
        context["candy_resources"] = settings.STATIC_URL + "vendor/candy_res"

        frag = Fragment(render_to_string("chat.html", context))

        # Set up the Candy.js resource CSS
        frag.add_css_url(settings.STATIC_URL + "vendor/candy_res/candy_full.css")
        frag.add_css("""
            .wrapper-chat {
                position: relative;
                height: 300;
                width: 500;
            }
        """)

        # Load up the Candy.js libs that we'll need
        frag.add_javascript_url(settings.STATIC_URL + "js/vendor/candy_libs/libs.min.js")
        frag.add_javascript_url(settings.STATIC_URL + "js/vendor/candy.min.js")

        # Render our loading JS as a template so that we can easily plug
        # in context information
        frag.add_javascript(render_to_string("chat.js", context))

        frag.initialize_js("initializeChat")
        return frag

    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("simple chat widget",
            """\
                <vertical>
                    <chat/>
                </vertical>
            """)
        ]
