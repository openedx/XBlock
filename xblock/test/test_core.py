from mock import patch, MagicMock
from nose.tools import assert_in, assert_equals, assert_raises, assert_not_equals
from datetime import datetime

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
    class FieldTester(XBlock):
        __metaclass__ = ModelMetaclass

        field_a = Integer(scope=Scope.settings)
        field_b = Integer(scope=Scope.content, default=10)
        field_c = Integer(scope=Scope.user_state, default='field c')

    field_tester = FieldTester(MagicMock(), {'field_a': 5, 'field_x': 15})

    # verify that the fields have been set
    assert_equals(5, field_tester.field_a)
    assert_equals(10, field_tester.field_b)
    assert_equals('field c', field_tester.field_c)
    assert not hasattr(field_tester, 'field_x')

    # set one of the fields
    field_tester.field_a = 20
    # save the XBlock
    field_tester.save()
    # verify that the fields have been updated correctly
    assert_equals(20, field_tester._model_data['field_a'])
    assert_equals(10, field_tester.field_b)
    assert_equals('field c', field_tester.field_c)

    del field_tester.field_a
    assert_equals(None, field_tester.field_a)
    assert hasattr(FieldTester, 'field_a')


def test_list_field_access():
    '''Check that values that are deleted are restored to their default values'''
    class FieldTester(XBlock):
        __metaclass__ = ModelMetaclass

        field_a = List(scope=Scope.settings)
        field_b = List(scope=Scope.content, default=[1, 2, 3])

    field_tester = FieldTester(MagicMock(), {})

    # Check initial values
    assert_equals([], field_tester.field_a)
    assert_equals([1, 2, 3], field_tester.field_b)

    # Test no default specified
    field_tester.field_a.append(1)
    assert_equals([1], field_tester.field_a)
    del field_tester.field_a
    assert_equals([], field_tester.field_a)

    # Test default explicitly specified
    field_tester.field_b.append(4)
    assert_equals([1, 2, 3, 4], field_tester.field_b)
    del field_tester.field_b
    assert_equals([1, 2, 3], field_tester.field_b)


def test_json_field_access():
    '''Check that values are correctly converted to and from json in accessors.'''

    class Date(ModelType):
        '''Date needs to convert between JSON-compatible persistence and a datetime object'''
        def from_json(self, field):
            """Convert a string representation of a date to a datetime object"""
            return datetime.strptime(field, "%m/%d/%Y")

        def to_json(self, value):
            """Convert a datetime object to a string"""
            return value.strftime("%m/%d/%Y")

    class FieldTester(object):
        __metaclass__ = ModelMetaclass

        field_a = Date(scope=Scope.settings)
        field_b = Date(scope=Scope.content, default=datetime(2013,4,1))

        def __init__(self, model_data):
            self._model_data = model_data

    field_tester = FieldTester({})

    # Check initial values
    assert_equals(None, field_tester.field_a)
    assert_equals(datetime(2013,4,1), field_tester.field_b)

    # Test no default specified
    field_tester.field_a = datetime(2013,1,2)
    assert_equals(datetime(2013,1,2), field_tester.field_a)
    del field_tester.field_a
    assert_equals(None, field_tester.field_a)

    # Test default explicitly specified
    field_tester.field_b = datetime(2013,1,2)
    assert_equals(datetime(2013,1,2), field_tester.field_b)
    del field_tester.field_b
    assert_equals(datetime(2013,4,1), field_tester.field_b)


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

    class FieldTester(XBlock):

        field_a = Integer(scope=Scope.settings)
        field_b = Integer(scope=Scope.content, default=10)
        field_c = Integer(scope=Scope.user_state, default='field c')

    field_tester = FieldTester(
        MagicMock(),
        {
            'field_a': 5,
            'field_x': [1, 2, 3],
        }
    )

    assert_equals(5, field_tester.field_a)
    assert_equals(10, field_tester.field_b)
    assert_equals('field c', field_tester.field_c)
    assert_equals([1, 2, 3], field_tester.test.field_x)
    assert_equals('default_value', field_tester.test.field_y)

    field_tester.test.field_x = ['a', 'b']
    field_tester.save()
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


def test_object_identity():
    '''Check that values that are modified are what is returned'''
    class FieldTester(object):
        __metaclass__ = ModelMetaclass

        field_a = List(scope=Scope.settings)

        def __init__(self, model_data):
            self._model_data = model_data

    # Make sure that model_data always returns a different object
    # each time it's actually queried, so that the caching is
    # doing the work to maintain object identity.
    model_data = MagicMock(spec=dict)
    model_data.__getitem__ = lambda self, name: [name]
    field_tester = FieldTester(model_data)

    value = field_tester.field_a
    assert_equals(value, field_tester.field_a)

    # Changing the field in place matches a previously fetched value
    field_tester.field_a.append(1)
    assert_equals(value, field_tester.field_a)

    # Changing the previously-fetched value also changes the value returned by the field:
    value.append(2)
    assert_equals(value, field_tester.field_a)

    # Deletion restores the default value.  In the case of a List with
    # no default defined, this is the empty list.
    del field_tester.field_a
    assert_equals([], field_tester.field_a)


def test_caching_is_per_instance():
    '''Test that values cached for one instance do not appear on another'''
    class FieldTester(object):
        __metaclass__ = ModelMetaclass

        field_a = List(scope=Scope.settings)

        def __init__(self, model_data):
            self._model_data = model_data

    model_data = MagicMock(spec=dict)
    model_data.__getitem__ = lambda self, name: [name]

    # Same model_data used in different objects should result
    # in separately-cached values, so that changing a value
    # in one instance doesn't affect values stored in others.
    field_tester_a = FieldTester(model_data)
    field_tester_b = FieldTester(model_data)
    value = field_tester_a.field_a
    assert_equals(value, field_tester_a.field_a)
    field_tester_a.field_a.append(1)
    assert_equals(value, field_tester_a.field_a)
    assert_not_equals(value, field_tester_b.field_a)


def test_field_serialization():
    """
    Some ModelTypes can define their own serialization mechanisms.

    This test ensures that we are using them properly.
    """

    class CustomField(ModelType):
        """
        Specifiy a custom field that defines its own serialization
        """
        def from_json(self, value):
            return value['value']

        def to_json(self, value):
            return {'value': value}

    class FieldTester(XBlock):
        field = CustomField()

    field_tester = FieldTester(
        MagicMock(),
        {
            'field': {'value': 4}
        }
    )

    assert_equals(4, field_tester.field)
    field_tester.field = 5
    field_tester.save()
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


def test_field_display_name_defaults():
    attempts = Integer()
    attempts._name = "max_problem_attempts"
    assert_equals('max_problem_attempts', attempts.display_name)

    class TestNamespace(Namespace):
        field_x = List()

    assert_equals("field_x", TestNamespace.field_x.display_name)


def test_field_display_name():
    attempts = Integer(display_name = 'Maximum Problem Attempts')
    attempts._name = "max_problem_attempts"
    assert_equals("Maximum Problem Attempts", attempts.display_name)

    boolean_field = Boolean(display_name= "boolean field")
    assert_equals("boolean field", boolean_field.display_name)

    class TestNamespace(Namespace):
        field_x = List(display_name="Field Known as X")

    assert_equals("Field Known as X", TestNamespace.field_x.display_name)


def test_values():
    # static return value
    field_values = ['foo', 'bar']
    test_field = String(values = field_values)
    assert_equals(field_values, test_field.values)

    # function to generate values
    test_field = String(values = lambda : [1, 4])
    assert_equals([1, 4], test_field.values)

    # default if nothing specified
    assert_equals(None, String().values)


def test_values_boolean():
    # Test Boolean, which has values defined
    test_field = Boolean()
    assert_equals(({'display_name': "True", "value": True}, {'display_name': "False", "value": False}), test_field.values)


def test_values_dict():
    # Test that the format expected for integers is allowed
    test_field = Integer(values={"min": 1, "max" : 100})
    assert_equals({"min": 1, "max" : 100}, test_field.values)
