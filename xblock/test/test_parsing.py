# -*- coding: utf-8 -*-
"""Test XML parsing in XBlocks."""

import re
import StringIO
import textwrap
import unittest
import ddt
import mock

from xblock.core import XBlock, XML_NAMESPACES
from xblock.fields import Scope, String, Integer, Dict, List
from xblock.test.tools import blocks_are_equivalent
from xblock.test.toy_runtime import ToyRuntime

# XBlock classes to use in the tests.


def get_namespace_attrs():
    """ Returns string suitable to be used as an xmlns parameters in XBlock XML representation """
    return " ".join('xmlns:{}="{}"'.format(k, v) for k, v in XML_NAMESPACES.items())


class Leaf(XBlock):
    """Something we can parse from XML."""
    data1 = String(default="default_value", scope=Scope.user_state)
    data2 = String(default="default_value", scope=Scope.user_state)
    content = String(default="", scope=Scope.content)


class LeafWithDictAndList(XBlock):
    """A leaf containing dict and list options."""
    dictionary = Dict(default={"default": True}, scope=Scope.user_state)
    sequence = List(default=[1, 2, 3], scope=Scope.user_state)


class LeafWithOption(Leaf):
    """A leaf with an additional option set via xml attribute."""
    data3 = Dict(
        default={}, scope=Scope.user_state, enforce_type=True,
        xml_node=True)
    data4 = List(
        default=[], scope=Scope.user_state, enforce_type=True,
        xml_node=True)


class Container(XBlock):
    """A thing with children."""
    has_children = True


class Specialized(XBlock):
    """A block that wants to do its own XML parsing."""
    num_children = Integer(default=0, scope=Scope.user_state)

    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        """We'll just set num_children to the number of child nodes."""
        block = runtime.construct_xblock_from_class(cls, keys)
        block.num_children = len(node)
        return block

# Helpers


class XmlTestMixin(object):
    """
    Wraps parsing and exporting and other things to return more useful values. Does not define
    a runtime (thus calling it a mixin)
    """
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


class XmlTest(XmlTestMixin):
    """Helpful things for XML tests."""
    def setUp(self):
        super(XmlTest, self).setUp()
        self.runtime = ToyRuntime()


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
        self.assertEqual(child1.parent, block.scope_ids.usage_id)

        child2 = self.runtime.get_block(block.children[1])
        self.assertIsInstance(child2, Leaf)
        self.assertEqual(child2.data1, "child2")
        self.assertEqual(child2.parent, block.scope_ids.usage_id)

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

    @XBlock.register_temp_plugin(Leaf)
    def test_parse_unicode(self):
        block = self.parse_xml_to_block(u"<leaf data1='\u2603' />")
        self.assertIsInstance(block, Leaf)
        self.assertEqual(block.data1, u'\u2603')


@ddt.ddt
class ExportTest(XmlTest, unittest.TestCase):
    """Tests of the XML export facility."""

    @XBlock.register_temp_plugin(Leaf)
    def test_dead_simple_export(self):
        block = self.parse_xml_to_block("<leaf/>")
        xml = self.export_xml_for_block(block)
        self.assertRegexpMatches(
            xml.strip(),
            r"\<\?xml version='1.0' encoding='UTF8'\?\>\n\<leaf .*/\>"
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

    @XBlock.register_temp_plugin(LeafWithDictAndList)
    def test_dict_and_list_as_attribute(self):
        block = self.parse_xml_to_block(textwrap.dedent("""\
            <?xml version='1.0' encoding='utf-8'?>
            <leafwithdictandlist
                dictionary='{"foo": "bar"}'
                sequence='["one", "two", "three"]' />
            """))

        self.assertEquals(block.dictionary, {"foo": "bar"})
        self.assertEquals(block.sequence, ["one", "two", "three"])

    @XBlock.register_temp_plugin(LeafWithOption)
    def test_export_then_import_with_options(self):
        block = self.parse_xml_to_block(textwrap.dedent("""\
            <?xml version='1.0' encoding='utf-8'?>
            <leafwithoption xmlns:option="http://code.edx.org/xblock/option"
                data1="child1" data2='with a dict'>
                <option:data3>
                    child: 1
                    with custom option: True
                </option:data3>
                <option:data4>
                    - 1.23
                    - true
                    - some string
                </option:data4>
            </leafwithoption>
            """))
        xml = self.export_xml_for_block(block)

        block_imported = self.parse_xml_to_block(xml)

        self.assertEqual(block_imported.data3, {"child": 1, "with custom option": True})
        self.assertEqual(block_imported.data4, [1.23, True, "some string"])

        self.assertEqual(xml.count("child1"), 1)
        self.assertTrue(blocks_are_equivalent(block, block_imported))

    @XBlock.register_temp_plugin(LeafWithOption)
    def test_dict_and_list_export_format(self):
        xml = textwrap.dedent("""\
            <?xml version='1.0' encoding='UTF8'?>
            <leafwithoption %s xblock-family="xblock.v1">
              <option:data3>{
              "child": 1,
              "with custom option": true
            }</option:data3>
              <option:data4>[
              1.23,
              true,
              "some string"
            ]</option:data4>
            </leafwithoption>
            """) % get_namespace_attrs()
        block = self.parse_xml_to_block(xml)
        exported_xml = self.export_xml_for_block(block)

        self.assertEqual(xml, exported_xml)

    @XBlock.register_temp_plugin(Leaf)
    @ddt.data(
        "apoapsis",
        "periapsis",
        "inclination",
        "eccentricity"
    )
    def test_unknown_field_as_attribute_raises_warning(self, parameter_name):
        with mock.patch('logging.warn') as patched_warn:
            block = self.parse_xml_to_block("<leaf {0}='something irrelevant'></leaf>".format(parameter_name))
            patched_warn.assert_called_once_with("XBlock %s does not contain field %s", type(block), parameter_name)

    @XBlock.register_temp_plugin(LeafWithOption)
    @ddt.data(
        "apoapsis",
        "periapsis",
        "inclination",
        "eccentricity"
    )
    def test_unknown_field_as_node_raises_warning(self, parameter_name):
        xml = textwrap.dedent("""\
            <leafwithoption %s>
                <option:%s>Some completely irrelevant data</option:%s>
            </leafwithoption>
        """) % (get_namespace_attrs(), parameter_name, parameter_name)
        with mock.patch('logging.warn') as patched_warn:
            block = self.parse_xml_to_block(xml)
            patched_warn.assert_called_once_with("XBlock %s does not contain field %s", type(block), parameter_name)


def squish(text):
    """Turn any run of whitespace into one space."""
    return re.sub(r"\s+", " ", text)
