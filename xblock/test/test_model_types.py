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


def assertSerializeEqual(field, expected, arg):
    """
    Asserts the result of field.serialize.
    """
    assert_equals(expected, field.serialize(arg))


def assertDeserializeEqual(field, expected, arg):
    """
    Asserts the result of field.deserialize.
    """
    assert_equals(expected, field.deserialize(arg))


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
        assertJSONEquals(Integer(), None, 'abc')
        assertJSONEquals(Integer(), None, '[1]')
        assertJSONEquals(Integer(), None, '1.023')
        assertJSONEquals(Integer(), None, [])
        assertJSONEquals(Integer(), None, {})

    # TODO: are we OK with this behavior (the fact that string '-3.4' differs from float -3.4)?
    def test_float_converts(self):
        assertJSONEquals(Integer(), 1, 1.023)
        assertJSONEquals(Integer(), -3, -3.8)

    def test_serialize(self):
        assertSerializeEqual(Integer(), '-2', -2)
        assertSerializeEqual(Integer(), '"2"', '2')
        assertSerializeEqual(Integer(), 'null', None)

    def test_deserialize(self):
        assertDeserializeEqual(Integer(), None, 'null')
        assertDeserializeEqual(Integer(), -2, '-2')
        assertDeserializeEqual(Integer(), "450", '"450"')

        # False can be parsed as a int (converts to 0)
        assertDeserializeEqual(Integer(), False, 'false')
        # True can be parsed as a int (converts to 1)
        assertDeserializeEqual(Integer(), True, 'true')

    def test_deserialize_unsupported_types(self):
        assertDeserializeEqual(Integer(), '[3]', '[3]')
        self.assertRaises(TypeError, Integer().deserialize, None)


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
        assertJSONEquals(Float(), None, 'abc')
        assertJSONEquals(Float(), None, '[1]')
        assertJSONEquals(Float(), None, [])
        assertJSONEquals(Float(), None, {})

    def test_serialize(self):
        assertSerializeEqual(Float(), '-2', -2)
        assertSerializeEqual(Float(), '"2"', '2')
        assertSerializeEqual(Float(), '-3.41', -3.41)
        assertSerializeEqual(Float(), '"2.589"', '2.589')
        assertSerializeEqual(Float(), 'null', None)

    def test_deserialize(self):
        assertDeserializeEqual(Float(), None, 'null')
        assertDeserializeEqual(Float(), -2, '-2')
        assertDeserializeEqual(Float(), "450", '"450"')
        assertDeserializeEqual(Float(), -2.78, '-2.78')
        assertDeserializeEqual(Float(), "0.45", '"0.45"')

        # False can be parsed as a float (converts to 0)
        assertDeserializeEqual(Float(), False, 'false')
        # True can be parsed as a float (converts to 1)
        assertDeserializeEqual(Float(), True, 'true')

    def test_deserialize_unsupported_types(self):
        assertDeserializeEqual(Float(), '[3]', '[3]')
        self.assertRaises(TypeError, Float().deserialize, None)


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

    def test_serialize(self):
        assertSerializeEqual(Boolean(), 'false', False)
        assertSerializeEqual(Boolean(), '"false"', 'false')
        assertSerializeEqual(Boolean(), '"fAlse"', 'fAlse')
        assertSerializeEqual(Boolean(), 'null', None)

    def test_deserialize(self):
        # json.loads converts the value to Python bool
        assertDeserializeEqual(Boolean(), False, 'false')
        assertDeserializeEqual(Boolean(), True, 'true')

        # json.loads fails, string value is returned.
        assertDeserializeEqual(Boolean(), 'False', 'False')
        assertDeserializeEqual(Boolean(), 'True', 'True')

        # json.loads deserializes 'null' to None
        assertDeserializeEqual(Boolean(), None, 'null')

        # json.loads deserializes as a string
        assertDeserializeEqual(Boolean(), 'false', '"false"')
        assertDeserializeEqual(Boolean(), 'fAlse', '"fAlse"')
        assertDeserializeEqual(Boolean(), "TruE", '"TruE"')

    def test_deserialize_unsupported_types(self):
        self.assertRaises(TypeError, Boolean().deserialize, None)


class StringTest(unittest.TestCase):
    """
    Tests the String ModelType.
    """

    def test_json_equals(self):
        assertJSONEquals(String(), "false", "false")
        assertJSONEquals(String(), "abba", "abba")
        assertJSONEquals(String(), None, None)

    def test_serialize(self):
        assertSerializeEqual(String(), '"hat box"', 'hat box')
        assertSerializeEqual(String(), 'null', None)

    def test_deserialize(self):
        assertDeserializeEqual(String(), 'hAlf', '"hAlf"')
        assertDeserializeEqual(String(), 'false', '"false"')
        assertDeserializeEqual(String(), 'single quote', 'single quote')
        assertDeserializeEqual(String(), None, 'null')

    def test_deserialize_unsupported_types(self):
        assertDeserializeEqual(String(), '3.4', '3.4')
        assertDeserializeEqual(String(), 'false', 'false')
        assertDeserializeEqual(String(), '2', '2')
        assertDeserializeEqual(String(), '[3]', '[3]')
        self.assertRaises(TypeError, String().deserialize, None)


class AnyTest(unittest.TestCase):
    """
    Tests the Any ModelType.
    """

    def test_json_equals(self):
        assertJSONEquals(Any(), {'bar'}, {'bar'})
        assertJSONEquals(Any(), "abba", "abba")
        assertJSONEquals(Any(), None, None)

    def test_serialize(self):
        assertSerializeEqual(Any(), '{"bar": "hat", "frog": "green"}', {'bar': 'hat', 'frog' : 'green'})
        assertSerializeEqual(Any(), '[3.5, 5.6]', [3.5, 5.6])
        assertSerializeEqual(Any(), '"hat box"', 'hat box')
        assertSerializeEqual(Any(), 'null', None)

    def test_deserialize(self):
        assertDeserializeEqual(Any(), 'hAlf', '"hAlf"')
        assertDeserializeEqual(Any(), 'false', '"false"')
        assertDeserializeEqual(Any(), None, 'null')
        assertDeserializeEqual(Any(), {'bar': 'hat', 'frog' : 'green'}, '{"bar": "hat", "frog": "green"}')
        assertDeserializeEqual(Any(), [3.5, 5.6], '[3.5, 5.6]')
        assertDeserializeEqual(Any(), '[', '[')
        assertDeserializeEqual(Any(), False, 'false')
        assertDeserializeEqual(Any(), 3.4, '3.4')

    def test_deserialize_unsupported_types(self):
        self.assertRaises(TypeError, Any().deserialize, None)


class ListTest(unittest.TestCase):
    """
    Tests the List ModelType.
    """

    def test_json_equals(self):
        assertJSONEquals(List(), [], [])
        assertJSONEquals(List(), ['foo', 'bar'], ['foo', 'bar'])
        assertJSONEquals(List(), [1, 3.4], [1, 3.4])
        assertJSONEquals(List(), None, None)

    def test_serialize(self):
        assertSerializeEqual(List(), '["foo", "bar"]', ['foo', 'bar'])
        assertSerializeEqual(List(), '[3.5, 5.6]', [3.5, 5.6])
        assertSerializeEqual(List(), 'null', None)

    def test_deserialize(self):
        assertDeserializeEqual(List(), ['foo', 'bar'], '["foo", "bar"]')
        assertDeserializeEqual(List(), [3.5, 5.6], '[3.5, 5.6]')
        assertDeserializeEqual(List(), [], '[]')
        assertDeserializeEqual(List(), None, 'null')

    def test_deserialize_unsupported_types(self):
        assertDeserializeEqual(List(), '3.4', '3.4')
        assertDeserializeEqual(List(), 'false', 'false')
        assertDeserializeEqual(List(), '2', '2')
        self.assertRaises(TypeError, List().deserialize, None)

# TODO: what should Object contain? It doesn't differ at all from List (in implementation), not sure what to test.
