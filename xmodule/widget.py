"""Widgets for XModules."""

class Widget(object):
    def __init__(self):
        self.content = None
        self.content_type = None
        self.resources = []
        self.cache_seconds = 0
        self.js_init = None

    def add_content(self, bytes, mimetype='text/html'):
        assert self.content is None
        self.content = bytes
        self.content_type = mimetype

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

