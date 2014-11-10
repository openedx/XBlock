"""
Test XBlock Aside
"""
from unittest import TestCase
from xblock.core import XBlockAside
from xblock.fields import ScopeIds
from xblock.fragment import Fragment
from xblock.runtime import DictKeyValueStore, KvsFieldData
from xblock.test.test_runtime import TestXBlock
from xblock.test.tools import TestRuntime


class TestAside(XBlockAside):
    """
    Test xblock aside class
    """
    FRAG_CONTENT = u"<p>Aside rendered</p>"

    @XBlockAside.aside_for('student_view')
    def student_view_aside(self, block, context):  # pylint: disable=unused-argument
        """Add to the student view"""
        return Fragment(self.FRAG_CONTENT)


class TestInheritedAside(TestAside):
    """
    XBlock Aside that inherits an aside view function from its parent.
    """
    FRAG_CONTENT = u"<p>Inherited aside rendered</p>"


class TestAsides(TestCase):
    """
    Tests of XBlockAsides.
    """
    def setUp(self):
        key_store = DictKeyValueStore()
        field_data = KvsFieldData(key_store)
        self.runtime = TestRuntime(services={'field-data': field_data})
        block_type = 'test'
        def_id = self.runtime.id_generator.create_definition(block_type)
        usage_id = self.runtime.id_generator.create_usage(def_id)
        self.tester = TestXBlock(self.runtime, scope_ids=ScopeIds('user', block_type, def_id, usage_id))

    @XBlockAside.register_temp_plugin(TestAside)
    def test_render_aside(self):
        """
        Test that rendering the xblock renders its aside
        """

        frag = self.runtime.render(self.tester, 'student_view', [u"ignore"])
        self.assertIn(TestAside.FRAG_CONTENT, frag.body_html())

        frag = self.runtime.render(self.tester, 'author_view', [u"ignore"])
        self.assertNotIn(TestAside.FRAG_CONTENT, frag.body_html())

    @XBlockAside.register_temp_plugin(TestAside)
    @XBlockAside.register_temp_plugin(TestInheritedAside)
    def test_inherited_aside_view(self):
        """
        Test that rendering the xblock renders its aside (when the aside view is
        inherited).
        """
        frag = self.runtime.render(self.tester, 'student_view', [u"ignore"])
        self.assertIn(TestAside.FRAG_CONTENT, frag.body_html())
        self.assertIn(TestInheritedAside.FRAG_CONTENT, frag.body_html())

        frag = self.runtime.render(self.tester, 'author_view', [u"ignore"])
        self.assertNotIn(TestAside.FRAG_CONTENT, frag.body_html())
        self.assertNotIn(TestInheritedAside.FRAG_CONTENT, frag.body_html())
