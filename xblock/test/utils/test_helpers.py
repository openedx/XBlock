"""
Tests for helpers.py
"""

import unittest
from io import BytesIO
from unittest.mock import patch, Mock
from lxml import etree

from xblock.core import XBlock
from xblock.test.toy_runtime import ToyRuntime
from xblock.utils.helpers import (
    child_isinstance,
    name_to_pathname,
    is_pointer_tag,
    load_definition_xml,
    format_filepath,
    file_to_xml,
)


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


class TestPointerTagParsing(unittest.TestCase):
    """
    Tests for core functions in XBlock.
    """
    def test_name_to_pathname(self):
        self.assertEqual(name_to_pathname("course:subcourse"), "course/subcourse")
        self.assertEqual(name_to_pathname("module:lesson:part"), "module/lesson/part")
        self.assertEqual(name_to_pathname("no_colon"), "no_colon")

    def test_is_pointer_tag(self):
        # Case 1: Valid pointer tag
        xml_obj = etree.Element("some_tag", url_name="test_url")
        self.assertTrue(is_pointer_tag(xml_obj))

        # Case 2: Valid course pointer tag
        xml_obj = etree.Element("course", url_name="test_url", course="test_course", org="test_org")
        self.assertTrue(is_pointer_tag(xml_obj))

        # Case 3: Invalid case - extra attribute
        xml_obj = etree.Element("some_tag", url_name="test_url", extra_attr="invalid")
        self.assertFalse(is_pointer_tag(xml_obj))

        # Case 4: Invalid case - has text
        xml_obj = etree.Element("some_tag", url_name="test_url")
        xml_obj.text = "invalid_text"
        self.assertFalse(is_pointer_tag(xml_obj))

        # Case 5: Invalid case - has children
        xml_obj = etree.Element("some_tag", url_name="test_url")
        _ = etree.SubElement(xml_obj, "child")
        self.assertFalse(is_pointer_tag(xml_obj))

    @patch("xblock.utils.helpers.load_file")
    def test_load_definition_xml(self, mock_load_file):
        mock_load_file.return_value = "<mock_xml />"
        node = etree.Element("course", url_name="test_url")
        runtime = Mock()
        def_id = "mock_id"

        definition_xml, filepath = load_definition_xml(node, runtime, def_id)
        self.assertEqual(filepath, "course/test_url.xml")
        self.assertEqual(definition_xml, "<mock_xml />")
        mock_load_file.assert_called_once()

    def test_format_filepath(self):
        self.assertEqual(format_filepath("course", "test_url"), "course/test_url.xml")

    def test_file_to_xml(self):
        """Test that `file_to_xml` correctly parses XML from a file object."""
        # Create a BytesIO object
        file_obj = BytesIO(b"<root><child>Value</child></root>")

        # Parse the XML
        result = file_to_xml(file_obj)

        # Verify the result
        self.assertEqual(result.tag, 'root')
        self.assertEqual(result[0].tag, 'child')
        self.assertEqual(result[0].text, 'Value')
