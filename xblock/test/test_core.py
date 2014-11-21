# -*- coding: utf-8 -*-
"""
Tests the fundamentals of XBlocks including - but not limited to -
metaclassing, field access, caching, serialization, and bulk saves.
"""

# Allow accessing protected members for testing purposes
# pylint: disable=W0212
from mock import patch, MagicMock, Mock
from datetime import datetime
import json
import re
import unittest

import ddt
from webob import Response

from xblock.core import XBlock
from xblock.exceptions import (
    XBlockSaveError,
    KeyValueMultiSaveError,
    JsonHandlerError,
    DisallowedFileError,
    FieldDataDeprecationWarning,
)
from xblock.fields import Dict, Float, Integer, List, Field, Scope, ScopeIds
from xblock.field_data import FieldData, DictFieldData
from xblock.mixins import ScopedStorageMixin
from xblock.runtime import Runtime

from xblock.test.tools import (
    assert_equals, assert_raises, assert_raises_regexp,
    assert_not_equals, assert_false,
    WarningTestMixin, TestRuntime,
)


def test_field_access():
    class FieldTester(XBlock):
        """Test XBlock for field access testing"""
        field_a = Integer(scope=Scope.settings)
        field_b = Integer(scope=Scope.content, default=10)
        field_c = Integer(scope=Scope.user_state, default=42)
        float_a = Float(scope=Scope.settings, default=5.8)
        float_b = Float(scope=Scope.settings)

    field_data = DictFieldData({'field_a': 5, 'float_a': 6.1, 'field_x': 15})

    field_tester = FieldTester(TestRuntime(services={'field-data': field_data}), scope_ids=Mock())
    # Verify that the fields have been set
    assert_equals(5, field_tester.field_a)
    assert_equals(10, field_tester.field_b)
    assert_equals(42, field_tester.field_c)
    assert_equals(6.1, field_tester.float_a)
    assert_equals(None, field_tester.float_b)
    assert not hasattr(field_tester, 'field_x')

    # Set two of the fields.
    field_tester.field_a = 20
    field_tester.float_a = 20.5
    # field_a should be updated in the cache, but /not/ in the underlying db.
    assert_equals(20, field_tester.field_a)
    assert_equals(20.5, field_tester.float_a)
    assert_equals(5, field_data.get(field_tester, 'field_a'))
    assert_equals(6.1, field_data.get(field_tester, 'float_a'))
    # save the XBlock
    field_tester.save()
    # verify that the fields have been updated correctly
    assert_equals(20, field_tester.field_a)
    assert_equals(20.5, field_tester.float_a)
    # Now, field_a should be updated in the underlying db
    assert_equals(20, field_data.get(field_tester, 'field_a'))
    assert_equals(20.5, field_data.get(field_tester, 'float_a'))
    assert_equals(10, field_tester.field_b)
    assert_equals(42, field_tester.field_c)
    assert_equals(None, field_tester.float_b)

    # Deletes happen immediately (do not require a save)
    del field_tester.field_a
    del field_tester.float_a

    # After delete, we should find default values in the cache
    assert_equals(None, field_tester.field_a)
    assert_equals(5.8, field_tester.float_a)
    # But the fields should not actually be present in the underlying kvstore
    with assert_raises(KeyError):
        field_data.get(field_tester, 'field_a')
    assert_false(field_data.has(field_tester, 'field_a'))
    with assert_raises(KeyError):
        field_data.get(field_tester, 'float_a')
    assert_false(field_data.has(field_tester, 'float_a'))


def test_list_field_access():
    # Check that lists are correctly saved when not directly set
    class FieldTester(XBlock):
        """Test XBlock for field access testing"""
        field_a = List(scope=Scope.settings)
        field_b = List(scope=Scope.content, default=[1, 2, 3])
        field_c = List(scope=Scope.content, default=[4, 5, 6])
        field_d = List(scope=Scope.settings)

    field_data = DictFieldData({'field_a': [200], 'field_b': [11, 12, 13]})
    field_tester = FieldTester(TestRuntime(services={'field-data': field_data}), scope_ids=Mock(spec=ScopeIds))

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
    #  Caveat: there's not a clean way to copy the originally provided values for `field_a` and `field_b`
    #  when we instantiate the XBlock. So, the values for those two in both `field_data` and `_field_data_cache`
    #  point at the same object. Thus, `field_a` and `field_b` actually have the correct values in
    #  `field_data` right now. `field_c` does not, because it has never been written to the `field_data`.
    assert_false(field_data.has(field_tester, 'field_c'))
    assert_false(field_data.has(field_tester, 'field_d'))

    # save the XBlock
    field_tester.save()

    # verify that the fields have been updated correctly
    assert_equals([200, 1], field_tester.field_a)
    assert_equals([11, 12, 13, 14], field_tester.field_b)
    assert_equals([4, 5, 6, 7], field_tester.field_c)
    assert_equals([1], field_tester.field_d)
    # Now, the fields should be updated in the underlying kvstore

    assert_equals([200, 1], field_data.get(field_tester, 'field_a'))
    assert_equals([11, 12, 13, 14], field_data.get(field_tester, 'field_b'))
    assert_equals([4, 5, 6, 7], field_data.get(field_tester, 'field_c'))
    assert_equals([1], field_data.get(field_tester, 'field_d'))


def test_mutable_none_values():
    # Check that fields with values intentionally set to None
    # save properly.
    class FieldTester(XBlock):
        """Test XBlock for field access testing"""
        field_a = List(scope=Scope.settings)
        field_b = List(scope=Scope.settings)
        field_c = List(scope=Scope.content, default=None)

    field_tester = FieldTester(
        TestRuntime(services={'field-data': DictFieldData({'field_a': None})}),
        scope_ids=Mock(spec=ScopeIds)
    )
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

    field_data = DictFieldData({
        'field_a': {'a': 200},
        'field_b': {'a': 11, 'b': 12, 'c': 13}
    })

    field_tester = FieldTester(
        TestRuntime(services={'field-data': field_data}),
        None,
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
    #  Caveat: there's not a clean way to copy the originally provided values for `field_a` and `field_b`
    #  when we instantiate the XBlock. So, the values for those two in both `field_data` and `_field_data_cache`
    #  point at the same object. Thus, `field_a` and `field_b` actually have the correct values in
    #  `field_data` right now. `field_c` does not, because it has never been written to the `field_data`.
    assert_false(field_data.has(field_tester, 'field_c'))
    assert_false(field_data.has(field_tester, 'field_d'))

    field_tester.save()
    # verify that the fields have been updated correctly
    assert_equals({'a': 250}, field_tester.field_a)
    assert_equals({'a': 11, 'b': 12, 'c': 13, 'd': 14}, field_tester.field_b)
    assert_equals({'a': 0, 'b': 5, 'c': 6}, field_tester.field_c)
    assert_equals({'new': 'value'}, field_tester.field_d)

    # Now, the fields should be updated in the underlying kvstore
    assert_equals({'a': 250}, field_data.get(field_tester, 'field_a'))
    assert_equals({'a': 11, 'b': 12, 'c': 13, 'd': 14}, field_data.get(field_tester, 'field_b'))
    assert_equals({'a': 0, 'b': 5, 'c': 6}, field_data.get(field_tester, 'field_c'))
    assert_equals({'new': 'value'}, field_data.get(field_tester, 'field_d'))


def test_default_values():
    # Check that values that are deleted are restored to their default values
    class FieldTester(XBlock):
        """Test XBlock for field access testing"""
        dic1 = Dict(scope=Scope.settings)
        dic2 = Dict(scope=Scope.content, default={'a': 1, 'b': 2, 'c': 3})
        list1 = List(scope=Scope.settings)
        list2 = List(scope=Scope.content, default=[1, 2, 3])

    field_data = DictFieldData({'dic1': {'a': 200}, 'list1': ['a', 'b']})
    field_tester = FieldTester(TestRuntime(services={'field-data': field_data}), scope_ids=Mock(spec=ScopeIds))

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
        assert field_data.has(field_tester, fname)

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
        assert_false(field_data.has(field_tester, fname))


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

    class FieldTester(ScopedStorageMixin):
        """Toy class for ModelMetaclass and field access testing"""

        field_a = Date(scope=Scope.settings)
        field_b = Date(scope=Scope.content, default=datetime(2013, 4, 1))

    field_tester = FieldTester(
        runtime=TestRuntime(services={'field-data': DictFieldData({})}),
        scope_ids=MagicMock(spec=ScopeIds)
    )

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

    field_tester_a = FieldTester(TestRuntime(services={'field-data': DictFieldData({})}), scope_ids=Mock(spec=ScopeIds))
    field_tester_b = FieldTester(TestRuntime(services={'field-data': DictFieldData({})}), scope_ids=Mock(spec=ScopeIds))

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
    class FieldTester(ScopedStorageMixin):
        """Toy class for ModelMetaclass and field access testing"""
        field_a = List(scope=Scope.settings)

    # Make sure that field_data always returns a different object
    # each time it's actually queried, so that the caching is
    # doing the work to maintain object identity.
    field_data = MagicMock(spec=FieldData)
    field_data.get = lambda block, name, default=None: [name]  # pylint: disable=C0322
    field_tester = FieldTester(
        runtime=TestRuntime(services={'field-data': field_data}),
        scope_ids=MagicMock(spec=ScopeIds)
    )

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
    class FieldTester(ScopedStorageMixin):
        """Toy class for ModelMetaclass and field access testing"""
        field_a = List(scope=Scope.settings)

    field_data = MagicMock(spec=FieldData)
    field_data.get = lambda block, name, default=None: [name]  # pylint: disable=C0322

    # Same field_data used in different objects should result
    # in separately-cached values, so that changing a value
    # in one instance doesn't affect values stored in others.
    field_tester_a = FieldTester(
        runtime=TestRuntime(services={'field-data': field_data}),
        scope_ids=MagicMock(spec=ScopeIds)
    )
    field_tester_b = FieldTester(
        runtime=TestRuntime(services={'field-data': field_data}),
        scope_ids=MagicMock(spec=ScopeIds)
    )
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

    field_data = DictFieldData({
        'field': {'value': 4}
    })

    field_tester = FieldTester(
        TestRuntime(services={'field-data': field_data}),
        None,
        Mock(),
    )

    assert_equals(4, field_tester.field)
    field_tester.field = 5
    field_tester.save()
    assert_equals({'value': 5}, field_data.get(field_tester, 'field'))


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
        field_c = Integer(scope=Scope.user_state, default=42)

    field_tester = FieldTester(TestRuntime(services={'field-data': field_data}), scope_ids=Mock(spec=ScopeIds))
    return field_tester


def test_xblock_save_one():
    # Mimics a save failure when we only manage to save one of the values

    def fake_set_many(block, update_dict):  # pylint: disable=unused-argument
        """Mock update method that throws a KeyValueMultiSaveError indicating
           that only one field was correctly saved."""
        raise KeyValueMultiSaveError([list(update_dict.keys())[0]])

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

    def fake_set_many(block, update_dict):  # pylint: disable=unused-argument
        """Mock update method that throws a KeyValueMultiSaveError indicating
           that no fields were correctly saved."""
        raise KeyValueMultiSaveError([])

    field_tester = setup_save_failure(fake_set_many)
    field_tester.field_a = 20
    field_tester.field_b = 30
    field_tester.field_c = 40

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

    field_data = DictFieldData({'field_a': 5})
    field_tester = FieldTester(TestRuntime(services={'field-data': field_data}), scope_ids=Mock(spec=ScopeIds))

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
    # so the field should immediately not be present in the field_data after the delete.
    # However, we copy the default values into the cache, so after the delete we expect the
    # cached values to be the default values, but the fields to be removed from the field_data.
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
    # Basically, we want to ensure that the `save` didn't overwrite anything in the actual field_data
    # Note this test directly accessess field_data and is thus somewhat fragile.
    assert_false(field_data.has(field_tester, 'field_a'))
    assert_false(field_data.has(field_tester, 'field_b'))


def test_get_mutable_mark_dirty():
    """
    Ensure that accessing a mutable field type does not mark it dirty
    if the field has never been set. If the field has been set, ensure
    that it is set to dirty.
    """
    class MutableTester(XBlock):
        """Test class with mutable fields."""
        list_field = List(default=[])

    mutable_test = MutableTester(TestRuntime(services={'field-data': DictFieldData({})}), scope_ids=Mock(spec=ScopeIds))

    # Test get/set with a default value.
    assert_equals(len(mutable_test._dirty_fields), 0)
    _test_get = mutable_test.list_field
    assert_equals(len(mutable_test._dirty_fields), 1)

    mutable_test.list_field = []
    assert_equals(len(mutable_test._dirty_fields), 1)

    # Now test after having explicitly set the field.
    mutable_test.save()
    assert_equals(len(mutable_test._dirty_fields), 0)
    _test_get = mutable_test.list_field
    assert_equals(len(mutable_test._dirty_fields), 1)


def test_change_mutable_default():
    """
    Ensure that mutating the default value for a field causes
    the changes to be saved, and doesn't corrupt other instances
    """

    class MutableTester(XBlock):
        """Test class with mutable fields."""
        list_field = List()

    field_data_a = DictFieldData({})
    mutable_test_a = MutableTester(TestRuntime(services={'field-data': field_data_a}), scope_ids=Mock(spec=ScopeIds))
    field_data_b = DictFieldData({})
    mutable_test_b = MutableTester(TestRuntime(services={'field-data': field_data_b}), scope_ids=Mock(spec=ScopeIds))

    # Saving without changing the default value shouldn't write to field_data
    mutable_test_a.list_field  # pylint: disable=W0104
    mutable_test_a.save()
    with assert_raises(KeyError):
        field_data_a.get(mutable_test_a, 'list_field')

    mutable_test_a.list_field.append(1)
    mutable_test_a.save()

    assert_equals([1], field_data_a.get(mutable_test_a, 'list_field'))
    with assert_raises(KeyError):
        field_data_b.get(mutable_test_b, 'list_field')


def test_handle_shortcut():
    runtime = Mock(spec=['handle'])
    scope_ids = Mock(spec=[])
    request = Mock(spec=[])
    block = XBlock(runtime, None, scope_ids)

    block.handle('handler_name', request)
    runtime.handle.assert_called_with(block, 'handler_name', request, '')

    runtime.handle.reset_mock()
    block.handle('handler_name', request, 'suffix')
    runtime.handle.assert_called_with(block, 'handler_name', request, 'suffix')


def test_services_decorators():
    # pylint: disable=E1101
    # A default XBlock has requested no services
    xblock = XBlock(None, None, None)
    assert_equals(XBlock._services_requested, {})
    assert_equals(xblock._services_requested, {})

    @XBlock.needs("n")
    @XBlock.wants("w")
    class ServiceUsingBlock(XBlock):
        """XBlock using some services."""
        pass

    service_using_block = ServiceUsingBlock(None, scope_ids=None)
    assert_equals(ServiceUsingBlock._services_requested, {'n': 'need', 'w': 'want'})
    assert_equals(service_using_block._services_requested, {'n': 'need', 'w': 'want'})


def test_services_decorators_with_inheritance():
    @XBlock.needs("n1")
    @XBlock.wants("w1")
    class ServiceUsingBlock(XBlock):
        """XBlock using some services."""
        pass

    @XBlock.needs("n2")
    @XBlock.wants("w2")
    class SubServiceUsingBlock(ServiceUsingBlock):
        """Does this class properly inherit services from ServiceUsingBlock?"""
        pass

    sub_service_using_block = SubServiceUsingBlock(None, scope_ids=None)
    assert_equals(sub_service_using_block.service_declaration("n1"), "need")
    assert_equals(sub_service_using_block.service_declaration("w1"), "want")
    assert_equals(sub_service_using_block.service_declaration("n2"), "need")
    assert_equals(sub_service_using_block.service_declaration("w2"), "want")
    assert_equals(sub_service_using_block.service_declaration("xx"), None)


def test_cached_parent():
    class HasParent(XBlock):
        """
        Dummy empty class
        """
        pass

    runtime = TestRuntime(services={'field-data': DictFieldData({})})
    runtime.get_block = Mock()
    block = HasParent(runtime, scope_ids=Mock(spec=ScopeIds))

    # block has no parent yet, and we don't need to call the runtime to find
    # that out.
    assert_equals(block.get_parent(), None)
    assert not runtime.get_block.called

    # Set a parent id for the block.  Get the parent.  Now we have one, and we
    # used runtime.get_block to get it.
    block.parent = "some_parent_id"
    parent = block.get_parent()
    assert_not_equals(parent, None)
    assert runtime.get_block.called_with("some_parent_id")

    # Get the parent again.  It will be the same parent, and we didn't call the
    # runtime.
    runtime.get_block.reset_mock()
    parent2 = block.get_parent()
    assert parent2 is parent
    assert not runtime.get_block.called


def test_json_handler_basic():
    test_self = Mock()
    test_data = {"foo": "bar", "baz": "quux"}
    test_data_json = json.dumps(test_data)
    test_suffix = "suff"
    test_request = Mock(method="POST", body=test_data_json)

    @XBlock.json_handler
    def test_func(self, request, suffix):
        assert_equals(self, test_self)
        assert_equals(request, test_data)
        assert_equals(suffix, test_suffix)
        return request

    response = test_func(test_self, test_request, test_suffix)
    assert_equals(response.status_code, 200)
    assert_equals(response.json_body, test_data)
    assert_equals(response.content_type, "application/json")


def test_json_handler_invalid_json():
    test_request = Mock(method="POST", body="{")

    @XBlock.json_handler
    def test_func(self, request, suffix):   # pylint: disable=unused-argument
        return {}

    response = test_func(Mock(), test_request, "dummy_suffix")
    # pylint: disable=no-member
    assert_equals(response.status_code, 400)
    assert_equals(response.json_body, {"error": "Invalid JSON"})
    assert_equals(response.content_type, "application/json")


def test_json_handler_get():
    test_request = Mock(method="GET")

    @XBlock.json_handler
    def test_func(self, request, suffix):   # pylint: disable=unused-argument
        return {}

    response = test_func(Mock(), test_request, "dummy_suffix")
    # pylint: disable=no-member
    assert_equals(response.status_code, 405)
    assert_equals(response.json_body, {"error": "Method must be POST"})
    assert_equals(list(response.allow), ["POST"])


def test_json_handler_empty_request():
    test_request = Mock(method="POST", body="")

    @XBlock.json_handler
    def test_func(self, request, suffix):   # pylint: disable=unused-argument
        return {}

    response = test_func(Mock(), test_request, "dummy_suffix")
    # pylint: disable=no-member
    assert_equals(response.status_code, 400)
    assert_equals(response.json_body, {"error": "Invalid JSON"})
    assert_equals(response.content_type, "application/json")


def test_json_handler_error():
    test_status_code = 418
    test_message = "I'm a teapot"
    test_request = Mock(method="POST", body="{}")

    @XBlock.json_handler
    def test_func(self, request, suffix):   # pylint: disable=unused-argument
        raise JsonHandlerError(test_status_code, test_message)

    response = test_func(Mock(), test_request, "dummy_suffix")  # pylint: disable=assignment-from-no-return
    assert_equals(response.status_code, test_status_code)
    assert_equals(response.json_body, {"error": test_message})
    assert_equals(response.content_type, "application/json")


def test_json_handler_return_response():
    test_request = Mock(method="POST", body="{}")

    @XBlock.json_handler
    def test_func(self, request, suffix):  # pylint: disable=unused-argument
        return Response(body="not JSON", status=418, content_type="text/plain")

    response = test_func(Mock(), test_request, "dummy_suffix")
    assert_equals(response.text, "not JSON")
    assert_equals(response.status_code, 418)
    assert_equals(response.content_type, "text/plain")


@ddt.ddt
class OpenLocalResourceTest(unittest.TestCase):
    """Tests of `open_local_resource`."""

    class LoadableXBlock(XBlock):
        """Just something to load resources from."""
        pass

    def stub_resource_stream(self, module, name):
        """Act like pkg_resources.resource_stream, for testing."""
        assert module == "xblock.test.test_core"
        return "!" + name + "!"

    @ddt.data(
        "public/hey.js",
        "public/sub/hey.js",
        "public/js/vendor/jNotify.jQuery.min.js",
        "public/something.foo",         # Unknown file extension is fine
        "public/a/long/PATH/no-problem=here$123.ext",
        "public/ℓιвяαяу.js",
    )
    def test_open_good_local_resource(self, uri):
        loadable = self.LoadableXBlock(None, scope_ids=None)
        with patch('pkg_resources.resource_stream', self.stub_resource_stream):
            assert loadable.open_local_resource(uri) == "!" + uri + "!"

    @ddt.data(
        "public/../secret.js",
        "public/.git/secret.js",
        "static/secret.js",
        "../public/no-no.bad",
        "image.png",
        ".git/secret.js",
        "static/ℓιвяαяу.js",
    )
    def test_open_bad_local_resource(self, uri):
        loadable = self.LoadableXBlock(None, scope_ids=None)
        with patch('pkg_resources.resource_stream', self.stub_resource_stream):
            msg = ".*: %s" % re.escape(repr(uri))
            with assert_raises_regexp(DisallowedFileError, msg):
                loadable.open_local_resource(uri)


class TestXBlockDeprecation(WarningTestMixin, unittest.TestCase):
    """
    Tests various pieces of XBlock that have been (or will be) deprecated.
    """

    class TestBlock(XBlock):
        """An empty XBlock for testing"""
        pass

    def test_field_data_paramater(self):
        field_data = Mock(spec=FieldData)
        with self.assertWarns(FieldDataDeprecationWarning):
            block = XBlock(Mock(spec=Runtime), field_data, Mock(spec=ScopeIds))
        self.assertEqual(field_data, block._field_data)

    def test_assign_field_data(self):
        field_data = Mock(spec=FieldData)
        block = XBlock(Mock(spec=Runtime), scope_ids=Mock(spec=ScopeIds))
        with self.assertWarns(FieldDataDeprecationWarning):
            block._field_data = field_data
        self.assertEqual(field_data, block._field_data)
