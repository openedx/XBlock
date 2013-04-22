from mock import patch
from nose.tools import assert_in, assert_equals, assert_raises

from xblock.core import *


def test_model_metaclass():
    class ModelMetaclassTester(object):
        __metaclass__ = ModelMetaclass

        field_a = Integer(scope=Scope.settings)
        field_b = Integer(scope=Scope.content)

        def __init__(self, model_data):
            self._model_data = model_data

    class ChildClass(ModelMetaclassTester):
        pass

    assert hasattr(ModelMetaclassTester, 'field_a')
    assert hasattr(ModelMetaclassTester, 'field_b')

    assert_in(ModelMetaclassTester.field_a, ModelMetaclassTester.fields)
    assert_in(ModelMetaclassTester.field_b, ModelMetaclassTester.fields)

    assert hasattr(ChildClass, 'field_a')
    assert hasattr(ChildClass, 'field_b')

    assert_in(ChildClass.field_a, ChildClass.fields)
    assert_in(ChildClass.field_b, ChildClass.fields)


def test_model_metaclass_with_mixins():
    class FieldsMixin(object):
        field_a = Integer(scope=Scope.settings)

    class BaseClass(object):
        __metaclass__ = ModelMetaclass

    class ChildClass(FieldsMixin, BaseClass):
        pass

    class GrandchildClass(ChildClass):
        pass

    assert hasattr(ChildClass, 'field_a')
    assert_in(ChildClass.field_a, ChildClass.fields)

    assert hasattr(GrandchildClass, 'field_a')
    assert_in(GrandchildClass.field_a, GrandchildClass.fields)

def test_children_metaclass():

    class HasChildren(object):
        __metaclass__ = ChildrenModelMetaclass

        has_children = True

    class WithoutChildren(object):
        __metaclass__ = ChildrenModelMetaclass

    class InheritedChildren(HasChildren):
        pass

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


def test_field_access():
    class FieldTester(object):
        __metaclass__ = ModelMetaclass

        field_a = Integer(scope=Scope.settings)
        field_b = Integer(scope=Scope.content, default=10)
        field_c = Integer(scope=Scope.user_state, computed_default=lambda s: s.field_a + s.field_b)

        def __init__(self, model_data):
            self._model_data = model_data

    field_tester = FieldTester({'field_a': 5, 'field_x': 15})

    assert_equals(5, field_tester.field_a)
    assert_equals(10, field_tester.field_b)
    assert_equals(15, field_tester.field_c)
    assert not hasattr(field_tester, 'field_x')

    field_tester.field_a = 20
    assert_equals(20, field_tester._model_data['field_a'])
    assert_equals(10, field_tester.field_b)
    assert_equals(30, field_tester.field_c)

    del field_tester.field_a
    assert_equals(None, field_tester.field_a)
    assert hasattr(FieldTester, 'field_a')


class TestNamespace(Namespace):
    field_x = List(scope=Scope.content)
    field_y = String(scope=Scope.user_state, default="default_value")


@patch('xblock.core.Namespace.load_classes', return_value=[('test', TestNamespace)])
def test_namespace_metaclass(mock_load_classes):
    class TestClass(object):
        __metaclass__ = NamespacesMetaclass

    assert hasattr(TestClass, 'test')
    assert hasattr(TestClass.test, 'field_x')
    assert hasattr(TestClass.test, 'field_y')

    assert_in(TestNamespace.field_x, TestClass.test.fields)
    assert_in(TestNamespace.field_y, TestClass.test.fields)
    assert isinstance(TestClass.test, Namespace)


@patch('xblock.core.Namespace.load_classes', return_value=[('test', TestNamespace)])
def test_namespace_field_access(mock_load_classes):
    class Metaclass(ModelMetaclass, NamespacesMetaclass):
        pass

    class FieldTester(object):
        __metaclass__ = Metaclass

        field_a = Integer(scope=Scope.settings)
        field_b = Integer(scope=Scope.content, default=10)
        field_c = Integer(scope=Scope.user_state, computed_default=lambda s: s.field_a + s.field_b)

        def __init__(self, model_data):
            self._model_data = model_data

    field_tester = FieldTester({
        'field_a': 5,
        'field_x': [1, 2, 3],
    })

    assert_equals(5, field_tester.field_a)
    assert_equals(10, field_tester.field_b)
    assert_equals(15, field_tester.field_c)
    assert_equals([1, 2, 3], field_tester.test.field_x)
    assert_equals('default_value', field_tester.test.field_y)

    field_tester.test.field_x = ['a', 'b']
    assert_equals(['a', 'b'], field_tester._model_data['field_x'])

    del field_tester.test.field_x
    assert_equals([], field_tester.test.field_x)

    assert_raises(AttributeError, getattr, field_tester.test, 'field_z')
    assert_raises(AttributeError, delattr, field_tester.test, 'field_z')

    # Namespaces are created on the fly, so setting a new attribute on one
    # has no long-term effect
    field_tester.test.field_z = 'foo'
    assert_raises(AttributeError, getattr, field_tester.test, 'field_z')
    assert 'field_z' not in field_tester._model_data


def test_defaults_not_shared():
    class FieldTester(object):
        __metaclass__ = ModelMetaclass

        field_a = List(scope=Scope.settings)

        def __init__(self, model_data):
            self._model_data = model_data

    field_tester_a = FieldTester({})
    field_tester_b = FieldTester({})

    field_tester_a.field_a.append(1)
    assert_equals([], field_tester_b.field_a)


def test_field_serialization():

    class CustomField(ModelType):
        def from_json(self, value):
            return value['value']

        def to_json(self, value):
            return {'value': value}

    class FieldTester(object):
        __metaclass__ = ModelMetaclass

        field = CustomField()

        def __init__(self, model_data):
            self._model_data = model_data

    field_tester = FieldTester({
        'field': {'value': 4}
    })

    assert_equals(4, field_tester.field)
    field_tester.field = 5
    assert_equals({'value': 5}, field_tester._model_data['field'])


def test_class_tags():
    xblock = XBlock(None, None)
    assert_equals(xblock._class_tags, set())

    class Sub1Block(XBlock):
        pass

    sub1block = Sub1Block(None, None)
    assert_equals(sub1block._class_tags, set())

    @XBlock.tag("cat dog")
    class Sub2Block(Sub1Block):
        pass

    sub2block = Sub2Block(None, None)
    assert_equals(sub2block._class_tags, set(["cat", "dog"]))

    class Sub3Block(Sub2Block):
        pass

    sub3block = Sub3Block(None, None)
    assert_equals(sub3block._class_tags, set(["cat", "dog"]))

    @XBlock.tag("mixin")
    class MixinBlock(XBlock):
        pass

    class Sub4Block(MixinBlock, Sub3Block):
        pass

    sub4block = Sub4Block(None, None)
    assert_equals(sub4block._class_tags, set(["cat", "dog", "mixin"]))


def test_loading_tagged_classes():

    @XBlock.tag("thetag")
    class HasTag1(XBlock):
        pass

    class HasTag2(HasTag1):
        pass

    class HasntTag(XBlock):
        pass

    the_classes = [('hastag1', HasTag1), ('hastag2', HasTag2), ('hasnttag', HasntTag)]
    tagged_classes = [('hastag1', HasTag1), ('hastag2', HasTag2)]
    with patch('xblock.core.XBlock.load_classes', return_value=the_classes):
        assert_equals(set(XBlock.load_tagged_classes('thetag')), set(tagged_classes))
