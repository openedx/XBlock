"""Fragments for XBlocks.

This code is in the Runtime layer.

"""

from collections import namedtuple


FragmentResource = namedtuple("FragmentResource", "kind, data, mimetype, placement")  # pylint: disable=C0103


class Fragment(object):
    """A fragment of a web page, for XBlock views to return.

    A fragment consists of HTML for the body of the page, and a series of
    resources needed by the body. Resources are specified with a MIME type
    (such as "application/javascript" or "text/css") that determines how they
    are inserted into the page.  The resource is provided either as literal
    text, or as a URL.  Text will be included on the page, wrapped
    appropriately for the MIME type.  URLs will be used as-is on the page.

    Resources are only inserted into the page once, even if many Fragments
    in the page ask for them.  Determining duplicates is done by simple text
    matching.

    """
    def __init__(self, content=None):
        #: The html content for this Fragment
        self.content = u""

        self._resources = []
        self.js_init_fn = None
        self.js_init_version = None
        self.json_init_args = None

        if content is not None:
            self.add_content(content)

    @property
    def resources(self):
        r"""
        Returns list of unique `FragmentResource`\s by order of first appearance.
        """
        seen = set()
        # seen.add always returns None, so 'not seen.add(x)' is always True,
        # but will only be called if the value is not already in seen (because
        # 'and' short-circuits)
        return [x for x in self._resources if x not in seen and not seen.add(x)]

    def to_pods(self):
        """
        Returns the data in a dictionary.

        'pods' = Plain Old Data Structure.
        """
        return {
            'content': self.content,
            'resources': [r._asdict() for r in self.resources],  # pylint: disable=W0212
            'js_init_fn': self.js_init_fn,
            'js_init_version': self.js_init_version,
            'json_init_args': self.json_init_args
        }

    @classmethod
    def from_pods(cls, pods):
        """
        Returns a new Fragment from a `pods`.

        `pods` is a Plain Old Data Structure, a Python dictionary with
        keys `content`, `resources`, `js_init_fn`, and `js_init_version`.

        """
        frag = cls()
        frag.content = pods['content']
        frag.resources = [FragmentResource(**d) for d in pods['resources']]
        frag.js_init_fn = pods['js_init_fn']
        frag.js_init_version = pods['js_init_version']
        return frag

    def add_content(self, content):
        """Add content to this fragment.

        `content` is a Unicode string, HTML to append to the body of the
        fragment.  It must not contain a ``<body>`` tag, or otherwise assume
        that it is the only content on the page.

        """
        assert isinstance(content, unicode)
        self.content += content

    def _default_placement(self, mimetype):
        """Decide where a resource will go, if the user didn't say."""
        if mimetype == 'application/javascript':
            return 'foot'
        return 'head'

    def add_resource(self, text, mimetype, placement=None):
        """Add a resource needed by this Fragment.

        Other helpers, such as :func:`add_css` or :func:`add_javascript` are
        more convenient for those common types of resource.

        `text`: the actual text of this resource, as a unicode string.

        `mimetype`: the MIME type of the resource.

        `placement`: where on the page the resource should be placed:

            None: let the Fragment choose based on the MIME type.

            "head": put this resource in the ``<head>`` of the page.

            "foot": put this resource at the end of the ``<body>`` of the
            page.

        """
        if not placement:
            placement = self._default_placement(mimetype)
        res = FragmentResource('text', text, mimetype, placement)
        self._resources.append(res)

    def add_resource_url(self, url, mimetype, placement=None):
        """Add a resource by URL needed by this Fragment.

        Other helpers, such as :func:`add_css_url` or
        :func:`add_javascript_url` are more convenent for those common types of
        resource.

        `url`: the URL to the resource.

        Other parameters are as defined for :func:`add_resource`.

        """
        if not placement:
            placement = self._default_placement(mimetype)
        self._resources.append(FragmentResource('url', url, mimetype, placement))

    def add_css(self, text):
        """Add literal CSS to the Fragment."""
        self.add_resource(text, 'text/css')

    def add_css_url(self, url):
        """Add a CSS URL to the Fragment."""
        self.add_resource_url(url, 'text/css')

    def add_javascript(self, text):
        """Add literal Javascript to the Fragment."""
        self.add_resource(text, 'application/javascript')

    def add_javascript_url(self, url):
        """Add a Javascript URL to the Fragment."""
        self.add_resource_url(url, 'application/javascript')

    def add_frag_resources(self, frag):
        """Add all the resources from `frag` to my resources.

        This is used by an XBlock to collect resources from Fragments produced
        by its children.

        `frag` is a Fragment.

        The content from the Fragment is ignored.  The caller must collect
        together the content into this Fragment's content.

        """
        self._resources.extend(frag.resources)

    def add_frags_resources(self, frags):
        """Add all the resources from `frags` to my resources.

        This is used by an XBlock to collect resources from Fragments produced
        by its children.

        `frags` is a sequence of Fragments.

        The content from the Fragments is ignored.  The caller must collect
        together the content into this Fragment's content.

        """
        for resource in frags:
            self.add_frag_resources(resource)

    def initialize_js(self, js_func, json_args=None):
        """Register a Javascript function to initialize the Javascript resources.

        `js_func` is the name of a Javascript function defined by one of the
        Javascript resources.  As part of setting up the browser's runtime
        environment, the function will be invoked, passing a runtime object
        and a DOM element.

        """
        # This is version 1 of the interface.
        self.js_init_fn = js_func
        self.js_init_version = 1
        if json_args:
            self.json_init_args = json_args

    # Implementation methods: don't override
    # TODO: [rocha] should this go in the runtime?

    def body_html(self):
        """Get the body HTML for this Fragment.

        Returns a Unicode string, the HTML content for the ``<body>`` section
        of the page.

        """
        return self.content

    def head_html(self):
        """Get the head HTML for this Fragment.

        Returns a Unicode string, the HTML content for the ``<head>`` section
        of the page.

        """
        return self.resources_to_html("head")

    def foot_html(self):
        """Get the foot HTML for this Fragment.

        Returns a Unicode string, the HTML content for the end of the
        ``<body>`` section of the page.

        """
        return self.resources_to_html("foot")

    def resources_to_html(self, placement):
        """Get some resource HTML for this Fragment.

        `placement` is "head" or "foot".

        Returns a unicode string, the HTML for the head or foot of the page.

        """
        # TODO: [rocha] aggregate and wrap css and javascript.
        # - non url js could be wrapped in an anonymous function
        # - non url css could be rewritten to match the wrapper tag

        return '\n'.join(
            self.resource_to_html(resource)
            for resource in self.resources
            if resource.placement == placement
        )

    @staticmethod
    def resource_to_html(resource):
        """
        Returns `resource` wrapped in the appropriate html tag for it's mimetype.
        """
        if resource.mimetype == "text/css":
            if resource.kind == "text":
                return u"<style type='text/css'>\n%s\n</style>" % resource.data
            elif resource.kind == "url":
                return u"<link rel='stylesheet' href='%s' type='text/css'>" % resource.data

        elif resource.mimetype == "application/javascript":
            if resource.kind == "text":
                return u"<script>\n%s\n</script>" % resource.data
            elif resource.kind == "url":
                return u"<script src='%s' type='application/javascript'></script>" % resource.data

        elif resource.mimetype == "text/html":
            assert resource.kind == "text"
            return resource.data

        else:
            raise Exception("Never heard of mimetype %r" % resource.mimetype)
