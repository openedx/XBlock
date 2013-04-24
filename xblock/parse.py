"""XML Parsing for XBlocks."""

from lxml import etree
from cStringIO import StringIO

from xblock.core import XBlock


def parse_xml(fileobj, usage_factory):
    """Parse the data in the open file `fileobj`.

    The result is a usage object constructed by `usage_factory`, which must
    have a signature like::

        Usage(block_name, initial_state, children, def_id)

    and those four attributes must then exist on the result.

    """
    dom = etree.parse(fileobj)
    tree = _usage_from_node(dom.getroot(), usage_factory)
    tree = _process_node(tree, usage_factory)
    return tree


def parse_xml_string(xml, usage_factory):
    """Parse the string `xml`, just like `parse_xml`.

    `xml` is a byte string to parse.

    """
    return parse_xml(StringIO(xml), usage_factory)

HTML_TAGS = set("p ol ul div span b i".split())


def _usage_from_node(node, usage_factory):
    """A recursive function to create a usage from a dom node."""

    if node.tag in HTML_TAGS:
        content = etree.tostring(node, encoding='unicode')
        return usage_factory("html", [], {"content": content})
    else:
        kids = []
        for child in node:
            kid = _usage_from_node(child, usage_factory)
            # Coalesce adjacent HTML nodes.
            if kid.block_name == 'html' and kids and kids[-1].block_name == 'html':
                kids[-1].initial_state["content"] += kid.initial_state["content"]
            else:
                kids.append(kid)
        content = dict(node.items())
        text = node.text
        if text and text.strip():
            content["content"] = text
        return usage_factory(node.tag, kids, content)


def _process_node(node, usage_factory):
    """Give the XBlock classes a chance to manipulate the tree."""
    block_cls = XBlock.load_class(node.block_name)
    node = block_cls.preprocess_input(node, usage_factory)
    kids = [_process_node(kid, usage_factory) for kid in node.children]
    if any(old is not new for old, new in zip(node.children, kids)):
        node = usage_factory(node.block_name, kids, node.initial_state, node.def_id)
    node = block_cls.postprocess_input(node, usage_factory)
    return node
