"""Implementation of the XBlock facility.

This code is in the Runtime layer, because it is authored once by edX
and used by all runtimes.

"""
import functools
try:
    import simplesjson as json  # pylint: disable=F0401
except ImportError:
    import json
from webob import Response

from xblock.exceptions import XBlockSaveError, KeyValueMultiSaveError
from xblock.fields import ChildrenModelMetaclass, ModelMetaclass, String, List, Scope
from xblock.plugin import Plugin


class TagCombiningMetaclass(type):
    """
    Collects and combines `._class_tags` from all base classes and
    puts them together in one `.class_tags` attribute.
    """
    def __new__(mcs, name, bases, attrs):
        # Allow this method to access the `_class_tags`
        # pylint: disable=W0212
        class_tags = set([])
        # Collect the tags from all base classes.
        for base in bases:
            try:
                class_tags.update(base._class_tags)
            except AttributeError:
                # Base classes may have no ._class_tags, that's ok.
                pass
        attrs['_class_tags'] = class_tags
        return super(TagCombiningMetaclass, mcs).__new__(mcs, name, bases, attrs)


class XBlockMetaclass(
        ChildrenModelMetaclass,
        ModelMetaclass,
        TagCombiningMetaclass,
):
    """
    Metaclass that combines the three base XBlock metaclasses:
    * `ChildrenModelMetaclass`
    * `ModelMetaclass`
    * `TagCombiningMetaclass`
    """
    pass


# -- Base Block


class XBlock(Plugin):
    """Base class for XBlocks.

    Derive from this class to create a new kind of XBlock.  There are no
    required methods, but you will probably need at least one view.

    Don't provide the ``__init__`` method when deriving from this class.

    """

    __metaclass__ = XBlockMetaclass

    entry_point = 'xblock.v1'

    parent = String(help='The id of the parent of this XBlock', default=None, scope=Scope.parent)
    name = String(help="Short name for the block", scope=Scope.settings)
    tags = List(help="Tags for this block", scope=Scope.settings)

    _class_tags = set()

    @classmethod
    def json_handler(cls, func):
        """Wrap a handler to consume and produce JSON.

        Rather than a Request object, the method will now be passed the
        JSON-decoded body of the request.  Any data returned by the function
        will be JSON-encoded and returned as the response.

        """
        @XBlock.handler
        @functools.wraps(func)
        def wrapper(self, request, suffix=''):
            """The wrapper function `json_handler` returns."""
            request_json = json.loads(request.body)
            response_json = json.dumps(func(self, request_json, suffix))
            return Response(response_json, content_type='application/json')
        return wrapper

    @classmethod
    def handler(cls, func):
        """A decorator to indicate a function is usable as a handler."""
        func._is_xblock_handler = True      # pylint: disable=protected-access
        return func

    @classmethod
    def tag(cls, tags):
        """Returns a function that adds the words in `tags` as class tags to this class."""
        def dec(cls):
            """Add the words in `tags` as class tags to this class."""
            # Add in this class's tags
            cls._class_tags.update(tags.replace(",", " ").split())
            return cls
        return dec

    @classmethod
    def load_tagged_classes(cls, tag):
        """Produce a sequence of all XBlock classes tagged with `tag`."""
        # Allow this method to access the `_class_tags`
        # pylint: disable=W0212
        for name, class_ in cls.load_classes():
            if tag in class_._class_tags:
                yield name, class_

    def __init__(self, runtime, field_data, scope_ids):
        """
        :param runtime: Use it to access the environment.
            It is available in XBlock code as ``self.runtime``.
        :type runtime: :class:`xblock.core.Runtime`.

        :param field_data: Interface used by the XBlock fields to access their data
            from wherever it is persisted
        :type field_data: :class:`xblock.field_data.FieldData`

        :param scope_ids: Identifiers needed to resolve scopes
        :type scope_ids: `~xblock.fields.ScopeIds`.
        """
        self.runtime = runtime
        self._field_data = field_data
        self._field_data_cache = {}
        self._dirty_fields = {}
        self.scope_ids = scope_ids

    def __repr__(self):
        # `XBlock` obtains the `fields` attribute from the `ModelMetaclass`.
        # Since this is not understood by static analysis, silence this error.
        # pylint: disable=E1101
        attrs = []
        for field in self.fields.values():
            try:
                value = getattr(self, field.name)
            except Exception:  # pylint: disable=W0703
                # Ensure we return a string, even if unanticipated exceptions.
                attrs.append(" %s=???" % (field.name,))
            else:
                if isinstance(value, basestring):
                    value = value.strip()
                    if len(value) > 40:
                        value = value[:37] + "..."
                attrs.append(" %s=%r" % (field.name, value))
        return "<%s @%04X%s>" % (
            self.__class__.__name__,
            id(self) % 0xFFFF,
            ','.join(attrs)
        )

    def render(self, view, context=None):
        """Render `view` with this block's :class:`Runtime` and the supplied `context`"""
        return self.runtime.render(self, view, context)

    def handle(self, handler_name, request, suffix=''):
        """Handle `request` with this block's :class:`Runtime`"""
        return self.runtime.handle(self, handler_name, request, suffix)

    def save(self):
        """Save all dirty fields attached to this XBlock."""
        if not self._dirty_fields:
            # nop if _dirty_fields attribute is empty
            return
        try:
            fields_to_save = self._get_fields_to_save()
            # Throws KeyValueMultiSaveError if things go wrong
            self._field_data.set_many(self, fields_to_save)

        except KeyValueMultiSaveError as save_error:
            saved_fields = [field for field in self._dirty_fields if field.name in save_error.saved_field_names]
            for field in saved_fields:
                # should only find one corresponding field
                del self._dirty_fields[field]
            raise XBlockSaveError(saved_fields, self._dirty_fields.keys())

        # Remove all dirty fields, since the save was successful
        self._clear_dirty_fields()

    def _get_fields_to_save(self):
        """
        Create dictionary mapping between dirty fields and data cache values.
        A `field` is an instance of `Field`.
        """
        fields_to_save = {}
        for field in self._dirty_fields.keys():
            # If the field value isn't the same as the baseline we recorded
            # when it was read, then save it
            if field._is_dirty(self):
                fields_to_save[field.name] = field.to_json(self._field_data_cache[field.name])
        return fields_to_save

    def _clear_dirty_fields(self):
        """
        Remove all dirty fields from an XBlock
        """
        self._dirty_fields.clear()

    @classmethod
    def parse_xml(cls, node, runtime, keys):
        """
        Use `node` to construct a new block.
        """
        block = runtime.construct_xblock_from_class(cls, keys)

        # The base implementation: child nodes become child blocks.
        for child in node:
            block.runtime.add_node_as_child(block, child)

        # Attributes become fields.
        for name, value in node.items():
            if name in block.fields:
                setattr(block, name, value)

        # Text content becomes "content", if such a field exists.
        if "content" in block.fields and block.fields["content"].scope == Scope.content:
            text = node.text
            if text:
                text = text.strip()
                if text:
                    block.content = text

        return block

    def export_xml(self, node):
        """
        For exporting, set data on `node` from ourselves.
        """
        # pylint: disable=E1101
        # Set node.tag based on our class name.
        node.tag = self.xml_element_name()

        # Set node attributes based on our fields.
        for field_name, field in self.fields.items():
            if field_name in ('children', 'parent', 'content'):
                continue
            if field.is_set_on(self):
                node.set(field_name, unicode(field.read_from(self)))

        # Add children for each of our children.
        if self.has_children:
            for child_id in self.children:
                child = self.runtime.get_block(child_id)
                self.runtime.add_block_as_child_node(child, node)

        # A content field becomes text content.
        text = self.xml_text_content()
        if text is not None:
            node.text = text

    def xml_element_name(self):
        """What XML element name should be used for this block?"""
        return self.scope_ids.block_type

    def xml_text_content(self):
        """What is the text content for this block's XML node?"""
        # pylint: disable=E1101
        if 'content' in self.fields and self.content:
            return self.content
        else:
            return None
