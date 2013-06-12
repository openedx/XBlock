"""
Tests for classes extending ModelType.
"""

from nose.tools import assert_equals
import unittest
from xblock.core import *


def assertJSONEquals(field, expected, arg):
    """
    Asserts the result of field.from_json.
    """
    assert_equals(expected, field.from_json(arg))


def assertJSONValueError(self, field, arg):
    """
    Asserts that field.from_json throws a ValueError for the supplied value.
    """
    with self.assertRaises(ValueError):
        field.from_json(arg)


def assertJSONTypeError(self, field, arg):
    """
    Asserts that field.from_json throws a TypeError for the supplied value.
    """
    with self.assertRaises(TypeError):
        field.from_json(arg)


class IntegerTest(unittest.TestCase):
    """
    Tests the Integer ModelType.
    """

    def test_integer(self):
        assertJSONEquals(Integer(), 5, '5')
        assertJSONEquals(Integer(), 0, '0')
        assertJSONEquals(Integer(), -1023, '-1023')
        assertJSONEquals(Integer(), 7, 7)
        assertJSONEquals(Integer(), 0, False)
        assertJSONEquals(Integer(), 1, True)

    def test_none(self):
        assertJSONEquals(Integer(), None, None)

    def test_Error(self):
        assertJSONValueError(self, Integer(), 'abc')
        assertJSONValueError(self, Integer(), '[1]')
        assertJSONValueError(self, Integer(), '1.023')

        assertJSONTypeError(self, Integer(), [])
        assertJSONTypeError(self, Integer(), {})

    def test_float_converts(self):
        assertJSONEquals(Integer(), 1, 1.023)
        assertJSONEquals(Integer(), -3, -3.8)


class FloatTest(unittest.TestCase):
    """
    Tests the Float ModelType.
    """

    def test_float(self):
        assertJSONEquals(Float(), .23, '.23')
        assertJSONEquals(Float(), 5, '5')
        assertJSONEquals(Float(), 0, '0.0')
        assertJSONEquals(Float(), -1023.22, '-1023.22')
        assertJSONEquals(Float(), 0, 0.0)
        assertJSONEquals(Float(), 4, 4)
        assertJSONEquals(Float(), -0.23, -0.23)
        assertJSONEquals(Float(), 0, False)
        assertJSONEquals(Float(), 1, True)

    def test_none(self):
        assertJSONEquals(Float(), None, None)

    def test_Error(self):
        assertJSONValueError(self, Float(), 'abc')
        assertJSONValueError(self, Float(), '[1]')

        assertJSONTypeError(self, Float(), [])
        assertJSONTypeError(self, Float(), {})


class BooleanTest(unittest.TestCase):
    """
    Tests the Boolean ModelType.
    """

    def test_false(self):
        assertJSONEquals(Boolean(), False, "false")
        assertJSONEquals(Boolean(), False, "False")
        assertJSONEquals(Boolean(), False, "")
        assertJSONEquals(Boolean(), False, "any other string")
        assertJSONEquals(Boolean(), False, False)

    def test_true(self):
        assertJSONEquals(Boolean(), True, "true")
        assertJSONEquals(Boolean(), True, "TruE")
        assertJSONEquals(Boolean(), True, True)

    def test_everything_converts_to_bool(self):
        assertJSONEquals(Boolean(), True, 123)
        assertJSONEquals(Boolean(), True, ['a'])
        assertJSONEquals(Boolean(), False, [])
        assertJSONEquals(Boolean(), False, None)


class StringTest(unittest.TestCase):
    """
    Tests the String ModelType.
    """

    def test_json_equals(self):
        assertJSONEquals(String(), "false", "false")
        assertJSONEquals(String(), "abba", "abba")
        assertJSONEquals(String(), None, None)


class AnyTest(unittest.TestCase):
    """
    Tests the Any ModelType.
    """

    def test_json_equals(self):
        assertJSONEquals(Any(), {'bar'}, {'bar'})
        assertJSONEquals(Any(), "abba", "abba")
        assertJSONEquals(Any(), None, None)


class ListTest(unittest.TestCase):
    """
    Tests the List ModelType.
    """

    def test_json_equals(self):
        assertJSONEquals(List(), [], [])
        assertJSONEquals(List(), ['foo', 'bar'], ['foo', 'bar'])
        assertJSONEquals(List(), [1, 3.4], [1, 3.4])
        assertJSONEquals(List(), ['a', 'b', 'c'], 'abc')
        assertJSONEquals(List(), ['1', '.', '2', '3'], '1.23')
        assertJSONEquals(List(), ['t', 'r', 'u', 'e'], 'true')
        assertJSONEquals(List(), None, None)
        assertJSONEquals(List(), [], {})
