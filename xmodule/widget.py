"""Widgets for XModules."""

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

    def add_javascript(self, bytes):
        self.add_resource(bytes, 'application/javascript')

    def add_resource_url(self, url, mimetype):
        self.resources.append(('url', url, mimetype))

    def add_widget_resources(self, widget):
        """Add all the resources from `widget` to my resources."""

    def cache_for(self, seconds):
        self.cache_seconds = seconds

    def js_initialize(self, js_func):
        self.js_init = js_func

    def html(self):
        if self.mimetype == 'text/html':
            return self.content
    
        return "[[No HTML from %s]]" % self.content_type
