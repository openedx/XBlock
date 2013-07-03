"""Tests the fundamentals of XBlocks, including - but not limited to -
metaclassing, field access, caching, serialization, and bulk saves."""
# Allow accessing protected members for testing purposes
# pylint: disable=W0212
from mock import patch, MagicMock
# Nose redefines assert_equal and assert_not_equal
# pylint: disable=E0611
from nose.tools import assert_in, assert_equals, assert_raises, \
    assert_not_equals
# pylint: enable=E0611
from datetime import datetime

from xblock.core import Boolean, ChildrenModelMetaclass, Integer, \
    KeyValueMultiSaveError, List, ModelMetaclass, ModelType, \
    Namespace, NamespacesMetaclass, Scope, String, XBlock, XBlockSaveError


def test_model_metaclass():
    class ModelMetaclassTester(object):
        """Toy class for ModelMetaclass testing"""
        __metaclass__ = ModelMetaclass

        field_a = Integer(scope=Scope.settings)
        field_b = Integer(scope=Scope.content)

        def __init__(self, model_data):
            self._model_data = model_data

    class ChildClass(ModelMetaclassTester):
        """Toy class for ModelMetaclass testing"""
        pass

    # `ModelMetaclassTester` and `ChildClass` both obtain the `fields` attribute
    # from the `ModelMetaclass`. Since this is not understood by static analysis,
    # silence this error for the duration of this test.
    # pylint: disable=E1101
    assert hasattr(ModelMetaclassTester, 'field_a')
    assert hasattr(ModelMetaclassTester, 'field_b')

    assert_in(ModelMetaclassTester.field_a, ModelMetaclassTester.fields)
    assert_in(ModelMetaclassTester.field_b, ModelMetaclassTester.fields)

    assert hasattr(ChildClass, 'field_a')
    assert hasattr(ChildClass, 'field_b')

    assert_in(ChildClass.field_a, ChildClass.fields)
    assert_in(ChildClass.field_b, ChildClass.fields)


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
    assert_in(ChildClass.field_a, ChildClass.fields)

    assert hasattr(GrandchildClass, 'field_a')
    assert_in(GrandchildClass.field_a, GrandchildClass.fields)


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


def test_field_access():
    class FieldTester(XBlock):
        """Test XBlock for field access testing"""
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
    # Check that values that are deleted are restored to their default values
    class FieldTester(XBlock):
        """Test XBlock for field access testing"""
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
    # Check that values are correctly converted to and from json in accessors.

    class Date(ModelType):
        """Date needs to convert between JSON-compatible persistence and a datetime object"""
        def from_json(self, field):
            """Convert a string representation of a date to a datetime object"""
            return datetime.strptime(field, "%m/%d/%Y")

        def to_json(self, value):
            """Convert a datetime object to a string"""
            return value.strftime("%m/%d/%Y")

    class FieldTester(object):
        """Toy class for ModelMetaclass and field access testing"""
        __metaclass__ = ModelMetaclass

        field_a = Date(scope=Scope.settings)
        field_b = Date(scope=Scope.content, default=datetime(2013, 4, 1))

        def __init__(self, model_data):
            self._model_data = model_data
            self._dirty_fields = set()

    field_tester = FieldTester({})

    # Check initial values
    assert_equals(None, field_tester.field_a)
    assert_equals(datetime(2013, 4, 1), field_tester.field_b)

    # Test no default specified
    field_tester.field_a = datetime(2013, 1, 2)
    assert_equals(datetime(2013, 1, 2), field_tester.field_a)
    del field_tester.field_a
    assert_equals(None, field_tester.field_a)

    # Test default explicitly specified
    field_tester.field_b = datetime(2013, 1, 2)
    assert_equals(datetime(2013, 1, 2), field_tester.field_b)
    del field_tester.field_b
    assert_equals(datetime(2013, 4, 1), field_tester.field_b)


class TestNamespace(Namespace):
    """Toy class for namespace testing"""
    field_x = List(scope=Scope.content)
    field_y = String(scope=Scope.user_state, default="default_value")


# pylint: disable=W0613
@patch('xblock.core.Namespace.load_classes', return_value=[('test', TestNamespace)])
def test_namespace_metaclass(mock_load_classes):
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


@patch('xblock.core.Namespace.load_classes', return_value=[('test', TestNamespace)])
def test_namespace_field_access(mock_load_classes):

    class FieldTester(XBlock):
        """Test XBlock for field access testing"""
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

    # `test` is a namespace provided by the @patch method above, which ultimately
    # comes from the NamespacesMetaclass. Since this is not understood by static
    # analysis, silence this error for the duration of this test.
    # pylint: disable=E1101

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

    with assert_raises(AttributeError):
        getattr(field_tester.test, 'field_z')
    with assert_raises(AttributeError):
        delattr(field_tester.test, 'field_z')

    # Namespaces are created on the fly, so setting a new attribute on one
    # has no long-term effect
    field_tester.test.field_z = 'foo'
    with assert_raises(AttributeError):
        getattr(field_tester.test, 'field_z')
    assert 'field_z' not in field_tester._model_data
# pylint: enable=W0613


def test_defaults_not_shared():
    class FieldTester(object):
        """Toy class for ModelMetaclass and field access testing"""
        __metaclass__ = ModelMetaclass

        field_a = List(scope=Scope.settings)

        def __init__(self, model_data):
            self._model_data = model_data
            self._dirty_fields = set()

    field_tester_a = FieldTester({})
    field_tester_b = FieldTester({})

    field_tester_a.field_a.append(1)
    assert_equals([], field_tester_b.field_a)


def test_object_identity():
    # Check that values that are modified are what is returned
    class FieldTester(object):
        """Toy class for ModelMetaclass and field access testing"""
        __metaclass__ = ModelMetaclass

        field_a = List(scope=Scope.settings)

        def __init__(self, model_data):
            self._model_data = model_data
            self._dirty_fields = set()

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
    # Test that values cached for one instance do not appear on another
    class FieldTester(object):
        """Toy class for ModelMetaclass and field access testing"""
        __metaclass__ = ModelMetaclass

        field_a = List(scope=Scope.settings)

        def __init__(self, model_data):
            self._model_data = model_data
            self._dirty_fields = set()

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
    # Some ModelTypes can define their own serialization mechanisms.
    # This test ensures that we are using them properly.

    class CustomField(ModelType):
        """
        Specifiy a custom field that defines its own serialization
        """
        def from_json(self, value):
            return value['value']

        def to_json(self, value):
            return {'value': value}

    class FieldTester(XBlock):
        """Test XBlock for field serialization testing"""
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
        """Toy XBlock"""
        pass

    sub1block = Sub1Block(None, None)
    assert_equals(sub1block._class_tags, set())

    @XBlock.tag("cat dog")
    class Sub2Block(Sub1Block):
        """Toy XBlock"""
        pass

    sub2block = Sub2Block(None, None)
    assert_equals(sub2block._class_tags, set(["cat", "dog"]))

    class Sub3Block(Sub2Block):
        """Toy XBlock"""
        pass

    sub3block = Sub3Block(None, None)
    assert_equals(sub3block._class_tags, set(["cat", "dog"]))

    @XBlock.tag("mixin")
    class MixinBlock(XBlock):
        """Toy XBlock"""
        pass

    class Sub4Block(MixinBlock, Sub3Block):
        """Toy XBlock"""
        pass

    sub4block = Sub4Block(None, None)
    assert_equals(sub4block._class_tags, set(["cat", "dog", "mixin"]))


def test_loading_tagged_classes():

    @XBlock.tag("thetag")
    class HasTag1(XBlock):
        """Toy XBlock"""
        pass

    class HasTag2(HasTag1):
        """Toy XBlock"""
        pass

    class HasntTag(XBlock):
        """Toy XBlock"""
        pass

    the_classes = [('hastag1', HasTag1), ('hastag2', HasTag2), ('hasnttag', HasntTag)]
    tagged_classes = [('hastag1', HasTag1), ('hastag2', HasTag2)]
    with patch('xblock.core.XBlock.load_classes', return_value=the_classes):
        assert_equals(set(XBlock.load_tagged_classes('thetag')), set(tagged_classes))


def test_field_name_defaults():
    # Tests field display name default values
    attempts = Integer()
    attempts._name = "max_problem_attempts"
    assert_equals('max_problem_attempts', attempts.display_name)

    class NamespaceTestClass(Namespace):
        """Toy class for Namespace testing"""
        field_x = List()

    assert_equals("field_x", NamespaceTestClass.field_x.display_name)


def test_field_display_name():
    attempts = Integer(display_name='Maximum Problem Attempts')
    attempts._name = "max_problem_attempts"
    assert_equals("Maximum Problem Attempts", attempts.display_name)

    boolean_field = Boolean(display_name="boolean field")
    assert_equals("boolean field", boolean_field.display_name)

    class NamespaceTestClass(Namespace):
        """Toy class for Namespace testing"""
        field_x = List(display_name="Field Known as X")

    assert_equals("Field Known as X", NamespaceTestClass.field_x.display_name)


def test_values():
    # static return value
    field_values = ['foo', 'bar']
    test_field = String(values=field_values)
    assert_equals(field_values, test_field.values)

    # function to generate values
    test_field = String(values=lambda: [1, 4])
    assert_equals([1, 4], test_field.values)

    # default if nothing specified
    assert_equals(None, String().values)


def test_values_boolean():
    # Test Boolean, which has values defined
    test_field = Boolean()
    assert_equals(
        ({'display_name': "True", "value": True}, {'display_name': "False", "value": False}),
        test_field.values
    )


def test_values_dict():
    # Test that the format expected for integers is allowed
    test_field = Integer(values={"min": 1, "max": 100})
    assert_equals({"min": 1, "max": 100}, test_field.values)


def setup_save_failure(update_method):
    """
    Set up tests for when there's a save error in the underlying KeyValueStore
    """
    model_data = MagicMock(spec=dict)
    model_data.__getitem__ = lambda self, name: [name]

    model_data.update = update_method

    class FieldTester(XBlock):
        """
        Test XBlock with three fields
        """
        field_a = Integer(scope=Scope.settings)
        field_b = Integer(scope=Scope.content, default=10)
        field_c = Integer(scope=Scope.user_state, default='field c')

    field_tester = FieldTester(MagicMock(), model_data)
    return field_tester


def test_xblock_save_one():
    # Mimics a save failure when we only manage to save one of the values

    # pylint: disable=W0613
    def fake_update(*args, **kwargs):
        """Mock update method that throws a KeyValueMultiSaveError indicating
           that only one field was correctly saved."""
        other_dict = args[0]
        raise KeyValueMultiSaveError(other_dict.keys()[0])
    # pylint: enable=W0613

    field_tester = setup_save_failure(fake_update)

    field_tester.field_a = 20
    field_tester.field_b = 40

    with assert_raises(XBlockSaveError) as save_error:
        # This call should raise an XBlockSaveError
        field_tester.save()

        # Verify that the correct data is getting stored by the error
        assert_equals(len(save_error.saved_fields), 1)
        assert_equals(len(save_error.dirty_fields), 1)


def test_xblock_save_failure_none():
    # Mimics a save failure when we don't manage to save any of the values

    # pylint: disable=W0613
    def fake_update(*args, **kwargs):
        """Mock update method that throws a KeyValueMultiSaveError indicating
           that no fields were correctly saved."""
        raise KeyValueMultiSaveError([])
    # pylint: enable=W0613

    field_tester = setup_save_failure(fake_update)
    field_tester.field_a = 20
    field_tester.field_b = 30
    field_tester.field_c = "hello world"

    with assert_raises(XBlockSaveError) as save_error:
        # This call should raise an XBlockSaveError
        field_tester.save()

        # Verify that the correct data is getting stored by the error
        assert_equals(len(save_error.saved_fields), 0)
        assert_equals(len(save_error.dirty_fields), 3)


def test_xblock_write_then_delete():
    # Tests that setting a field, then deleting it later, doesn't
    # cause an erroneous write of the originally set value after
    # a call to `XBlock.save`
    class FieldTester(XBlock):
        """Test XBlock with two fields"""
        field_a = Integer(scope=Scope.settings)
        field_b = Integer(scope=Scope.content, default=10)

    field_tester = FieldTester(MagicMock(), {'field_a': 5})
    # verify that the fields have been set
    assert_equals(5, field_tester.field_a)
    assert_equals(10, field_tester.field_b)

    # Set the fields to new values
    field_tester.field_a = 20
    field_tester.field_b = 20

    # Additionally assert that in the model data, we cached the value of field_a
    # (field_b has a default value, so it will not be present in the cache)
    assert_equals(len(field_tester._model_data), 1)
    assert_in('field_a', field_tester._model_data)

    # Before saving, delete all the fields
    del field_tester.field_a
    del field_tester.field_b

    # Assert that we're now finding the right cached values
    assert_equals(None, field_tester.field_a)
    assert_equals(10, field_tester.field_b)

    # Additionally assert that in the model data, we don't have any values set
    assert_equals(len(field_tester._model_data), 0)
    # Perform explicit save
    field_tester.save()

    # Assert that we're now finding the right cached values
    assert_equals(None, field_tester.field_a)
    assert_equals(10, field_tester.field_b)

    # Additionally assert that in the model data, we don't have any values set
    assert_equals(len(field_tester._model_data), 0)
