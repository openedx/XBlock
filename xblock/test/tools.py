"""
Tools for testing XBlocks
"""

from functools import partial

# nose.tools has convenient assert methods, but it defines them in a clever way
# that baffles pylint.  Import them all here so we can keep the pylint clutter
# out of the rest of our files.
from nose.tools import (                        # pylint: disable=W0611,E0611
    assert_true, assert_false,
    assert_equals, assert_not_equals,
    assert_is, assert_is_not,
    assert_is_instance, assert_is_none,
    assert_in, assert_not_in,
    assert_raises, assert_raises_regexp,
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
        def dummy_method(self, *args, **kwargs):  # pylint: disable=unused-argument
            """The method provided for all missing abstract methods."""
            raise NotImplementedError(msg.format(ab_name))
        return dummy_method

    for ab_name in cls.__abstractmethods__:
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
