"""Test XML parsing in XBlocks."""

import unittest

from xblock.core import XBlock
from xblock.fields import Scope, String, Integer
from workbench.runtime import WorkbenchRuntime



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

    def parse_xml(self, node):
        """We'll just set num_children to the number of child nodes."""
        self.num_children = len(node)


class ParsingTest(unittest.TestCase):
    """Tests if XML parsing."""

    def setUp(self):
        super(ParsingTest, self).setUp()
        self.runtime = None

    def parse_xml_to_block(self, xml):
        """A helper to get a block from some XML."""
        self.runtime = WorkbenchRuntime()
        usage_id = self.runtime.parse_xml_string(xml)
        block = self.runtime.get_block(usage_id)
        return block

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
