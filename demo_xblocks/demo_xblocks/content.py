"""Content-oriented XBlocks."""

from string import Template  # pylint: disable=W0402

from lxml import etree

from xblock.core import XBlock, String, Scope
from xblock.fragment import Fragment


class HelloWorldBlock(XBlock):
    """A simple block: just show some fixed content."""
    def fallback_view(self, view_name, context=None):  # pylint: disable=W0613
        """Provide a fallback view handler"""
        return Fragment(u"Hello, world!")


class HtmlBlock(XBlock):
    """Render content as HTML.

    The content can have $PLACEHOLDERS, which will be substituted with values
    from the context.

    """

    content = String(help="The HTML to display", scope=Scope.content, default=u"<b>DEFAULT</b>")

    def fallback_view(self, view_name, context=None):
        """Provide a fallback view handler"""
        context = context or {}
        return Fragment(Template(self.content).substitute(**context))

    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        """
        Parse the XML for an HTML block.

        The entire subtree under `node` is re-serialized, and set as the
        content of the XBlock.

        """
        block = runtime.construct_xblock_from_class(cls, keys)

        block.content = unicode(node.text or u"")
        for child in node:
            block.content += etree.tostring(child, encoding='unicode')

        return block

    def add_xml_to_node(self, node):
        """
        Set attributes and children on `node` to represent ourselves as XML.

        We parse our HTML content, and graft those nodes onto `node`.

        """
        xml = "<html_demo>" + self.content + "</html_demo>"
        html_node = etree.fromstring(xml)

        node.tag = html_node.tag
        node.text = html_node.text
        for child in html_node:
            node.append(child)

    @staticmethod
    def workbench_scenarios():
        return [
            ("A little HTML", """
                <vertical_demo>
                <html_demo>
                <h2>Gettysburg Address</h2>

                <p>Four score and seven years ago our fathers brought forth on
                this <a href='http://en.wikipedia.org/wiki/Continent'>continent</a>
                a new nation, conceived in liberty, and dedicated to
                the proposition that all men are created equal.</p>

                <p>Now we are engaged in a great <a href='http://en.wikipedia.org/wiki/Civil_war'>civil war</a>,
                testing whether that nation, or any nation so conceived and so
                dedicated, can long endure. We are met on a great battle-field of
                that war. We have come to dedicate a portion of that field, as a
                final resting place for those who here gave their lives that that
                nation might live. It is altogether fitting and proper that we
                should do this.</p>

                <p>But, in a larger sense, we can not dedicate, we can not
                consecrate, we can not hallow this ground. The brave men, living
                and dead, who struggled here, have consecrated it, far above our
                poor power to add or detract. The world will little note, nor long
                remember what we say here, but it can never forget what they did
                here. It is for us the living, rather, to be dedicated here to the
                unfinished work which they who fought here have thus far so nobly
                advanced. It is rather for us to be here dedicated to the great
                task remaining before us &#8212; that from these honored dead we
                take increased devotion to that cause for which they gave the last
                full measure of devotion &#8212; that we here highly resolve that
                these dead shall not have died in vain &#8212; that this nation,
                under God, shall have a new birth of freedom &#8212; and that
                government of the people, by the people, for the people, shall not
                perish from the earth.</p>
                </html_demo>
                </vertical_demo>
             """),
        ]
