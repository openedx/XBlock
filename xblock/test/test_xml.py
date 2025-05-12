"""
Tests for xblock/xml.py
"""

import unittest
from io import BytesIO
from lxml import etree

from xblock.xml import (
    name_to_pathname,
    is_pointer_tag,
    format_filepath,
    file_to_xml,
)


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
