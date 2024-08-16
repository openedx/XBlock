"""
Test xblock/core/plugin.py
"""
from unittest.mock import patch, Mock
import pytest

from xblock.core import XBlock
from xblock import plugin
from xblock.plugin import AmbiguousPluginError, AmbiguousPluginOverrideError, PluginMissingError


class AmbiguousBlock1(XBlock):
    """A dummy class to find as a plugin."""


class AmbiguousBlock2(XBlock):
    """A dummy class to find as a plugin."""


class UnambiguousBlock(XBlock):
    """A dummy class to find as a plugin."""


class OverriddenBlock(XBlock):
    """A dummy class to find as a plugin."""


@XBlock.register_temp_plugin(AmbiguousBlock1, "bad_block")
@XBlock.register_temp_plugin(AmbiguousBlock2, "bad_block")
@XBlock.register_temp_plugin(UnambiguousBlock, "good_block")
def test_ambiguous_plugins():
    # We can load ok blocks even if there are bad blocks.
    cls = XBlock.load_class("good_block")
    assert cls is UnambiguousBlock

    # Trying to load bad blocks raises an exception.
    expected_msg = (
        "Ambiguous entry points for bad_block: "
        "xblock.test.test_plugin.AmbiguousBlock1, "
        "xblock.test.test_plugin.AmbiguousBlock2"
    )
    with pytest.raises(AmbiguousPluginError, match=expected_msg):
        XBlock.load_class("bad_block")

    # We can use our own function as the select function.
    class MyOwnException(Exception):
        """We'll raise this from `boom`."""

    def boom(identifier, entry_points):
        """A select function to prove user-defined functions are called."""
        assert len(entry_points) == 2
        assert identifier == "bad_block"
        raise MyOwnException("This is boom")

    with pytest.raises(MyOwnException, match="This is boom"):
        XBlock.load_class("bad_block", select=boom)


@XBlock.register_temp_plugin(OverriddenBlock, "overridden_block", group='xblock.v1.overrides')
@XBlock.register_temp_plugin(UnambiguousBlock, "overridden_block")
def test_plugin_override():
    # Trying to load a block that is overridden returns the correct override
    override = XBlock.load_class("overridden_block")
    assert override is OverriddenBlock


@XBlock.register_temp_plugin(OverriddenBlock, "overridden_block", group='xblock.v1.overrides')
def test_plugin_override_missing_original():
    # Trying to override a block that has no original block should raise an error
    with pytest.raises(PluginMissingError, match="overridden_block"):
        XBlock.load_class("overridden_block")


@XBlock.register_temp_plugin(AmbiguousBlock1, "overridden_block", group='xblock.v1.overrides')
@XBlock.register_temp_plugin(AmbiguousBlock2, "overridden_block", group='xblock.v1.overrides')
@XBlock.register_temp_plugin(OverriddenBlock, "overridden_block")
def test_plugin_override_ambiguous():

    # Trying to load a block that is overridden, but ambigous, errors.
    expected_msg = (
        "Ambiguous entry points for overridden_block: "
        "xblock.test.test_plugin.AmbiguousBlock1, "
        "xblock.test.test_plugin.AmbiguousBlock2"
    )
    with pytest.raises(AmbiguousPluginOverrideError, match=expected_msg):
        XBlock.load_class("overridden_block")


def test_nosuch_plugin():
    # We can provide a default class to return for missing plugins.
    cls = XBlock.load_class("nosuch_block", default=UnambiguousBlock)
    assert cls is UnambiguousBlock

    # If we don't provide a default class, an exception is raised.
    with pytest.raises(PluginMissingError, match="nosuch_block"):
        XBlock.load_class("nosuch_block")


@patch.object(XBlock, '_load_class_entry_point', Mock(side_effect=Exception))
def test_broken_plugin():
    plugins = XBlock.load_classes()
    assert not list(plugins)


def _num_plugins_cached():
    """
    Returns the number of plugins that have been cached.
    """
    return len(plugin.PLUGIN_CACHE)


@XBlock.register_temp_plugin(AmbiguousBlock1, "ambiguous_block_1")
def test_plugin_caching():
    plugin.PLUGIN_CACHE = {}
    assert _num_plugins_cached() == 0

    XBlock.load_class("ambiguous_block_1")
    assert _num_plugins_cached() == 1

    XBlock.load_class("ambiguous_block_1")
    assert _num_plugins_cached() == 1
