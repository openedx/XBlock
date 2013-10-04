# -*- coding: utf-8 -*-
"""Test XML parsing in XBlocks."""

import re
import StringIO
import textwrap
import unittest

from xblock.core import XBlock
from xblock.fields import Scope, String, Integer
from xblock.test.tools import blocks_are_equivalent
from workbench.runtime import WorkbenchRuntime

# XBlock classes to use in the tests.


class Leaf(XBlock):
    """Something we can parse from XML."""
    data1 = String(default="default_value", scope=Scope.user_state)
    data2 = String(default="default_value", scope=Scope.user_state)
    content = String(default="", scope=Scope.content)


class Container(XBlock):
    """A thing with children."""
    has_children = True


class Specialized(XBlock):
    """A block that wants to do its own XML parsing."""
    num_children = Integer(default=0, scope=Scope.user_state)

    @classmethod
    def parse_xml(cls, node, runtime, keys):
        """We'll just set num_children to the number of child nodes."""
        block = runtime.construct_xblock_from_class(cls, keys)
        block.num_children = len(node)
        return block

# Helpers


class XmlTest(object):
    """Helpful things for XML tests."""

    def setUp(self):
        super(XmlTest, self).setUp()
        self.runtime = WorkbenchRuntime()

    def parse_xml_to_block(self, xml):
        """A helper to get a block from some XML."""
        usage_id = self.runtime.parse_xml_string(xml)
        block = self.runtime.get_block(usage_id)
        return block

    def export_xml_for_block(self, block):
        """A helper to return the XML string for a block."""
        output = StringIO.StringIO()
        self.runtime.export_to_xml(block, output)
        return output.getvalue()


# Tests!

class ParsingTest(XmlTest, unittest.TestCase):
    """Tests of XML parsing."""

    @XBlock.register_temp_plugin(Leaf)
    def test_parsing(self):
        block = self.parse_xml_to_block("<leaf data2='parsed'/>")

        self.assertIsInstance(block, Leaf)
        self.assertEqual(block.data1, "default_value")
        self.assertEqual(block.data2, "parsed")
        self.assertEqual(block.content, "")

    @XBlock.register_temp_plugin(Leaf)
    def test_parsing_content(self):
        block = self.parse_xml_to_block("<leaf>my text!</leaf>")

        self.assertIsInstance(block, Leaf)
        self.assertEqual(block.content, "my text!")

    @XBlock.register_temp_plugin(Leaf)
    @XBlock.register_temp_plugin(Container)
    def test_parsing_children(self):
        block = self.parse_xml_to_block("""\
                    <container>
                        <leaf data1='child1'/>
                        <leaf data1='child2'/>
                    </container>
                    """)
        self.assertIsInstance(block, Container)
        self.assertEqual(len(block.children), 2)

        child1 = self.runtime.get_block(block.children[0])
        self.assertIsInstance(child1, Leaf)
        self.assertEqual(child1.data1, "child1")

        child2 = self.runtime.get_block(block.children[1])
        self.assertIsInstance(child2, Leaf)
        self.assertEqual(child2.data1, "child2")

    @XBlock.register_temp_plugin(Leaf)
    @XBlock.register_temp_plugin(Specialized)
    def test_customized_parsing(self):
        block = self.parse_xml_to_block("""\
                    <specialized>
                        <leaf/><leaf/><leaf/>
                    </specialized>
                    """)
        self.assertIsInstance(block, Specialized)
        self.assertEqual(block.num_children, 3)


class ExportTest(XmlTest, unittest.TestCase):
    """Tests of the XML export facility."""

    @XBlock.register_temp_plugin(Leaf)
    def test_dead_simple_export(self):
        block = self.parse_xml_to_block("<leaf/>")
        xml = self.export_xml_for_block(block)
        self.assertEqual(
            xml.strip(),
            "<?xml version='1.0' encoding='UTF8'?>\n<leaf/>"
        )

    @XBlock.register_temp_plugin(Leaf)
    @XBlock.register_temp_plugin(Container)
    def test_export_then_import(self):
        block = self.parse_xml_to_block(textwrap.dedent("""\
            <?xml version='1.0' encoding='utf-8'?>
            <container>
                <leaf data1='child1' data2='I&#39;m also child1' />
                <leaf data2="me too!" data1='child2' ></leaf>
                <container>
                    <leaf data1='ʇxǝʇ uʍop-ǝpısdn' data2='whoa'>
                        ᵾnɨȼøđɇ ȼȺn ƀɇ ŧɍɨȼꝁɏ!
                    </leaf>
                </container>
                <leaf>Some text content.</leaf>
            </container>
            """))
        xml = self.export_xml_for_block(block)
        block_imported = self.parse_xml_to_block(xml)

        print repr(xml)   # so if the test fails, we can see it.

        # Crude checks that the XML is correct.  The exact form of the XML
        # isn't important.
        self.assertEqual(xml.count("container"), 4)
        self.assertEqual(xml.count("child1"), 2)
        self.assertEqual(xml.count("child2"), 1)
        self.assertEqual(xml.count("ʇxǝʇ uʍop-ǝpısdn"), 1)
        self.assertEqual(xml.count("ᵾnɨȼøđɇ ȼȺn ƀɇ ŧɍɨȼꝁɏ!"), 1)

        # The important part: exporting then importing a block should give
        # you an equivalent block.
        self.assertTrue(blocks_are_equivalent(block, block_imported))


def squish(text):
    """Turn any run of whitespace into one space."""
    return re.sub(r"\s+", " ", text)


class HtmlInOutTest(XmlTest, unittest.TestCase):
    """Tests of the implicit HTML block."""

    def test_implicit_html_import(self):
        # This test is fiddly about where the whitespace goes in the xml...
        the_xml = """\
            <?xml version='1.0' encoding='UTF8'?>
            <html><p>Hello there.</p>
                <p>This is HTML!</p>
                <p>ᵾnɨȼøđɇ ȼȺn ƀɇ ŧɍɨȼꝁɏ!</p>
                <p>1 &lt; 2 &amp; 4 &gt; 3</p>
            </html>
            """.strip()
        block = self.parse_xml_to_block(the_xml)
        new_xml = self.export_xml_for_block(block)
        # For now, I'm not sure how to treat the whitespace, so ignore it.
        self.assertEqual(squish(the_xml), squish(new_xml))

    def test_text_content(self):
        tests = [
            "<html>Hello, world!</html>",
            "<html>Hello, <b>world!</b></html>",
            "<html><b>Hello</b>, world!</html>",
            "<html><b>Hello</b>, <b>world!</b></html>",
            "<html><b>Hello</b>, <b>world!</b> &amp; goodbye.</html>",
        ]

        for test in tests:
            block = self.parse_xml_to_block(test)
            xml = self.export_xml_for_block(block)

            self.assertIn(test, xml)

    def test_text_is_unicode(self):
        the_xml = "<html>Hello, world</html>"
        block = self.parse_xml_to_block(the_xml)
        self.assertTrue(isinstance(block.content, unicode))
