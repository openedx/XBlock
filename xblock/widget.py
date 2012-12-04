"""Widgets for XBlocks."""

class Widget(object):
    def __init__(self, content=None, mimetype='text/html'):
        self.content = ""
        self.mimetype = None
        self.resources = []
        self.cache_seconds = 0
        self.js_init = None
        if content is not None:
            self.add_content(content, mimetype)

    def add_content(self, content, mimetype='text/html'):
        if self.mimetype is not None:
            if mimetype != self.mimetype:
                raise Exception("Can't switch mimetypes midstream: %r -> %r" % (self.mimetype, mimetype))
        else:
            self.mimetype = mimetype
        self.content += content

    def add_resource(self, bytes, mimetype):
        self.resources.append(('text', bytes, mimetype))

    def add_css(self, bytes):
        self.add_resource(bytes, 'text/css')

    def add_css_url(self, url):
        self.add_resource_url(url, 'text/css')

    def add_javascript(self, bytes):
        self.add_resource(bytes, 'application/javascript')

    def add_javascript_url(self, url):
        self.add_resource_url(url, 'application/javascript')

    def add_resource_url(self, url, mimetype):
        self.resources.append(('url', url, mimetype))

    def add_widget_resources(self, widget):
        """Add all the resources from `widget` to my resources."""
        self.resources.extend(widget.resources)

    def add_widgets_resources(self, widgets):
        for w in widgets:
            self.add_widget_resources(w)

    def cache_for(self, seconds):
        self.cache_seconds = seconds

    def initialize_js(self, js_func, runtime_version=1):
        """Register a Javascript function to initialize the Widget's browser code."""
        self.js_init = (js_func, runtime_version)

    # Implementation methods: don't override
    # TODO: [rocha] should this go in the runtime?

    def html(self):
        if self.mimetype == 'text/html':
            return self.content

        return "[[No HTML from %s]]" % self.content_type

    def head_html(self):
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
                    hh.append("<style type='text/css'>\n%s\n</style>" % data)
                elif kind == "url":
                    hh.append("<link rel='stylesheet' href='%s' type='text/css'>" % data)
            elif mimetype == "application/javascript":
                if kind == "text":
                    hh.append("<script>\n%s\n</script>" % data)
                elif kind == "url":
                    hh.append("<script src='%s' type='application/javascript'></script>" % data)
            else:
                raise Exception("Never heard of mimetype %r" % mimetype)

        return "\n".join(hh)
