"""
Tests for helpers.py
"""

import unittest

from xblock.core import XBlock
from xblock.test.toy_runtime import ToyRuntime
from xblock.utils.helpers import child_isinstance


# pylint: disable=unnecessary-pass
class DogXBlock(XBlock):
    """ Test XBlock representing any dog. Raises error if instantiated. """
    pass


# pylint: disable=unnecessary-pass
class GoldenRetrieverXBlock(DogXBlock):
    """ Test XBlock representing a golden retriever """
    pass


# pylint: disable=unnecessary-pass
class CatXBlock(XBlock):
    """ Test XBlock representing any cat """
    pass


class BasicXBlock(XBlock):
    """ Basic XBlock """
    has_children = True


class TestChildIsInstance(unittest.TestCase):
    """
    Test child_isinstance helper method, in the workbench runtime.
    """

    @XBlock.register_temp_plugin(GoldenRetrieverXBlock, "gr")
    @XBlock.register_temp_plugin(CatXBlock, "cat")
    @XBlock.register_temp_plugin(BasicXBlock, "block")
    def test_child_isinstance(self):
        """
        Check that child_isinstance() works on direct children
        """
        runtime = ToyRuntime()
        root_id = runtime.parse_xml_string('<block> <block><cat/><gr/></block> <cat/> <gr/> </block>')
        root = runtime.get_block(root_id)
        self.assertFalse(child_isinstance(root, root.children[0], DogXBlock))
        self.assertFalse(child_isinstance(root, root.children[0], GoldenRetrieverXBlock))
        self.assertTrue(child_isinstance(root, root.children[0], BasicXBlock))

        self.assertFalse(child_isinstance(root, root.children[1], DogXBlock))
        self.assertFalse(child_isinstance(root, root.children[1], GoldenRetrieverXBlock))
        self.assertTrue(child_isinstance(root, root.children[1], CatXBlock))

        self.assertFalse(child_isinstance(root, root.children[2], CatXBlock))
        self.assertTrue(child_isinstance(root, root.children[2], DogXBlock))
        self.assertTrue(child_isinstance(root, root.children[2], GoldenRetrieverXBlock))

    @XBlock.register_temp_plugin(GoldenRetrieverXBlock, "gr")
    @XBlock.register_temp_plugin(CatXBlock, "cat")
    @XBlock.register_temp_plugin(BasicXBlock, "block")
    def test_child_isinstance_descendants(self):
        """
        Check that child_isinstance() works on deeper descendants
        """
        runtime = ToyRuntime()
        root_id = runtime.parse_xml_string('<block> <block><cat/><gr/></block> <cat/> <gr/> </block>')
        root = runtime.get_block(root_id)
        block = root.runtime.get_block(root.children[0])
        self.assertIsInstance(block, BasicXBlock)

        self.assertFalse(child_isinstance(root, block.children[0], DogXBlock))
        self.assertTrue(child_isinstance(root, block.children[0], CatXBlock))

        self.assertTrue(child_isinstance(root, block.children[1], DogXBlock))
        self.assertTrue(child_isinstance(root, block.children[1], GoldenRetrieverXBlock))
        self.assertFalse(child_isinstance(root, block.children[1], CatXBlock))
