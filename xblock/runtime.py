"""
Machinery to make the common case easy when building new runtimes
"""

import functools
import gettext
import re
import threading

from abc import ABCMeta, abstractmethod
from lxml import etree
from cStringIO import StringIO

from collections import namedtuple
from xblock.fields import Field, BlockScope, Scope, ScopeIds, UserScope
from xblock.field_data import FieldData
from xblock.exceptions import (
    NoSuchViewError, NoSuchHandlerError, XBlockNotFoundError,
    NoSuchServiceError,
)
from xblock.core import XBlock


class KeyValueStore(object):
    """The abstract interface for Key Value Stores."""

    __metaclass__ = ABCMeta

    # Keys are structured to retain information about the scope of the data.
    # Stores can use this information however they like to store and retrieve
    # data.
    Key = namedtuple("Key", "scope, user_id, block_scope_id, field_name")

    @abstractmethod
    def get(self, key):
        """Reads the value of the given `key` from storage."""
        pass

    @abstractmethod
    def set(self, key, value):
        """Sets `key` equal to `value` in storage."""
        pass

    @abstractmethod
    def delete(self, key):
        """Deletes `key` from storage."""
        pass

    @abstractmethod
    def has(self, key):
        """Returns whether or not `key` is present in storage."""
        pass

    def default(self, key):
        """
        Returns the context relevant default of the given `key`
        or raise KeyError which will result in the field's global default.
        """
        raise KeyError(repr(key))

    def set_many(self, update_dict):
        """
        For each (`key, value`) in `update_dict`, set `key` to `value` in storage.

        The default implementation brute force updates field by field through set which may be inefficient
        for any runtimes doing persistence operations on each set. Such implementations will want to
        override this method.

        :update_dict: field_name, field_value pairs for all cached changes
        """
        for key, value in update_dict.iteritems():
            self.set(key, value)


class DbModel(FieldData):
    """
    An interface mapping value access that uses field names to one
    that uses the correct scoped keys for the underlying KeyValueStore
    """

    def __init__(self, kvs):
        self._kvs = kvs

    def __repr__(self):
        return "<{0.__class__.__name__} {0._kvs!r}>".format(self)

    def _getfield(self, block, name):
        """
        Return the field with the given `name` from `block`.
        If no field with `name` exists in any namespace, raises a KeyError.

        :param block: xblock to retrieve the field from
        :type block: :class:`~xblock.core.XBlock`
        :param name: name of the field to retrieve
        :type name: str
        :raises KeyError: when no field with `name` exists in any namespace
        """

        # First, get the field from the class, if defined
        block_field = getattr(block.__class__, name, None)
        if block_field is not None and isinstance(block_field, Field):
            return block_field

        # Not in the class, so name
        # really doesn't name a field
        raise KeyError(name)

    def _key(self, block, name):
        """
        Resolves `name` to a key, in the following form:

        KeyValueStore.Key(
            scope=field.scope,
            user_id=student_id,
            block_scope_id=block_id,
            field_name=name
        )
        """
        field = self._getfield(block, name)
        if field.scope in (Scope.children, Scope.parent):
            block_id = block.scope_ids.usage_id
            user_id = None
        else:
            block_scope = field.scope.block

            if block_scope == BlockScope.ALL:
                block_id = None
            elif block_scope == BlockScope.USAGE:
                block_id = block.scope_ids.usage_id
            elif block_scope == BlockScope.DEFINITION:
                block_id = block.scope_ids.def_id
            elif block_scope == BlockScope.TYPE:
                block_id = block.scope_ids.block_type

            if field.scope.user == UserScope.ONE:
                user_id = block.scope_ids.user_id
            else:
                user_id = None

        key = KeyValueStore.Key(
            scope=field.scope,
            user_id=user_id,
            block_scope_id=block_id,
            field_name=name
        )
        return key

    def get(self, block, name):
        """
        Retrieve the value for the field named `name`.

        If a value is provided for `default`, then it will be
        returned if no value is set
        """
        return self._kvs.get(self._key(block, name))

    def set(self, block, name, value):
        """
        Set the value of the field named `name`
        """
        self._kvs.set(self._key(block, name), value)

    def delete(self, block, name):
        """
        Reset the value of the field named `name` to the default
        """
        self._kvs.delete(self._key(block, name))

    def has(self, block, name):
        """
        Return whether or not the field named `name` has a non-default value
        """
        try:
            return self._kvs.has(self._key(block, name))
        except KeyError:
            return False

    def set_many(self, block, update_dict):
        """Update the underlying model with the correct values."""
        updated_dict = {}

        # Generate a new dict with the correct mappings.
        for (key, value) in update_dict.items():
            updated_dict[self._key(block, key)] = value

        self._kvs.set_many(updated_dict)

    def default(self, block, name):
        """
        Ask the kvs for the default (default implementation which other classes may override).

        :param block: block containing field to default
        :type block: :class:`~xblock.core.XBlock`
        :param name: name of the field to default
        """
        return self._kvs.default(self._key(block, name))


class UsageStore(object):
    """An abstract object that stores usages and definitions."""
    __metaclass__ = ABCMeta

    @abstractmethod
    def create_usage(self, def_id):
        """Make a usage, storing its definition id.

        Returns the newly-created usage id.

        """
        pass

    @abstractmethod
    def get_definition_id(self, usage_id):
        """Get a usage.

        Returns the definition id stored as the usage.

        """
        pass

    @abstractmethod
    def create_definition(self, block_type):
        """Make a definition, storing its block type.

        Returns the newly-created definition id.

        """
        pass

    @abstractmethod
    def get_block_type(self, def_id):
        """Get a definition.

        Returns the block_type stored as the definition.

        """
        pass


class Runtime(object):
    """
    Access to the runtime environment for XBlocks.
    """

    __metaclass__ = ABCMeta

    # Abstract methods

    @abstractmethod
    def get_block(self, usage_id):
        """Get a block by usage id.

        Returns the block identified by `usage_id`, or raises an exception.
        """
        raise XBlockNotFoundError(usage_id)

    @abstractmethod
    def handler_url(self, block, handler_name, suffix='', query='', thirdparty=False):
        """Get the actual URL to invoke a handler.

        `handler_name` is the name of your handler function. Any additional
        portion of the url will be passed as the `suffix` argument to the handler.

        The return value is a complete absolute URL that will route through the
        runtime to your handler.

        :param block: The block to generate the url for
        :param handler_name: The handler on that block that the url should resolve to
        :param suffix: Any path suffix that should be added to the handler url
        :param query: Any query string that should be added to the handler url
            (which should not include an initial ? or &)
        :param thirdparty: If true, create a URL that can be used without the
            user being logged in.  This is useful for URLs to be used by third-party
            services.
        """
        raise NotImplementedError("Runtime needs to provide handler_url()")

    @abstractmethod
    def resources_url(self, resource):
        """Get the URL for a static resorce file.

        `resource` is the application local path to the resource.

        The return value is a complete absolute URL that will locate the
        resource on your runtime.

        """
        raise NotImplementedError("Runtime needs to provide resources_url()")

    @abstractmethod
    def local_resource_url(self, block, uri):
        """Get the URL to load a static resource from an XBlock.

        `block` is the XBlock that owns the resource.

        `uri` is a relative URI to the resource. The XBlock class's
             get_local_resource(uri) method should be able to open the resource
             identified by this uri.

        The return value is a complete absolute URL which will locate the
        resource on your runtime.
        """
        raise NotImplementedError("Runtime needs to provide resources_url()")

    # Construction

    def __init__(self, usage_store, field_data, mixins=(), services=None):
        """
        Arguments:
            mixins (tuple of classes): Classes that should be mixed in with
                every :class:`~xblock.core.XBlock` created by this `Runtime`.
            services (dictionary): Services to make available through the
                :meth:`service` method.  There's no point passing anything here
                if you are overriding :meth:`service` in your sub-class.

        """
        self._view_name = None
        self.mixologist = Mixologist(mixins)
        self.usage_store = usage_store
        self.field_data = field_data
        self._services = services or {}

        # Provide some default implementations
        self._services.setdefault("i18n", gettext.NullTranslations())

    # Block operations

    def construct_xblock(self, block_type, scope_ids, field_data=None, default_class=None, *args, **kwargs):
        r"""
        Construct a new xblock of the type identified by block_type,
        passing \*args and \*\*kwargs into `__init__`.
        """
        block_class = XBlock.load_class(block_type, default_class)
        return self.construct_xblock_from_class(
            cls=block_class,
            scope_ids=scope_ids,
            field_data=field_data,
            *args, **kwargs
        )

    def construct_xblock_from_class(self, cls, scope_ids, field_data=None, *args, **kwargs):
        """
        Construct a new xblock of type cls, mixing in the mixins
        defined for this application
        """
        return self.mixologist.mix(cls)(
            runtime=self,
            field_data=field_data or self.field_data,
            scope_ids=scope_ids,
            *args, **kwargs
        )

    # Parsing XML

    def parse_xml_string(self, xml):
        """Parse a string of XML, returning a usage id."""
        return self.parse_xml_file(StringIO(xml))

    def parse_xml_file(self, fileobj):
        """Parse an open XML file, returning a usage id."""
        root = etree.parse(fileobj).getroot()
        usage_id = self._usage_id_from_node(root, None)
        return usage_id

    def _usage_id_from_node(self, node, parent_id):
        """Create a new usage id from an XML dom node.

        :param node: The DOM node to interpret.
        :type node: `lxml.etree.Element`
        :param parent_id: The usage ID of the parent block.

        """
        block_type = node.tag
        # TODO: a way for this node to be a usage to an existing definition?
        def_id = self.usage_store.create_definition(block_type)
        usage_id = self.usage_store.create_usage(def_id)
        keys = ScopeIds(UserScope.NONE, block_type, def_id, usage_id)
        block_class = self.mixologist.mix(XBlock.load_class(block_type))
        block = block_class.parse_xml(node, self, keys)
        block.parent = parent_id
        block.save()
        return usage_id

    def add_node_as_child(self, block, node):
        """
        Called by XBlock.parse_xml to treat a child node as a child block.
        """
        usage_id = self._usage_id_from_node(node, block.scope_ids.usage_id)
        block.children.append(usage_id)

    # Exporting XML

    def export_to_xml(self, block, xmlfile):
        """
        Export the block to XML, writing the XML to `xmlfile`.
        """
        root = etree.Element("unknown_root")
        tree = etree.ElementTree(root)
        block.export_xml(root)
        tree.write(xmlfile, xml_declaration=True, encoding="utf8")

    def add_block_as_child_node(self, block, node):
        """
        Export `block` as a child node of `node`.
        """
        child = etree.SubElement(node, "unknown")
        block.export_xml(child)

    # Rendering

    def render(self, block, view_name, context=None):
        """
        Render a block by invoking its view.

        Finds the view named `view_name` on `block`.  The default view will be
        used if a specific view hasn't be registered.  If there is no default
        view, an exception will be raised.

        The view is invoked, passing it `context`.  The value returned by the
        view is returned, with possible modifications by the runtime to
        integrate it into a larger whole.

        """
        # Set the active view so that :function:`render_child` can use it
        # as a default
        old_view_name = self._view_name
        self._view_name = view_name
        try:

            view_fn = getattr(block, view_name, None)
            if view_fn is None:
                view_fn = getattr(block, "fallback_view", None)
                if view_fn is None:
                    raise NoSuchViewError(block, view_name)
                view_fn = functools.partial(view_fn, view_name)

            frag = view_fn(context)

            # Explicitly save because render action may have changed state
            block.save()
            return self.wrap_child(block, view_name, frag, context)
        finally:
            # Reset the active view to what it was before entering this method
            self._view_name = old_view_name

    def render_child(self, child, view_name=None, context=None):
        """A shortcut to render a child block.

        Use this method to render your children from your own view function.

        If `view_name` is not provided, it will default to the view name you're
        being rendered with.

        Returns the same value as :func:`render`.

        """
        return child.render(view_name or self._view_name, context)

    def render_children(self, block, view_name=None, context=None):
        """Render a block's children, returning a list of results.

        Each child of `block` will be rendered, just as :func:`render_child` does.

        Returns a list of values, each as provided by :func:`render`.

        """
        results = []
        for child_id in block.children:
            child = self.get_block(child_id)
            result = self.render_child(child, view_name, context)
            results.append(result)
        return results

    def wrap_child(self, block, view, frag, context):  # pylint: disable=W0613
        """
        Wraps the fragment with any necessary HTML, informed by
        the block, view being rendered, and the context. This default implementation
        simply returns the fragment.
        """
        # By default, just return the fragment itself.
        return frag

    # Handlers

    def handle(self, block, handler_name, request, suffix=''):
        """
        Handles any calls to the specified `handler_name`.

        Provides a fallback handler if the specified handler isn't found.

        :param handler_name: The name of the handler to call
        :param request: The request to handle
        :type request: webob.Request
        :param suffix: The remainder of the url, after the handler url prefix, if available
        """
        handler = getattr(block, handler_name, None)
        if handler and getattr(handler, '_is_xblock_handler', False):
            # Cache results of the handler call for later saving
            results = handler(request, suffix)
        else:
            fallback_handler = getattr(block, "fallback_handler", None)
            if fallback_handler and getattr(fallback_handler, '_is_xblock_handler', False):
                # Cache results of the handler call for later saving
                results = fallback_handler(handler_name, request, suffix)
            else:
                raise NoSuchHandlerError("Couldn't find handler %r for %r" % (handler_name, block))

        # Write out dirty fields
        block.save()
        return results

    # Services

    def service(self, block, service_name):
        """Return a service, or None.

        Services are objects implementing arbitrary other interfaces.  They are
        requested by agreed-upon names, see [XXX TODO] for a list of possible
        services.  The object returned depends on the service requested.

        XBlocks must announce their intention to request services with the
        `XBlock.needs` or `XBlock.wants` decorators.  Use `needs` if you assume
        that the service is available, or `wants` if your code is flexible and
        can accept a None from this method.

        Runtimes can override this method if they have different techniques for
        finding and delivering services.

        Arguments:
            block (an XBlock): this block's class will be examined for service
                decorators.
            service_name (string): the name of the service requested.

        Returns:
            An object implementing the requested service, or None.

        """
        declaration = block.service_declaration(service_name)
        if declaration is None:
            raise NoSuchServiceError("Service {!r} was not requested.".format(service_name))
        service = self._services.get(service_name)
        if service is None and declaration == "need":
            raise NoSuchServiceError("Service {!r} is not available.".format(service_name))
        return service

    # Querying

    def query(self, block):
        """Query for data in the tree, starting from `block`.

        Returns a Query object with methods for navigating the tree and
        retrieving information.

        """
        raise NotImplementedError("Querying is an experimental feature")

    def querypath(self, block, path):
        """An XPath-like interface to `query`."""
        class BadPath(Exception):
            """Bad path exception thrown when path cannot be found."""
            pass
        results = self.query(block)
        ROOT, SEP, WORD, FINAL = range(4)               # pylint: disable=C0103
        state = ROOT
        lexer = RegexLexer(
            ("dotdot", r"\.\."),
            ("dot", r"\."),
            ("slashslash", r"//"),
            ("slash", r"/"),
            ("atword", r"@\w+"),
            ("word", r"\w+"),
            ("err", r"."),
        )
        for tokname, toktext in lexer.lex(path):
            if state == FINAL:
                # Shouldn't be any tokens after a last token.
                raise BadPath()
            if tokname == "dotdot":
                # .. (parent)
                if state == WORD:
                    raise BadPath()
                results = results.parent()
                state = WORD
            elif tokname == "dot":
                # . (current node)
                if state == WORD:
                    raise BadPath()
                state = WORD
            elif tokname == "slashslash":
                # // (descendants)
                if state == SEP:
                    raise BadPath()
                if state == ROOT:
                    raise NotImplementedError()
                results = results.descendants()
                state = SEP
            elif tokname == "slash":
                # / (here)
                if state == SEP:
                    raise BadPath()
                if state == ROOT:
                    raise NotImplementedError()
                state = SEP
            elif tokname == "atword":
                # @xxx (attribute access)
                if state != SEP:
                    raise BadPath()
                results = results.attr(toktext[1:])
                state = FINAL
            elif tokname == "word":
                # xxx (tag selection)
                if state != SEP:
                    raise BadPath()
                results = results.children().tagged(toktext)
                state = WORD
            else:
                raise BadPath("Invalid thing: %r" % toktext)
        return results


class ObjectAggregator(object):
    """
    Provides a single object interface that combines many smaller objects.

    Attribute access on the aggregate object acts on the first sub-object
    that has that attribute.
    """

    def __init__(self, *objects):
        self.__dict__['_objects'] = objects

    def _object_with_attr(self, name):
        """
        Returns the first object that has the attribute `name`

        :param name: the attribute to filter by
        :type name: `str`
        :raises AttributeError: when no object has the named attribute
        """
        for obj in self._objects:
            if hasattr(obj, name):
                return obj

        raise AttributeError("No object has attribute {!r}".format(name))

    def __getattr__(self, name):
        return getattr(self._object_with_attr(name), name)

    def __setattr__(self, name, value):
        setattr(self._object_with_attr(name), name, value)

    def __delattr__(self, name):
        delattr(self._object_with_attr(name), name)


# Cache of Mixologist generated classes
_CLASS_CACHE = {}
_CLASS_CACHE_LOCK = threading.RLock()


class Mixologist(object):
    """
    Provides a facility to dynamically generate classes with additional mixins.
    """
    def __init__(self, mixins):
        """
        :param mixins: Classes to mixin
        :type mixins: `iterable` of `class`
        """
        self._mixins = tuple(mixins)

    def mix(self, cls):
        """
        Returns a subclass of `cls` mixed with `self.mixins`.

        :param cls: The base class to mix into
        :type cls: `class`
        """

        if hasattr(cls, 'unmixed_class'):
            base_class = cls.unmixed_class
            old_mixins = cls.__bases__[1:]  # Skip the original unmixed class
            mixins = old_mixins + tuple(
                mixin
                for mixin in self._mixins
                if mixin not in old_mixins
            )
        else:
            base_class = cls
            mixins = self._mixins

        mixin_key = (base_class, mixins)

        if mixin_key not in _CLASS_CACHE:
            # Only lock if we're about to make a new class
            with _CLASS_CACHE_LOCK:
                # Use setdefault so that if someone else has already
                # created a class before we got the lock, we don't
                # overwrite it
                return _CLASS_CACHE.setdefault(mixin_key, type(
                    base_class.__name__ + 'WithMixins',
                    (base_class, ) + mixins,
                    {'unmixed_class': base_class}
                ))
        else:
            return _CLASS_CACHE[mixin_key]


class RegexLexer(object):
    """Split text into lexical tokens based on regexes."""
    def __init__(self, *toks):
        parts = []
        for name, regex in toks:
            parts.append("(?P<%s>%s)" % (name, regex))
        self.regex = re.compile("|".join(parts))

    def lex(self, text):
        """Iterator that tokenizes `text` and yields up tokens as they are found"""
        for match in self.regex.finditer(text):
            name = match.lastgroup
            yield (name, match.group(name))
