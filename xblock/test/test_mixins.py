"""
Tests of the XBlock-family functionality mixins
"""

from unittest import TestCase

from xblock.fields import List, Scope, Integer
from xblock.mixins import ScopedStorageMixin, HierarchyMixin, IndexInfoMixin


class AttrAssertionMixin(TestCase):
    """
    A mixin to add attribute assertion methods to TestCases.
    """
    def assertHasAttr(self, obj, attr):
        "Assert that `obj` has the attribute named `attr`."
        self.assertTrue(hasattr(obj, attr), "{!r} doesn't have attribute {!r}".format(obj, attr))

    def assertNotHasAttr(self, obj, attr):
        "Assert that `obj` doesn't have the attribute named `attr`."
        self.assertFalse(hasattr(obj, attr), "{!r} has attribute {!r}".format(obj, attr))


class TestScopedStorageMixin(AttrAssertionMixin, TestCase):
    "Tests of the ScopedStorageMixin."

    class ScopedStorageMixinTester(ScopedStorageMixin):
        """Toy class for ScopedStorageMixin testing"""

        field_a = Integer(scope=Scope.settings)
        field_b = Integer(scope=Scope.content)

    class ChildClass(ScopedStorageMixinTester):
        """Toy class for ModelMetaclass testing"""
        pass

    class FieldsMixin(object):
        """Toy mixin for field testing"""
        field_c = Integer(scope=Scope.settings)

    class MixinChildClass(FieldsMixin, ScopedStorageMixinTester):
        """Toy class for ScopedStorageMixin testing with mixed-in fields"""
        pass

    class MixinGrandchildClass(MixinChildClass):
        """Toy class for ScopedStorageMixin testing with inherited mixed-in fields"""
        pass

    def test_scoped_storage_mixin(self):

        # `ModelMetaclassTester` and `ChildClass` both obtain the `fields` attribute
        # from the `ModelMetaclass`. Since this is not understood by static analysis,
        # silence this error for the duration of this test.
        # pylint: disable=E1101
        self.assertIsNot(self.ScopedStorageMixinTester.fields, self.ChildClass.fields)

        self.assertHasAttr(self.ScopedStorageMixinTester, 'field_a')
        self.assertHasAttr(self.ScopedStorageMixinTester, 'field_b')

        self.assertIs(self.ScopedStorageMixinTester.field_a, self.ScopedStorageMixinTester.fields['field_a'])
        self.assertIs(self.ScopedStorageMixinTester.field_b, self.ScopedStorageMixinTester.fields['field_b'])

        self.assertHasAttr(self.ChildClass, 'field_a')
        self.assertHasAttr(self.ChildClass, 'field_b')

        self.assertIs(self.ChildClass.field_a, self.ChildClass.fields['field_a'])
        self.assertIs(self.ChildClass.field_b, self.ChildClass.fields['field_b'])

    def test_with_mixins(self):
        # Testing model metaclass with mixins

        # `MixinChildClass` and `MixinGrandchildClass` both obtain the `fields` attribute
        # from the `ScopedStorageMixin`. Since this is not understood by static analysis,
        # silence this error for the duration of this test.
        # pylint: disable=E1101

        self.assertHasAttr(self.MixinChildClass, 'field_a')
        self.assertHasAttr(self.MixinChildClass, 'field_c')
        self.assertIs(self.MixinChildClass.field_a, self.MixinChildClass.fields['field_a'])
        self.assertIs(self.FieldsMixin.field_c, self.MixinChildClass.fields['field_c'])

        self.assertHasAttr(self.MixinGrandchildClass, 'field_a')
        self.assertHasAttr(self.MixinGrandchildClass, 'field_c')
        self.assertIs(self.MixinGrandchildClass.field_a, self.MixinGrandchildClass.fields['field_a'])
        self.assertIs(self.MixinGrandchildClass.field_c, self.MixinGrandchildClass.fields['field_c'])


class TestHierarchyMixin(AttrAssertionMixin, TestCase):
    "Tests of the HierarchyMixin."

    class HasChildren(HierarchyMixin):
        """Toy class for ChildrenModelMetaclass testing"""
        has_children = True

    class WithoutChildren(HierarchyMixin):
        """Toy class for ChildrenModelMetaclass testing"""
        pass

    class InheritedChildren(HasChildren):
        """Toy class for ChildrenModelMetaclass testing"""
        pass

    def test_children_metaclass(self):
        # `HasChildren` and `WithoutChildren` both obtain the `children` attribute and
        # the `has_children` method from the `ChildrenModelMetaclass`. Since this is not
        # understood by static analysis, silence this error for the duration of this test.
        # pylint: disable=E1101

        self.assertTrue(self.HasChildren.has_children)
        self.assertFalse(self.WithoutChildren.has_children)
        self.assertTrue(self.InheritedChildren.has_children)

        self.assertHasAttr(self.HasChildren, 'children')
        self.assertNotHasAttr(self.WithoutChildren, 'children')
        self.assertHasAttr(self.InheritedChildren, 'children')

        self.assertIsInstance(self.HasChildren.children, List)
        self.assertEqual(Scope.children, self.HasChildren.children.scope)
        self.assertIsInstance(self.InheritedChildren.children, List)
        self.assertEqual(Scope.children, self.InheritedChildren.children.scope)


class TestIndexInfoMixin(AttrAssertionMixin):
    """
    Tests for Index
    """
    class IndexInfoMixinTester(IndexInfoMixin):
        """Test class for index mixin"""
        pass

    def test_index_info(self):
        self.assertHasAttr(self.IndexInfoMixinTester, 'index_dictionary')
        with_index_info = self.IndexInfoMixinTester().index_dictionary()
        self.assertFalse(with_index_info)
        self.assertTrue(isinstance(with_index_info, dict))
