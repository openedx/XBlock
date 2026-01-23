"""
Tools for testing XBlocks
"""
import typing as t

import warnings
from contextlib import contextmanager
from functools import partial

from opaque_keys.edx.keys import CourseKey, DefinitionKey, UsageKey, LearningContextKey
from xblock.runtime import Runtime, MemoryIdManager


class TestContextKey(LearningContextKey):
    """
    A simple context key type for testing XBlock

    When serialized, these keys look like:
        tc:myContext
    """
    CANONICAL_NAMESPACE = 'tc'  # "Test Context"
    KEY_FIELDS = ('slug',)
    slug: str
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    def __init__(self, slug: str):
        super().__init__(slug=slug)

    def _to_string(self) -> str:
        """
        Serialize this key as a string
        """
        return self.slug

    @classmethod
    def _from_string(cls, serialized: str):
        """
        Instantiate this key from a serialized string
        """
        return cls(serialized)


class TestDefinitionKey(DefinitionKey):
    """
    A simple definition key type for testing XBlock

    When serialized, these keys look like:
        td:myType$myId
    """
    CANONICAL_NAMESPACE = 'td'  # "Test Definition"
    KEY_FIELDS = ('block_type', 'block_id')
    block_type: str
    block_id: str
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    def __init__(self, block_type: str, block_id: str):
        super().__init__(block_type=block_type, block_id=block_id)

    def _to_string(self) -> str:
        """
        Serialize this key as a string
        """
        return f"{self.block_type}${self.block_id}"

    @classmethod
    def _from_string(cls, serialized: str):
        """
        Instantiate this key from a serialized string
        """
        (block_type, block_id) = serialized.split('$')
        return cls(block_type, block_id)


class TestUsageKey(UsageKey):
    """
    A simple usage key type for testing XBlock

    When serialized, these keys look like:
        tu:myContext$myType$myId
    """
    CANONICAL_NAMESPACE = 'tu'  # "Test Usage"
    KEY_FIELDS = ('context_key', 'definition_key')
    context_key: TestContextKey
    definition_key: TestDefinitionKey
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    def __init__(self, context_key: TestContextKey, definition_key: TestDefinitionKey):
        super().__init__(context_key=context_key, definition_key=definition_key)

    @property
    def block_type(self) -> str:
        """
        The XBlock type of this usage.
        """
        return self.definition_key.block_type

    @property
    def block_id(self) -> str:
        """
        The name of this usage.
        """
        return self.definition_key.block_id

    @property
    def course_key(self) -> LearningContextKey:
        raise ValueError("Cannot use this key type in the context of courses")

    def map_into_course(self, course_key: CourseKey) -> t.Self:
        raise ValueError("Cannot use this key type in the context of courses")

    def _to_string(self) -> str:
        """
        Serialize this key as a string
        """
        return "$".join((self.context_key.slug, self.block_type, self.block_id))

    @classmethod
    def _from_string(cls, serialized: str) -> t.Self:
        """
        Instantiate this key from a serialized string
        """
        (context_slug, block_type, block_id) = serialized.split('$')
        return cls(
            context_key=TestContextKey(context_slug),
            definition_key=TestDefinitionKey(block_type, block_id),
        )


def blocks_are_equivalent(block1, block2):
    """Compare two blocks for equivalence.
    """
    # The two blocks have to be the same class.
    if block1.__class__ != block2.__class__:
        return False

    # They have to have the same fields.
    if set(block1.fields) != set(block2.fields):
        return False

    # The data fields have to have the same values.
    for field_name in block1.fields:
        if field_name in ('parent', 'children'):
            continue
        if getattr(block1, field_name) != getattr(block2, field_name):
            return False

    # The children need to be equal.
    if block1.has_children != block2.has_children:
        return False

    if block1.has_children:
        if len(block1.children) != len(block2.children):
            return False

        for child_id1, child_id2 in zip(block1.children, block2.children):
            if child_id1 == child_id2:
                # Equal ids mean they must be equal, check the next child.
                continue

            # Load up the actual children to see if they are equal.
            child1 = block1.runtime.get_block(child_id1)
            child2 = block2.runtime.get_block(child_id2)
            if not blocks_are_equivalent(child1, child2):
                return False

    return True


def _unabc(cls, msg="{} isn't implemented"):
    """Helper method to implement `unabc`"""
    def make_dummy_method(ab_name):
        """A function to make the dummy method, to close over ab_name."""
        def dummy_method(self, *args, **kwargs):
            """The method provided for all missing abstract methods."""
            raise NotImplementedError(msg.format(ab_name))
        return dummy_method

    for ab_name in cls.__abstractmethods__:
        print(cls, ab_name)
        setattr(cls, ab_name, make_dummy_method(ab_name))

    cls.__abstractmethods__ = ()
    return cls


def unabc(msg):
    """
    Add dummy methods to a class to satisfy abstract base class constraints.

    Usage::

        @unabc
        class NotAbstract(SomeAbstractClass):
            pass

        @unabc('Fake {}')
        class NotAbstract(SomeAbstractClass):
            pass
    """

    # Handle the possibility that unabc is called without a custom message
    if isinstance(msg, type):
        return _unabc(msg)
    else:
        return partial(_unabc, msg=msg)


class WarningTestMixin:
    """
    Add the ability to assert on warnings raised by a chunk of code.
    """
    @contextmanager
    def assertWarns(self, warning_class):
        """
        Assert that at least one warning of class `warning_class` is
        logged during the surrounded context.
        """
        with warnings.catch_warnings(record=True) as warns:
            warnings.simplefilter("always")
            yield
            self.assertGreaterEqual(len(warns), 1)
            self.assertTrue(any(issubclass(warning.category, warning_class) for warning in warns))


@unabc("{} shouldn't be used in tests")
class TestRuntime(Runtime):
    """
    An empty runtime to be used in tests
    """
    __test__ = False

    # unabc doesn't squash pylint errors
    def __init__(self, *args, **kwargs):
        memory_id_manager = MemoryIdManager()
        # Provide an IdReader if one isn't already passed to the runtime.
        if not args:
            kwargs.setdefault('id_reader', memory_id_manager)
        kwargs.setdefault('id_generator', memory_id_manager)
        super().__init__(*args, **kwargs)

    def handler_url(self, *args, **kwargs):
        raise NotImplementedError

    def local_resource_url(self, *args, **kwargs):
        raise NotImplementedError

    def publish(self, *args, **kwargs):
        raise NotImplementedError

    def resource_url(self, *args, **kwargs):
        raise NotImplementedError
