"""An XBlock that produces a view from static content."""

from pkg_resources import resource_string

from webob import Response

from .core import XBlockMetaclass, XBlock
from .util import call_once_property
from .fragment import Fragment


class StaticXBlockMetaclass(XBlockMetaclass):
    def __new__(cls, name, bases, attrs):
        if 'content' in attrs and 'view_names' in attrs and attrs['view_names']:
            @call_once_property
            def _content(self):
                return resource_string(self.__class__.__module__, 'content/' + attrs['content'])

            attrs['_content'] = _content

            def view(self, context):
                frag = Fragment(self._content)

                for url, mime_type in attrs.get('urls', []):
                    frag.add_resource_url(self.runtime.handler_url('static') + '/' + url, mime_type)

                if hasattr(self, 'initialize_js'):
                    frag.initialize_js(self.initialize_js)

                return frag

            for view_name in attrs['view_names']:
                view = XBlock.view(view_name)(view)

            attrs['_view'] = view

        attrs['_mime_types_map'] = dict(attrs.get('urls', []))

        @XBlock.handler('static')
        def static_handler(self, request):
            path = request.path_info[1:]
            mime_type = self._mime_types_map[path]
            return Response(body=resource_string(self.__class__.__module__, 'content/' + path), content_type=mime_type)

        attrs['static_handler'] = static_handler

        return super(StaticXBlockMetaclass, cls).__new__(cls, name, bases, attrs)


class StaticXBlock(XBlock):
    __metaclass__ = StaticXBlockMetaclass
