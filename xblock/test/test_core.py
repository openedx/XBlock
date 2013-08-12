"""Tests the fundamentals of XBlocks, including - but not limited to -
metaclassing, field access, caching, serialization, and bulk saves."""
# Allow accessing protected members for testing purposes
# pylint: disable=W0212
from mock import patch, MagicMock, Mock
# Nose redefines assert_equal and assert_not_equal
# pylint: disable=E0611
from nose.tools import assert_in, assert_equals, assert_raises, \
    assert_not_equals, assert_false
# pylint: enable=E0611
from datetime import datetime

from xblock.core import XBlock
from xblock.exceptions import XBlockSaveError, KeyValueMultiSaveError
from xblock.fields import ChildrenModelMetaclass, Dict, Float, \
    Integer, List, ModelMetaclass, Field, \
    Scope
from xblock.fields import FieldData
from xblock.test.tools import DictModel


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
        float_a = Float(scope=Scope.settings, default=5.8)
        float_b = Float(scope=Scope.settings)

    field_tester = FieldTester(MagicMock(), DictModel({'field_a': 5, 'float_a': 6.1, 'field_x': 15}), Mock())
    # Verify that the fields have been set
    assert_equals(5, field_tester.field_a)
    assert_equals(10, field_tester.field_b)
    assert_equals('field c', field_tester.field_c)
    assert_equals(6.1, field_tester.float_a)
    assert_equals(None, field_tester.float_b)
    assert not hasattr(field_tester, 'field_x')

    # Set two of the fields.
    field_tester.field_a = 20
    field_tester.float_a = 20.5
    # field_a should be updated in the cache, but /not/ in the underlying db.
    assert_equals(20, field_tester.field_a)
    assert_equals(20.5, field_tester.float_a)
    assert_equals(5, field_tester._field_data.get(field_tester, 'field_a'))
    assert_equals(6.1, field_tester._field_data.get(field_tester, 'float_a'))
    # save the XBlock
    field_tester.save()
    # verify that the fields have been updated correctly
    assert_equals(20, field_tester.field_a)
    assert_equals(20.5, field_tester.float_a)
    # Now, field_a should be updated in the underlying db
    assert_equals(20, field_tester._field_data.get(field_tester, 'field_a'))
    assert_equals(20.5, field_tester._field_data.get(field_tester, 'float_a'))
    assert_equals(10, field_tester.field_b)
    assert_equals('field c', field_tester.field_c)
    assert_equals(None, field_tester.float_b)

    # Deletes happen immediately (do not require a save)
    del field_tester.field_a
    del field_tester.float_a

    # After delete, we should find default values in the cache
    assert_equals(None, field_tester.field_a)
    assert_equals(5.8, field_tester.float_a)
    # But the fields should not actually be present in the underlying kvstore
    assert_equals("Not Present", field_tester._field_data.get(field_tester, 'field_a', "Not Present"))
    assert_equals("Not Present", field_tester._field_data.get(field_tester, 'float_a', "Not Present"))


def test_list_field_access():
    # Check that lists are correctly saved when not directly set
    class FieldTester(XBlock):
        """Test XBlock for field access testing"""
        field_a = List(scope=Scope.settings)
        field_b = List(scope=Scope.content, default=[1, 2, 3])
        field_c = List(scope=Scope.content, default=[4, 5, 6])
        field_d = List(scope=Scope.settings)

    field_tester = FieldTester(MagicMock(), DictModel({'field_a': [200], 'field_b': [11, 12, 13]}), Mock())

    # Check initial values have been set properly
    assert_equals([200], field_tester.field_a)
    assert_equals([11, 12, 13], field_tester.field_b)
    assert_equals([4, 5, 6], field_tester.field_c)
    assert_equals([], field_tester.field_d)

    # Update the fields
    field_tester.field_a.append(1)
    field_tester.field_b.append(14)
    field_tester.field_c.append(7)
    field_tester.field_d.append(1)

    # The fields should be update in the cache, but /not/ in the underlying kvstore.
    assert_equals([200, 1], field_tester.field_a)
    assert_equals([11, 12, 13, 14], field_tester.field_b)
    assert_equals([4, 5, 6, 7], field_tester.field_c)
    assert_equals([1], field_tester.field_d)

    # Examine model data directly
    ## Caveat: there's not a clean way to copy the originally provided values for `field_a` and `field_b`
    ## when we instantiate the XBlock. So, the values for those two in both `_field_data` and `_field_data_cache`
    ## point at the same object. Thus, `field_a` and `field_b` actually have the correct values in
    ## `_field_data` right now. `field_c` does not, because it has never been written to the `_field_data`.
    assert_false(field_tester._field_data.has(field_tester, 'field_c'))
    assert_false(field_tester._field_data.has(field_tester, 'field_d'))

    # save the XBlock
    field_tester.save()

    # verify that the fields have been updated correctly
    assert_equals([200, 1], field_tester.field_a)
    assert_equals([11, 12, 13, 14], field_tester.field_b)
    assert_equals([4, 5, 6, 7], field_tester.field_c)
    assert_equals([1], field_tester.field_d)
    # Now, the fields should be updated in the underlying kvstore

    assert_equals([200, 1], field_tester._field_data.get(field_tester, 'field_a'))
    assert_equals([11, 12, 13, 14], field_tester._field_data.get(field_tester, 'field_b'))
    assert_equals([4, 5, 6, 7], field_tester._field_data.get(field_tester, 'field_c'))
    assert_equals([1], field_tester._field_data.get(field_tester, 'field_d'))


def test_mutable_none_values():
    # Check that fields with values intentionally set to None
    # save properly.
    class FieldTester(XBlock):
        """Test XBlock for field access testing"""
        field_a = List(scope=Scope.settings)
        field_b = List(scope=Scope.settings)
        field_c = List(scope=Scope.content, default=None)

    field_tester = FieldTester(MagicMock(), DictModel({'field_a': None}), Mock())
    # Set fields b & c to None
    field_tester.field_b = None
    field_tester.field_c = None
    # Save our changes
    field_tester.save()

    # Access the fields without modifying them. Want to call `__get__`, not `__set__`,
    # because `__get__` marks only mutable fields as dirty.
    _test_get = field_tester.field_a
    _test_get = field_tester.field_b
    _test_get = field_tester.field_c

    # The previous accesses will mark the fields as dirty (via __get__)
    assert_equals(len(field_tester._dirty_fields), 3)  # pylint: disable=W0212

    # However, the fields should not ACTUALLY be marked as fields that need to be saved.
    assert_equals(len(field_tester._get_fields_to_save()), 0)  # pylint: disable=W0212


def test_dict_field_access():
    # Check that dicts are correctly saved when not directly set
    class FieldTester(XBlock):
        """Test XBlock for field access testing"""
        field_a = Dict(scope=Scope.settings)
        field_b = Dict(scope=Scope.content, default={'a': 1, 'b': 2, 'c': 3})
        field_c = Dict(scope=Scope.content, default={'a': 4, 'b': 5, 'c': 6})
        field_d = Dict(scope=Scope.settings)

    field_tester = FieldTester(
        MagicMock(),
        DictModel({
            'field_a': {'a': 200},
            'field_b': {'a': 11, 'b': 12, 'c': 13}
        }),
        Mock()
    )

    # Check initial values have been set properly
    assert_equals({'a': 200}, field_tester.field_a)
    assert_equals({'a': 11, 'b': 12, 'c': 13}, field_tester.field_b)
    assert_equals({'a': 4, 'b': 5, 'c': 6}, field_tester.field_c)
    assert_equals({}, field_tester.field_d)

    # Update the fields
    field_tester.field_a['a'] = 250
    field_tester.field_b['d'] = 14
    field_tester.field_c['a'] = 0
    field_tester.field_d['new'] = 'value'

    # The fields should be update in the cache, but /not/ in the underlying kvstore.
    assert_equals({'a': 250}, field_tester.field_a)
    assert_equals({'a': 11, 'b': 12, 'c': 13, 'd': 14}, field_tester.field_b)
    assert_equals({'a': 0, 'b': 5, 'c': 6}, field_tester.field_c)
    assert_equals({'new': 'value'}, field_tester.field_d)

    # Examine model data directly
    ## Caveat: there's not a clean way to copy the originally provided values for `field_a` and `field_b`
    ## when we instantiate the XBlock. So, the values for those two in both `_field_data` and `_field_data_cache`
    ## point at the same object. Thus, `field_a` and `field_b` actually have the correct values in
    ## `_field_data` right now. `field_c` does not, because it has never been written to the `_field_data`.
    assert_false(field_tester._field_data.has(field_tester, 'field_c'))
    assert_false(field_tester._field_data.has(field_tester, 'field_d'))

    field_tester.save()
    # verify that the fields have been updated correctly
    assert_equals({'a': 250}, field_tester.field_a)
    assert_equals({'a': 11, 'b': 12, 'c': 13, 'd': 14}, field_tester.field_b)
    assert_equals({'a': 0, 'b': 5, 'c': 6}, field_tester.field_c)
    assert_equals({'new': 'value'}, field_tester.field_d)

    # Now, the fields should be updated in the underlying kvstore
    assert_equals({'a': 250}, field_tester._field_data.get(field_tester, 'field_a'))
    assert_equals({'a': 11, 'b': 12, 'c': 13, 'd': 14}, field_tester._field_data.get(field_tester, 'field_b'))
    assert_equals({'a': 0, 'b': 5, 'c': 6}, field_tester._field_data.get(field_tester, 'field_c'))
    assert_equals({'new': 'value'}, field_tester._field_data.get(field_tester, 'field_d'))


def test_default_values():
    # Check that values that are deleted are restored to their default values
    class FieldTester(XBlock):
        """Test XBlock for field access testing"""
        dic1 = Dict(scope=Scope.settings)
        dic2 = Dict(scope=Scope.content, default={'a': 1, 'b': 2, 'c': 3})
        list1 = List(scope=Scope.settings)
        list2 = List(scope=Scope.content, default=[1, 2, 3])

    field_tester = FieldTester(MagicMock(), DictModel({'dic1': {'a': 200}, 'list1': ['a', 'b']}), Mock())
    assert_equals({'a': 200}, field_tester.dic1)
    assert_equals({'a': 1, 'b': 2, 'c': 3}, field_tester.dic2)
    assert_equals(['a', 'b'], field_tester.list1)
    assert_equals([1, 2, 3], field_tester.list2)
    # Modify the fields & save
    field_tester.dic1.popitem()
    field_tester.dic2.clear()
    field_tester.list1.pop()
    field_tester.list2.remove(2)
    field_tester.save()

    # Test that after save, new values exist and fields are present in the underlying kvstore
    assert_equals({}, field_tester.dic1)
    assert_equals({}, field_tester.dic2)
    assert_equals(['a'], field_tester.list1)
    assert_equals([1, 3], field_tester.list2)
    for fname in ['dic1', 'dic2', 'list1', 'list2']:
        assert(field_tester._field_data.has(field_tester, fname))

    # Now delete each field
    del field_tester.dic1
    del field_tester.dic2
    del field_tester.list1
    del field_tester.list2

    # Test that default values return after a delete, but fields not actually
    # in the underlying kvstore

    # Defaults not explicitly set
    assert_equals({}, field_tester.dic1)
    assert_equals([], field_tester.list1)
    # Defaults explicitly set
    assert_equals({'a': 1, 'b': 2, 'c': 3}, field_tester.dic2)
    assert_equals([1, 2, 3], field_tester.list2)
    for fname in ['dic1', 'dic2', 'list1', 'list2']:
        assert_false(field_tester._field_data.has(field_tester, fname))


def test_json_field_access():
    # Check that values are correctly converted to and from json in accessors.

    class Date(Field):
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

        def __init__(self, field_data):
            self._field_data = field_data
            self._dirty_fields = set()

    field_tester = FieldTester(DictModel({}))

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


def test_defaults_not_shared():
    class FieldTester(XBlock):
        """Toy class for field access testing"""

        field_a = List(scope=Scope.settings)

    field_tester_a = FieldTester(MagicMock(), DictModel({}), Mock())
    field_tester_b = FieldTester(MagicMock(), DictModel({}), Mock())

    field_tester_a.field_a.append(1)
    assert_equals([1], field_tester_a.field_a)
    assert_equals([], field_tester_b.field_a)
    # Write out the data
    field_tester_a.save()
    # Double check that write didn't do something weird
    assert_equals([1], field_tester_a.field_a)
    assert_equals([], field_tester_b.field_a)


def test_object_identity():
    # Check that values that are modified are what is returned
    class FieldTester(object):
        """Toy class for ModelMetaclass and field access testing"""
        __metaclass__ = ModelMetaclass

        field_a = List(scope=Scope.settings)

        def __init__(self, field_data):
            self._field_data = field_data
            self._dirty_fields = set()

    # Make sure that field_data always returns a different object
    # each time it's actually queried, so that the caching is
    # doing the work to maintain object identity.
    field_data = MagicMock(spec=FieldData)
    field_data.get = lambda block, name, default=None: [name]  # pylint: disable=C0322
    field_tester = FieldTester(field_data)

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

        def __init__(self, field_data):
            self._field_data = field_data
            self._dirty_fields = set()

    field_data = MagicMock(spec=FieldData)
    field_data.get = lambda block, name, default=None: [name]  # pylint: disable=C0322

    # Same field_data used in different objects should result
    # in separately-cached values, so that changing a value
    # in one instance doesn't affect values stored in others.
    field_tester_a = FieldTester(field_data)
    field_tester_b = FieldTester(field_data)
    value = field_tester_a.field_a
    assert_equals(value, field_tester_a.field_a)
    field_tester_a.field_a.append(1)
    assert_equals(value, field_tester_a.field_a)
    assert_not_equals(value, field_tester_b.field_a)


def test_field_serialization():
    # Some Fields can define their own serialization mechanisms.
    # This test ensures that we are using them properly.

    class CustomField(Field):
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
        DictModel({
            'field': {'value': 4}
        }),
        Mock(),
    )

    assert_equals(4, field_tester.field)
    field_tester.field = 5
    field_tester.save()
    assert_equals({'value': 5}, field_tester._field_data.get(field_tester, 'field'))


def test_class_tags():
    xblock = XBlock(None, None, None)
    assert_equals(xblock._class_tags, set())

    class Sub1Block(XBlock):
        """Toy XBlock"""
        pass

    sub1block = Sub1Block(None, None, None)
    assert_equals(sub1block._class_tags, set())

    @XBlock.tag("cat dog")
    class Sub2Block(Sub1Block):
        """Toy XBlock"""
        pass

    sub2block = Sub2Block(None, None, None)
    assert_equals(sub2block._class_tags, set(["cat", "dog"]))

    class Sub3Block(Sub2Block):
        """Toy XBlock"""
        pass

    sub3block = Sub3Block(None, None, None)
    assert_equals(sub3block._class_tags, set(["cat", "dog"]))

    @XBlock.tag("mixin")
    class MixinBlock(XBlock):
        """Toy XBlock"""
        pass

    class Sub4Block(MixinBlock, Sub3Block):
        """Toy XBlock"""
        pass

    sub4block = Sub4Block(None, None, None)
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



def setup_save_failure(set_many):
    """
    Set up tests for when there's a save error in the underlying KeyValueStore
    """
    field_data = MagicMock(spec=FieldData)
    field_data.get = lambda block, name, default=None: 99  # pylint: disable=C0322

    field_data.set_many = set_many

    class FieldTester(XBlock):
        """
        Test XBlock with three fields
        """
        field_a = Integer(scope=Scope.settings)
        field_b = Integer(scope=Scope.content, default=10)
        field_c = Integer(scope=Scope.user_state, default='field c')

    field_tester = FieldTester(MagicMock(), field_data, Mock())
    return field_tester


def test_xblock_save_one():
    # Mimics a save failure when we only manage to save one of the values

    # Pylint, please allow this method to accept arguments.
    # pylint: disable=W0613
    def fake_set_many(block, update_dict):
        """Mock update method that throws a KeyValueMultiSaveError indicating
           that only one field was correctly saved."""
        raise KeyValueMultiSaveError([update_dict.keys()[0]])
    # pylint: enable=W0613

    field_tester = setup_save_failure(fake_set_many)

    field_tester.field_a = 20
    field_tester.field_b = 40
    field_tester.field_c = 60

    with assert_raises(XBlockSaveError) as save_error:
        # This call should raise an XBlockSaveError
        field_tester.save()

    # Verify that the correct data is getting stored by the error
    assert_equals(len(save_error.exception.saved_fields), 1)
    assert_equals(len(save_error.exception.dirty_fields), 2)


def test_xblock_save_failure_none():
    # Mimics a save failure when we don't manage to save any of the values

    # Pylint, please allow this method to accept arguments.
    # pylint: disable=W0613
    def fake_set_many(block, update_dict):
        """Mock update method that throws a KeyValueMultiSaveError indicating
           that no fields were correctly saved."""
        raise KeyValueMultiSaveError([])
    # pylint: enable=W0613

    field_tester = setup_save_failure(fake_set_many)
    field_tester.field_a = 20
    field_tester.field_b = 30
    field_tester.field_c = "hello world"

    with assert_raises(XBlockSaveError) as save_error:
        # This call should raise an XBlockSaveError
        field_tester.save()

    # Verify that the correct data is getting stored by the error
    assert_equals(len(save_error.exception.saved_fields), 0)
    assert_equals(len(save_error.exception.dirty_fields), 3)


def test_xblock_write_then_delete():
    # Tests that setting a field, then deleting it later, doesn't
    # cause an erroneous write of the originally set value after
    # a call to `XBlock.save`
    class FieldTester(XBlock):
        """Test XBlock with two fields"""
        field_a = Integer(scope=Scope.settings)
        field_b = Integer(scope=Scope.content, default=10)

    field_tester = FieldTester(MagicMock(), DictModel({'field_a': 5}), Mock())

    # Verify that the fields have been set correctly
    assert_equals(5, field_tester.field_a)
    assert_equals(10, field_tester.field_b)

    # Set the fields to new values
    field_tester.field_a = 20
    field_tester.field_b = 20

    # Assert that we've correctly cached the value of both fields to the newly set values.
    assert_equals(20, field_tester.field_a)
    assert_equals(20, field_tester.field_b)

    # Before saving, delete all the fields. Deletes are performed immediately for now,
    # so the field should immediately not be present in the _field_data after the delete.
    # However, we copy the default values into the cache, so after the delete we expect the
    # cached values to be the default values, but the fields to be removed from the _field_data.
    del field_tester.field_a
    del field_tester.field_b

    # Assert that we're now finding the right cached values - these should be the default values
    # that the fields have from the class since we've performed a delete, and XBlock.__delete__
    # inserts the default values into the cache as an optimization.
    assert_equals(None, field_tester.field_a)
    assert_equals(10, field_tester.field_b)

    # Perform explicit save
    field_tester.save()

    # Now that we've done the save, double-check that we still have the correct cached values (the defaults)
    assert_equals(None, field_tester.field_a)
    assert_equals(10, field_tester.field_b)

    # Additionally assert that in the model data, we don't have any values actually set for these fields.
    # Basically, we want to ensure that the `save` didn't overwrite anything in the actual _field_data
    # Note this test directly accessess _field_data and is thus somewhat fragile.
    assert_false(field_tester._field_data.has(field_tester, 'field_a'))
    assert_false(field_tester._field_data.has(field_tester, 'field_b'))


def test_get_mutable_mark_dirty():
    """
    Ensure that accessing a mutable field type does not mark it dirty
    if the field has never been set. If the field has been set, ensure
    that it is set to dirty.
    """
    class MutableTester(XBlock):
        """Test class with mutable fields."""
        list_field = List(default=[])

    mutable_test = MutableTester(MagicMock(), DictModel({}), Mock())

    # Test get/set with a default value.
    assert_equals(len(mutable_test._dirty_fields), 0)
    _test_get = mutable_test.list_field
    assert_equals(len(mutable_test._dirty_fields), 0)
    mutable_test.list_field = []
    assert_equals(len(mutable_test._dirty_fields), 1)

    # Now test after having explicitly set the field.
    mutable_test.save()
    assert_equals(len(mutable_test._dirty_fields), 0)
    _test_get = mutable_test.list_field
    assert_equals(len(mutable_test._dirty_fields), 1)
