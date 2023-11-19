.. code-block:: python

    def student_view(self, context=None):  # pylint: disable=W0613
        """
        Create a fragment used to display the XBlock to a student.
        `context` is a dictionary used to configure the display (unused)

        Returns a `Fragment` object specifying the HTML, CSS, and JavaScript
        to display.
        """

        # Load the HTML fragment from within the package and fill in the template

        html_str = pkg_resources.resource_string(
            __name__,
            "static/html/thumbs.html".decode('utf-8')
        )
        frag = Fragment(str(html_str).format(block=self))

        # Load the CSS and JavaScript fragments from within the package
        css_str = pkg_resources.resource_string(
            __name__,
            "static/css/thumbs.css".decode('utf-8')
        )
        frag.add_css(str(css_str))

        js_str = pkg_resources.resource_string(
            __name__,
            "static/js/src/thumbs.js".decode('utf-8')
        )
        frag.add_javascript(str(js_str))

        frag.initialize_js('ThumbsBlock')
        return frag
