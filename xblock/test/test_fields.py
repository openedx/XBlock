"""
Tests for classes extending Field.
"""

# Allow accessing protected members for testing purposes
# pylint: disable=W0212

import unittest

from xblock.core import XBlock
from xblock.fields import Any, Boolean, Dict, Float, Integer, List, String

from xblock.test.tools import assert_equals


class FieldTest(unittest.TestCase):
    """ Base test class for Fields. """

    def field_totest(self):
        """Child classes should override this with the type of field
        the test is testing."""
        return None

    def assertJSONEquals(self, expected, arg):
        """
        Asserts the result of field.from_json.
        """
        self.assertEqual(expected, self.field_totest().from_json(arg))

    def assertJSONValueError(self, arg):
        """
        Asserts that field.from_json throws a ValueError for the supplied value.
        """
        with self.assertRaises(ValueError):
            self.field_totest().from_json(arg)

    def assertJSONTypeError(self, arg):
        """
        Asserts that field.from_json throws a TypeError for the supplied value.
        """
        with self.assertRaises(TypeError):
            self.field_totest().from_json(arg)


class IntegerTest(FieldTest):
    """
    Tests the Integer Field.
    """
    field_totest = Integer

    def test_integer(self):
        self.assertJSONEquals(5, '5')
        self.assertJSONEquals(0, '0')
        self.assertJSONEquals(-1023, '-1023')
        self.assertJSONEquals(7, 7)
        self.assertJSONEquals(0, False)
        self.assertJSONEquals(1, True)

    def test_float_converts(self):
        self.assertJSONEquals(1, 1.023)
        self.assertJSONEquals(-3, -3.8)

    def test_none(self):
        self.assertJSONEquals(None, None)
        self.assertJSONEquals(None, '')

    def test_error(self):
        self.assertJSONValueError('abc')
        self.assertJSONValueError('[1]')
        self.assertJSONValueError('1.023')

        self.assertJSONTypeError([])
        self.assertJSONTypeError({})


class FloatTest(FieldTest):
    """
    Tests the Float Field.
    """
    field_totest = Float

    def test_float(self):
        self.assertJSONEquals(.23, '.23')
        self.assertJSONEquals(5, '5')
        self.assertJSONEquals(0, '0.0')
        self.assertJSONEquals(-1023.22, '-1023.22')
        self.assertJSONEquals(0, 0.0)
        self.assertJSONEquals(4, 4)
        self.assertJSONEquals(-0.23, -0.23)
        self.assertJSONEquals(0, False)
        self.assertJSONEquals(1, True)

    def test_none(self):
        self.assertJSONEquals(None, None)
        self.assertJSONEquals(None, '')

    def test_error(self):
        self.assertJSONValueError('abc')
        self.assertJSONValueError('[1]')

        self.assertJSONTypeError([])
        self.assertJSONTypeError({})


class BooleanTest(FieldTest):
    """
    Tests the Boolean Field.
    """
    field_totest = Boolean

    def test_false(self):
        self.assertJSONEquals(False, "false")
        self.assertJSONEquals(False, "False")
        self.assertJSONEquals(False, "")
        self.assertJSONEquals(False, "any other string")
        self.assertJSONEquals(False, False)

    def test_true(self):
        self.assertJSONEquals(True, "true")
        self.assertJSONEquals(True, "TruE")
        self.assertJSONEquals(True, True)

    def test_none(self):
        self.assertJSONEquals(False, None)

    def test_everything_converts_to_bool(self):
        self.assertJSONEquals(True, 123)
        self.assertJSONEquals(True, ['a'])
        self.assertJSONEquals(False, [])


class StringTest(FieldTest):
    """
    Tests the String Field.
    """
    field_totest = String

    def test_json_equals(self):
        self.assertJSONEquals("false", "false")
        self.assertJSONEquals("abba", "abba")
        self.assertJSONEquals('"abba"', '"abba"')
        self.assertJSONEquals('', '')

    def test_none(self):
        self.assertJSONEquals(None, None)

    def test_error(self):
        self.assertJSONTypeError(['a'])
        self.assertJSONTypeError(1.023)
        self.assertJSONTypeError(3)
        self.assertJSONTypeError([1])
        self.assertJSONTypeError([])
        self.assertJSONTypeError({})


class AnyTest(FieldTest):
    """
    Tests the Any Field.
    """
    field_totest = Any

    def test_json_equals(self):
        self.assertJSONEquals({'bar'}, {'bar'})
        self.assertJSONEquals("abba", "abba")
        self.assertJSONEquals('', '')
        self.assertJSONEquals('3.2', '3.2')
        self.assertJSONEquals(False, False)
        self.assertJSONEquals([3, 4], [3, 4])

    def test_none(self):
        self.assertJSONEquals(None, None)


class ListTest(FieldTest):
    """
    Tests the List Field.
    """
    field_totest = List

    def test_json_equals(self):
        self.assertJSONEquals([], [])
        self.assertJSONEquals(['foo', 'bar'], ['foo', 'bar'])
        self.assertJSONEquals([1, 3.4], [1, 3.4])

    def test_none(self):
        self.assertJSONEquals(None, None)

    def test_error(self):
        self.assertJSONTypeError('abc')
        self.assertJSONTypeError('')
        self.assertJSONTypeError('1.23')
        self.assertJSONTypeError('true')
        self.assertJSONTypeError(3.7)
        self.assertJSONTypeError(True)
        self.assertJSONTypeError({})


class DictTest(FieldTest):
    """
    Tests the Dict Field.
    """
    field_totest = Dict

    def test_json_equals(self):
        self.assertJSONEquals({}, {})
        self.assertJSONEquals({'a': 'b', 'c': 3}, {'a': 'b', 'c': 3})

    def test_none(self):
        self.assertJSONEquals(None, None)

    def test_error(self):
        self.assertJSONTypeError(['foo', 'bar'])
        self.assertJSONTypeError([])
        self.assertJSONTypeError('abc')
        self.assertJSONTypeError('1.23')
        self.assertJSONTypeError('true')
        self.assertJSONTypeError(3.7)
        self.assertJSONTypeError(True)


def test_field_name_defaults():
    # Tests field display name default values
    attempts = Integer()
    attempts._name = "max_problem_attempts"
    assert_equals('max_problem_attempts', attempts.display_name)

    class TestBlock(XBlock):
        """
        Block for testing
        """
        field_x = List()

    assert_equals("field_x", TestBlock.field_x.display_name)


def test_field_display_name():
    attempts = Integer(display_name='Maximum Problem Attempts')
    attempts._name = "max_problem_attempts"
    assert_equals("Maximum Problem Attempts", attempts.display_name)

    boolean_field = Boolean(display_name="boolean field")
    assert_equals("boolean field", boolean_field.display_name)

    class TestBlock(XBlock):
        """
        Block for testing
        """
        field_x = List(display_name="Field Known as X")

    assert_equals("Field Known as X", TestBlock.field_x.display_name)


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
