"""
Tests of the XBlock-family functionality mixins
"""

from xblock.test.tools import assert_equals, assert_is

from xblock.fields import List, Scope, Integer
from xblock.mixins import ChildrenModelMetaclass, ModelMetaclass


def test_model_metaclass():
    class ModelMetaclassTester(object):
        """Toy class for ModelMetaclass testing"""
        __metaclass__ = ModelMetaclass

        field_a = Integer(scope=Scope.settings)
        field_b = Integer(scope=Scope.content)

        def __init__(self, field_data):
            self._field_data = field_data

    class ChildClass(ModelMetaclassTester):
        """Toy class for ModelMetaclass testing"""
        pass

    # `ModelMetaclassTester` and `ChildClass` both obtain the `fields` attribute
    # from the `ModelMetaclass`. Since this is not understood by static analysis,
    # silence this error for the duration of this test.
    # pylint: disable=E1101
    assert hasattr(ModelMetaclassTester, 'field_a')
    assert hasattr(ModelMetaclassTester, 'field_b')

    assert_is(ModelMetaclassTester.field_a, ModelMetaclassTester.fields['field_a'])
    assert_is(ModelMetaclassTester.field_b, ModelMetaclassTester.fields['field_b'])

    assert hasattr(ChildClass, 'field_a')
    assert hasattr(ChildClass, 'field_b')

    assert_is(ChildClass.field_a, ChildClass.fields['field_a'])
    assert_is(ChildClass.field_b, ChildClass.fields['field_b'])


def test_with_mixins():
    # Testing model metaclass with mixins
    class FieldsMixin(object):
        """Toy class for field testing"""
        field_a = Integer(scope=Scope.settings)

    class BaseClass(object):
        """Toy class for ModelMetaclass testing"""
        __metaclass__ = ModelMetaclass

    class ChildClass(FieldsMixin, BaseClass):
        """Toy class for ModelMetaclass and field testing"""
        pass

    class GrandchildClass(ChildClass):
        """Toy class for ModelMetaclass and field testing"""
        pass

    # `ChildClass` and `GrandchildClass` both obtain the `fields` attribute
    # from the `ModelMetaclass`. Since this is not understood by static analysis,
    # silence this error for the duration of this test.
    # pylint: disable=E1101

    assert hasattr(ChildClass, 'field_a')
    assert_is(ChildClass.field_a, ChildClass.fields['field_a'])

    assert hasattr(GrandchildClass, 'field_a')
    assert_is(GrandchildClass.field_a, GrandchildClass.fields['field_a'])


def test_children_metaclass():

    class HasChildren(object):
        """Toy class for ChildrenModelMetaclass testing"""
        __metaclass__ = ChildrenModelMetaclass

        has_children = True

    class WithoutChildren(object):
        """Toy class for ChildrenModelMetaclass testing"""
        __metaclass__ = ChildrenModelMetaclass

    class InheritedChildren(HasChildren):
        """Toy class for ChildrenModelMetaclass testing"""
        pass

    # `HasChildren` and `WithoutChildren` both obtain the `children` attribute and
    # the `has_children` method from the `ChildrenModelMetaclass`. Since this is not
    # understood by static analysis, silence this error for the duration of this test.
    # pylint: disable=E1101

    assert HasChildren.has_children
    assert not WithoutChildren.has_children
    assert InheritedChildren.has_children

    assert hasattr(HasChildren, 'children')
    assert not hasattr(WithoutChildren, 'children')
    assert hasattr(InheritedChildren, 'children')

    assert isinstance(HasChildren.children, List)
    assert_equals(Scope.children, HasChildren.children.scope)
    assert isinstance(InheritedChildren.children, List)
    assert_equals(Scope.children, InheritedChildren.children.scope)
