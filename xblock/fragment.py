"""Fragments for XBlocks.

This code is in the Runtime layer.

"""


class Fragment(object):
    """A fragment of a web page, for XBlock views to return."""

    def __init__(self, content=None):
        self.content = u""
        self.resources = []
        self.cache_seconds = 0
        self.js_init = None
        if content is not None:
            self.add_content(content)

    def add_content(self, content):
        """Add content to this fragment.

        `content` is a Unicode string, HTML to append to the body of the
        fragment.  It must not contain a ``<body>`` tag, or otherwise assume
        that it is the only content on the page.

        """
        assert isinstance(content, unicode)
        self.content += content

    def add_resource(self, text, mimetype):
        self.resources.append(('text', text, mimetype))

    def add_resource_url(self, url, mimetype):
        self.resources.append(('url', url, mimetype))

    def add_css(self, text):
        self.add_resource(text, 'text/css')

    def add_css_url(self, url):
        self.add_resource_url(url, 'text/css')

    def add_javascript(self, text):
        self.add_resource(text, 'application/javascript')

    def add_javascript_url(self, url):
        self.add_resource_url(url, 'application/javascript')

    def add_frag_resources(self, frag):
        """Add all the resources from `frag` to my resources."""
        self.resources.extend(frag.resources)

    def add_frags_resources(self, frags):
        for w in frags:
            self.add_frag_resources(w)

    def cache_for(self, seconds):
        self.cache_seconds = seconds

    def initialize_js(self, js_func, runtime_version=1):
        """Register a Javascript function to initialize the frag's browser code."""
        self.js_init = (js_func, runtime_version)

    # Implementation methods: don't override
    # TODO: [rocha] should this go in the runtime?

    def body_html(self):
        """Get the body HTML for this Fragment.

        Returns a Unicode string.

        """
        return self.content

    def head_html(self):
        """Get the head HTML for this Fragment.

        Returns a Unicode string.

        """
        # The list of head fragments
        hh = []
        # The set of all data we've already seen, so no dups.
        seen = set()

        # TODO: [rocha] aggregate and wrap css and javascript.
        # - non url js could be wrapped in an anonymous function
        # - non url css could be rewritten to match the wrapper tag

        for kind, data, mimetype in self.resources:
            # De-dup the data.
            if data in seen:
                continue
            seen.add(data)
            # Different things get different tags.
            if mimetype == "text/css":
                if kind == "text":
                    hh.append(u"<style type='text/css'>\n%s\n</style>" % data)
                elif kind == "url":
                    hh.append(u"<link rel='stylesheet' href='%s' type='text/css'>" % data)
            elif mimetype == "application/javascript":
                if kind == "text":
                    hh.append(u"<script>\n%s\n</script>" % data)
                elif kind == "url":
                    hh.append(u"<script src='%s' type='application/javascript'></script>" % data)
            else:
                raise Exception("Never heard of mimetype %r" % mimetype)

        return u"\n".join(hh)
