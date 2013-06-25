"""
Machinery to make the common case easy when building new runtimes
"""

import re

from collections import namedtuple, MutableMapping
from .core import ModelType, BlockScope, Scope


class InvalidScopeError(Exception):
    """
    Raised to indicated that operating on the supplied scope isn't allowed by a KeyValueStore
    """
    pass


class KeyValueStore(object):
    """The abstract interface for Key Value Stores."""

    # Keys are structured to retain information about the scope of the data.
    # Stores can use this information however they like to store and retrieve
    # data.
    Key = namedtuple("Key", "scope, student_id, block_scope_id, field_name")

    def get(self, key):
        pass

    def set(self, key, value):
        pass

    def delete(self, key):
        pass

    def has(self, key):
        pass

    def update(self, update_dict):
        pass


class DbModel(MutableMapping):
    """A dictionary-like interface to the fields on a block."""

    def __init__(self, kvs, block_cls, student_id, usage):
        self._kvs = kvs
        self._student_id = student_id
        self._block_cls = block_cls
        self._usage = usage

    def __repr__(self):
        return "<{0.__class__.__name__} {0._block_cls!r}>".format(self)

    def _getfield(self, name):
        # First, get the field from the class, if defined
        block_field = getattr(self._block_cls, name, None)
        if block_field is not None and isinstance(block_field, ModelType):
            return block_field

        # If the class doesn't have the field, and it also doesn't have any
        # namespaces, then the name isn't a field so KeyError
        if not hasattr(self._block_cls, 'namespaces'):
            raise KeyError(name)

        # Resolve the field name in the first namespace where it's available.
        for namespace_name in self._block_cls.namespaces:
            namespace = getattr(self._block_cls, namespace_name)
            namespace_field = getattr(type(namespace), name, None)
            if namespace_field is not None and isinstance(namespace_field, ModelType):
                return namespace_field

        # Not in the class or in any of the namespaces, so name
        # really doesn't name a field
        raise KeyError(name)

    def _key(self, name):
        field = self._getfield(name)
        if field.scope in (Scope.children, Scope.parent):
            block_id = self._usage.id
            student_id = None
        else:
            block = field.scope.block

            if block == BlockScope.ALL:
                block_id = None
            elif block == BlockScope.USAGE:
                block_id = self._usage.id
            elif block == BlockScope.DEFINITION:
                block_id = self._usage.def_id
            elif block == BlockScope.TYPE:
                block_id = self._block_cls.__name__

            if field.scope.user:
                student_id = self._student_id
            else:
                student_id = None

        key = KeyValueStore.Key(
            scope=field.scope,
            student_id=student_id,
            block_scope_id=block_id,
            field_name=name
        )
        return key

    def __getitem__(self, name):
        return self._kvs.get(self._key(name))

    def __setitem__(self, name, value):
        self._kvs.set(self._key(name), value)

    def __delitem__(self, name):
        self._kvs.delete(self._key(name))

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.keys())

    def __contains__(self, name):
        try:
            return self._kvs.has(self._key(name))
        except KeyError:
            return False

    def keys(self):
        fields = [field.name for field in self._block_cls.fields]
        for namespace_name in self._block_cls.namespaces:
            fields.extend(field.name for field in getattr(self._block_cls, namespace_name).fields)
        return fields

    def update(self, *args, **kwargs):
        """
        Update the underlying model with the correct values
        """
        updated_dict = {}
        other_dict = {}
        # combine all the arguments into a single dict
        if args:
            other_dict = args[0]
        for key in kwargs:
            other_dict[key] = kwargs[key]

        # generate a new dict with the correct mappings
        for (key, value) in other_dict.items():
            updated_dict[self._key(key)] = value

        self._kvs.update(updated_dict)


class Runtime(object):
    """Access to the runtime environment for XBlocks.

    A pre-configured instance of this class will be available to XBlocks as
    `self.runtime`.

    """
    def __init__(self):
        self._view_name = None

    def render(self, block, context, view_name):
        """Render a block by invoking its view.

        Finds the view named `view_name` on `block`.  The default view will be
        used if a specific view hasn't be registered.  If there is no default
        view, an exception will be raised.

        The view is invoked, passing it `context`.  The value returned by the
        view is returned, with possible modifications by the runtime to
        integrate it into a larger whole.

        """
        raise NotImplementedError("Runtime needs to provide render()")

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

    def wrap_child(self, block, frag, context):
        return frag

    def handle(self, block, handler_name, data):
        handler = getattr(block, handler_name, None)
        if handler:
            return handler(data)
        handler = getattr(block, "fallback_handler", None)
        if handler:
            return handler(handler_name, data)
        raise Exception("Couldn't find handler %r for %r" % (handler_name, block))

    def handler_url(self, url):
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
            pass
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


class RegexLexer(object):
    """Split text into lexical tokens based on regexes."""
    def __init__(self, *toks):
        parts = []
        for name, regex in toks:
            parts.append("(?P<%s>%s)" % (name, regex))
        self.regex = re.compile("|".join(parts))

    def lex(self, text):
        for match in self.regex.finditer(text):
            name = match.lastgroup
            yield (name, match.group(name))
