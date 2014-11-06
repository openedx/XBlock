"""
Tests asserting that ModelTypes convert to and from json when working
with ModelDatas
"""
# Allow inspection of private class members
# pylint: disable=W0212
from mock import Mock

from xblock.core import XBlock
from xblock.fields import Field, Scope, ScopeIds
from xblock.field_data import DictFieldData

from xblock.test.tools import assert_equals, assert_is_instance, TestRuntime


class TestJSONConversionField(Field):
    """Field for testing json conversion"""
    def from_json(self, value):
        assert_equals('set', value['$type'])
        return set(value['$vals'])

    def to_json(self, value):
        return {
            '$type': 'set',
            '$vals': sorted(value)
        }


class TestBlock(XBlock):
    """XBlock for testing json conversion"""
    field_a = TestJSONConversionField(scope=Scope.content)
    field_b = TestJSONConversionField(scope=Scope.content)


class TestModel(DictFieldData):
    """ModelData for testing json conversion"""
    def default(self, block, name):
        return {'$type': 'set', '$vals': [0, 1]}


class TestJsonConversion(object):
    """
    Verify that all ModelType operations correctly convert
    the json that comes out of the ModelData to python objects
    """

    def setUp(self):
        field_data = TestModel({
            'field_a': {'$type': 'set', '$vals': [1, 2, 3]}
        })
        runtime = TestRuntime(services={'field-data': field_data})
        self.block = TestBlock(runtime, scope_ids=Mock(spec=ScopeIds))

    def test_get(self):
        # Test field with a value
        assert_is_instance(self.block.field_a, set)

        # Test ModelData default
        assert_is_instance(self.block.field_b, set)

    def test_set(self):
        self.block.field_b = set([5, 6, 5])
        self.block.save()
        assert_is_instance(self.block.field_b, set)
        assert_equals(
            {'$type': 'set', '$vals': [5, 6]},
            self.block._field_data.get(self.block, 'field_b')
        )
