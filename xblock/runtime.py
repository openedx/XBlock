"""
Machinery to make the common case easy when building new runtimes
"""

import re
import functools

from collections import namedtuple
from xblock.fields import Field, BlockScope, Scope, FieldData, UNSET, UserScope
from xblock.exceptions import NoSuchViewError, NoSuchHandlerError
from xblock.core import XBlock


class KeyValueStore(object):
    """The abstract interface for Key Value Stores."""

    # Keys are structured to retain information about the scope of the data.
    # Stores can use this information however they like to store and retrieve
    # data.
    Key = namedtuple("Key", "scope, student_id, block_scope_id, field_name")

    def get(self, key):
        """Abstract get method. Implementations should return the value of the given `key`."""
        pass

    def set(self, key, value):
        """Abstract set method. Implementations should set `key` equal to `value`."""
        pass

    def delete(self, key):
        """Abstract delete method. Implementations should remove the `key`."""
        pass

    def has(self, key):
        """Abstract has method. Implementations should return Boolean, whether or not `key` is present."""
        pass

    def default(self, key):
        """
        Abstract default method. Implementations should return the context relevant default of the given `key`
        or raise KeyError which will result in the field's global default.
        """
        raise KeyError(repr(key))

    def set_many(self, update_dict):
        """
        Bulk update of the kvs.
        This implementation brute force updates field by field through set which may be inefficient
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
            student_id=student_id,
            block_scope_id=block_id,
            field_name=name
        )
        """
        field = self._getfield(block, name)
        if field.scope in (Scope.children, Scope.parent):
            block_id = block.scope_ids.usage_id
            student_id = None
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
                student_id = block.scope_ids.student_id
            else:
                student_id = None

        key = KeyValueStore.Key(
            scope=field.scope,
            student_id=student_id,
            block_scope_id=block_id,
            field_name=name
        )
        return key

    def get(self, block, name, default=UNSET):
        """
        Retrieve the value for the field named `name`.

        If a value is provided for `default`, then it will be
        returned if no value is set
        """
        try:
            return self._kvs.get(self._key(block, name))
        except KeyError:
            if default is UNSET:
                raise
            else:
                return default

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


class Runtime(object):
    """
    Access to the runtime environment for XBlocks.
    """

    def __init__(self, mixins=()):
        """
        :param mixins: Classes that should be mixed in with every :class:`~xblock.core.XBlock`
            created by this `Runtime`
        :type mixins: `tuple` of `class`es
        """
        self._view_name = None
        self.mixologist = Mixologist(mixins)

    def construct_block(self, plugin_name, field_data, scope_ids, default_class=None, *args, **kwargs):
        """
        Construct a new xblock of the type identified by plugin_name,
        passing *args and **kwargs into __init__
        """
        block_class = XBlock.load_class(plugin_name, default_class)
        return self.construct_block_from_class(cls=block_class, field_data=field_data, scope_ids=scope_ids, *args, **kwargs)

    def construct_block_from_class(self, cls, field_data, scope_ids, *args, **kwargs):
        """
        Construct a new xblock of type cls, mixing in the mixins
        defined for this application
        """
        return self.mixologist.mix(cls)(runtime=self, field_data=field_data, scope_ids=scope_ids, *args, **kwargs)

    def render(self, block, context, view_name):
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
                    raise NoSuchViewError()
                view_fn = functools.partial(view_fn, view_name)

            frag = view_fn(context)

            # Explicitly save because render action may have changed state
            block.save()
            return self.wrap_child(block, frag, context)
        finally:
            # Reset the active view to what it was before entering this method
            self._view_name = old_view_name

    def get_block(self, block_id):
        """Get a block by ID.

        Returns the block identified by `block_id`, or raises an exception.
        """
        raise NotImplementedError("Runtime needs to provide get_block()")

    def render_child(self, child, context, view_name=None):
        """A shortcut to render a child block.

        Use this method to render your children from your own view function.

        If `view_name` is not provided, it will default to the view name you're
        being rendered with.

        Returns the same value as :func:`render`.

        """
        return child.runtime.render(child, context, view_name or self._view_name)

    def render_children(self, block, context, view_name=None):
        """Render a block's children, returning a list of results.

        Each child of `block` will be rendered, just as :func:`render_child` does.

        Returns a list of values, each as provided by :func:`render`.

        """
        results = []
        for child_id in block.children:
            child = self.get_block(child_id)
            result = self.render_child(child, context, view_name)
            results.append(result)
        return results

    def wrap_child(self, block, frag, context):  # pylint: disable=W0613
        """
        Wraps the fragment with any necessary HTML, informed by
        the block and the context. This default implementation
        simply returns the fragment.
        """
        # By default, just return the fragment itself.
        return frag

    def handle(self, block, handler_name, data):
        """
        Handles any calls to the specified `handler_name`.

        Provides a fallback handler if the specified handler isn't found.
        """
        handler = getattr(block, handler_name, None)
        if handler:
            # Cache results of the handler call for later saving
            results = handler(data)
        else:
            fallback_handler = getattr(block, "fallback_handler", None)
            if fallback_handler:
                # Cache results of the handler call for later saving
                results = fallback_handler(handler_name, data)
            else:
                raise NoSuchHandlerError("Couldn't find handler %r for %r" % (handler_name, block))

        # Write out dirty fields
        block.save()
        return results

    def handler_url(self, block, url):
        """Get the actual URL to invoke a handler.

        `url` is the abstract URL to your handler.  It should start with the
        name you used to register your handler.

        The return value is a complete absolute URL that will route through the
        runtime to your handler.

        """
        raise NotImplementedError("Runtime needs to provide handler_url()")

    def query(self, block):
        """Query for data in the tree, starting from `block`.

        Returns a Query object with methods for navigating the tree and
        retrieving information.

        """
        raise NotImplementedError("Runtime needs to provide query()")

    def querypath(self, block, path):
        """An XPath-like interface to `query`."""
        class BadPath(Exception):
            """Bad path exception thrown when path cannot be found."""
            pass
        # pylint: disable=C0103
        q = self.query(block)
        ROOT, SEP, WORD, FINAL = range(4)
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
                q = q.parent()
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
                q = q.descendants()
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
                q = q.attr(toktext[1:])
                state = FINAL
            elif tokname == "word":
                # xxx (tag selection)
                if state != SEP:
                    raise BadPath()
                q = q.children().tagged(toktext)
                state = WORD
            else:
                raise BadPath("Invalid thing: %r" % toktext)
        return q


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
        Generate a list of objects that have the attribute `name`

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
        # Cache of generated classes
        self._generated_classes = {}

    def mix(self, cls):
        """
        Returns a subclass of `cls` mixed with `self.mixins`.

        :param cls: The base class to mix into
        :type cls: `class`
        """

        if cls not in self._generated_classes:
            self._generated_classes[cls] = type(
                cls.__name__ + 'WithMixins',
                (cls, ) + self._mixins,
                {'mixed_class': True}
            )

        return self._generated_classes[cls]


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
