"""
Machinery to make the common case easy when building new runtimes
"""

import functools
import new
import re

from collections import namedtuple, MutableMapping
from .core import ModelType, BlockScope


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
        if field.scope is None:
            block_id = None
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

            if field.scope.student:
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

    def __contains__(self, item):
        return item in self.keys()

    def keys(self):
        fields = [field.name for field in self._block_cls.fields]
        for namespace_name in self._block_cls.namespaces:
            fields.extend(field.name for field in getattr(self._block_cls, namespace_name).fields)
        return fields


class Runtime(object):
    """Methods all runtimes need."""
    def __init__(self):
        self._view_name = None

    def find_xblock_method(self, block, registration_type, name):
        # TODO: Maybe this should be a method on XBlock?
        first_arg = None
        try:
            fn = block.registered_methods[registration_type + name]
        except KeyError:
            try:
                fn = block.registered_methods[registration_type + "_fallback"]
                first_arg = name
            except KeyError:
                return None

        fn = new.instancemethod(fn, block, block.__class__)
        if first_arg:
            fn = functools.partial(fn, first_arg)
        return fn

    def render(self, block, context, view_name):
        raise NotImplementedError("Runtime needs to provide render()")

    def get_block(self, block_id):
        raise NotImplementedError("Runtime needs to provide get_block()")

    def render_child(self, child, context, view_name=None):
        return child.runtime.render(child, context, view_name or self._view_name)

    def render_children(self, block, context, view_name=None):
        """Render all the children, returning a list of results."""
        results = []
        for child_id in block.children:
            child = self.get_block(child_id)
            result = self.render_child(child, context, view_name)
            results.append(result)
        return results

    def wrap_child(self, block, frag, context):
        return frag

    def handle(self, block, handler_name, data):
        return self.find_xblock_method(block, 'handler', handler_name)(data)

    def query(self, block):
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
                raise BadPath("Invalid thing: %" % toktext)
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
