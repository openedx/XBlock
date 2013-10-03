"""
Test xblock/core/plugin.py
"""

from xblock.test.tools import assert_is, assert_raises_regexp

from xblock.core import XBlock
from xblock.plugin import AmbiguousPluginError, PluginMissingError


class AmbiguousBlock1(XBlock):
    """A dummy class to find as a plugin."""
    pass


class AmbiguousBlock2(XBlock):
    """A dummy class to find as a plugin."""
    pass


class UnambiguousBlock(XBlock):
    """A dummy class to find as a plugin."""
    pass


@XBlock.register_temp_plugin(AmbiguousBlock1, "bad_block")
@XBlock.register_temp_plugin(AmbiguousBlock2, "bad_block")
@XBlock.register_temp_plugin(UnambiguousBlock, "good_block")
def test_ambiguous_plugins():
    # We can load ok blocks even if there are bad blocks.
    cls = XBlock.load_class("good_block")
    assert_is(cls, UnambiguousBlock)

    # Trying to load bad blocks raises an exception.
    expected_msg = (
        "Ambiguous entry points for bad_block: "
        "xblock.test.test_plugin.AmbiguousBlock1, "
        "xblock.test.test_plugin.AmbiguousBlock2"
    )
    with assert_raises_regexp(AmbiguousPluginError, expected_msg):
        XBlock.load_class("bad_block")

    # We can use our own function as the select function.
    class MyOwnException(Exception):
        """We'll raise this from `boom`."""
        pass

    def boom(entry_points):
        """A select function to prove user-defined functions are called."""
        assert len(entry_points) == 2
        raise MyOwnException("This is boom")

    with assert_raises_regexp(MyOwnException, "This is boom"):
        XBlock.load_class("bad_block", select=boom)


def test_nosuch_plugin():
    # We can provide a default class to return for missing plugins.
    cls = XBlock.load_class("nosuch_block", default=UnambiguousBlock)
    assert_is(cls, UnambiguousBlock)

    # If we don't provide a default class, an exception is raised.
    with assert_raises_regexp(PluginMissingError, "nosuch_block"):
        XBlock.load_class("nosuch_block")
