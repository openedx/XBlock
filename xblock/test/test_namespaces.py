"""
Tests of the XBlock Namespaces functionality
"""

from mock import patch, MagicMock, Mock
# pylint: disable=E0611
from nose.tools import assert_in, assert_equals, assert_raises, assert_false
# pylint: enable=E0611

from xblock.core import XBlock
from xblock.fields import List, String, Scope, Integer
from xblock.namespaces import Namespace, NamespacesMetaclass
from xblock.test.tools import DictModel


class TestNamespace(Namespace):
    """Toy class for namespace testing"""
    field_w = List(scope=Scope.content)
    field_x = List(scope=Scope.content)
    field_y = String(scope=Scope.user_state, default="default_value")


@patch('xblock.namespaces.Namespace.load_classes', return_value=[('test', TestNamespace)])
def test_namespace_metaclass(_mock_load_classes):
    class TestClass(object):
        """Toy class for NamespacesMetaclass testing"""
        __metaclass__ = NamespacesMetaclass

    # `TestNamespace` obtains the `fields` attribute from the `NamespacesMetaclass`. Since this
    # is not understood by static analysis, silence this error for the duration of this test.
    # pylint: disable=E1101

    assert hasattr(TestClass, 'test')
    assert hasattr(TestClass.test, 'field_x')
    assert hasattr(TestClass.test, 'field_y')

    assert_in(TestNamespace.field_x, TestClass.test.fields)
    assert_in(TestNamespace.field_y, TestClass.test.fields)
    assert isinstance(TestClass.test, Namespace)


@patch('xblock.namespaces.Namespace.load_classes', return_value=[('test', TestNamespace)])
def test_namespace_field_access(_mock_load_classes):

    class FieldTester(XBlock):
        """Test XBlock for field access testing"""
        field_a = Integer(scope=Scope.settings)
        field_b = Integer(scope=Scope.content, default=10)
        field_c = Integer(scope=Scope.user_state, default='field c')

    model_data = DictModel({
        'field_a': 5,
        'field_x': [1, 2, 3],
    })
    field_tester = FieldTester(
        MagicMock(),
        model_data,
        Mock(),
    )

    # `test` is a namespace provided by the @patch method above, which ultimately
    # comes from the NamespacesMetaclass. Since this is not understood by static
    # analysis, silence this error for the duration of this test.
    # pylint: disable=E1101

    assert_equals(5, field_tester.field_a)
    assert_equals(10, field_tester.field_b)
    assert_equals('field c', field_tester.field_c)
    assert_equals([1, 2, 3], field_tester.test.field_x)
    assert_equals('default_value', field_tester.test.field_y)
    assert_equals([], field_tester.test.field_w)

    # Test setting namespaced fields
    field_tester.test.field_x = ['a', 'b']
    field_tester.save()

    assert_equals(['a', 'b'], model_data.get(field_tester, 'field_x'))

    # Test modifying mutable namespaced fields
    field_tester.test.field_x.insert(0, 'A')
    field_tester.test.field_w.extend(['new', 'elt'])
    # Before save, should get correct things out of the cache.
    assert_equals(['A', 'a', 'b'], field_tester.test.field_x)
    assert_equals(['new', 'elt'], field_tester.test.field_w)
    field_tester.save()
    # After save, new values should be reflected in the model_data
    assert_equals(['A', 'a', 'b'], model_data.get(field_tester, 'field_x'))
    assert_equals(['new', 'elt'], model_data.get(field_tester, 'field_w'))

    # Test deleting namespaced fields
    del field_tester.test.field_x
    assert_equals([], field_tester.test.field_x)

    with assert_raises(AttributeError):
        getattr(field_tester.test, 'field_z')
    with assert_raises(AttributeError):
        delattr(field_tester.test, 'field_z')

    # Namespaces are created on the fly, so setting a new attribute on one
    # has no long-term effect
    field_tester.test.field_z = 'foo'
    with assert_raises(AttributeError):
        getattr(field_tester.test, 'field_z')
    assert_false(model_data.has(field_tester, 'field_z'))
