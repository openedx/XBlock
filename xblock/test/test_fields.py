"""
Tests for classes extending Field.
"""
# pylint: disable=protected-access
from contextlib import contextmanager
import datetime as dt
import itertools
import math
import textwrap
import unittest
import warnings

from unittest.mock import Mock
import ddt
from lxml import etree
import pytz

from xblock.core import XBlock, Scope
from xblock.field_data import DictFieldData
from xblock.fields import (
    Any, Boolean, Dict, Field, Float, Integer, List, Set, String, XMLString, DateTime, Reference, ReferenceList,
    ScopeIds, Sentinel, UNIQUE_ID, scope_key, Date, Timedelta, RelativeTime, ScoreField, ListScoreField
)
from xblock.scorable import Score
from xblock.test.tools import TestRuntime


class FieldTest(unittest.TestCase):
    """ Base test class for Fields. """

    FIELD_TO_TEST = Mock()

    def get_block(self, enforce_type):
        """
        Create a block with a field 'field_x' that is of type FIELD_TO_TEST.
        """
        class TestBlock(XBlock):
            """
            Block for testing
            """
            field_x = self.FIELD_TO_TEST(enforce_type=enforce_type)

        runtime = TestRuntime(services={'field-data': DictFieldData({})})
        return TestBlock(runtime, scope_ids=Mock(spec=ScopeIds))

    def set_and_get_field(self, arg, enforce_type):
        """
        Set the field to arg in a Block, get it and return the set value.
        """
        block = self.get_block(enforce_type)
        block.field_x = arg
        return block.field_x

    @contextmanager
    def assertDeprecationWarning(self, count=1):
        """Asserts that the contained code raises `count` deprecation warnings"""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            yield
        self.assertEqual(count, sum(
            1 for warning in caught
            if issubclass(warning.category, DeprecationWarning)
        ))

    def assertJSONOrSetGetEquals(self, expected, arg):
        """
        Asserts the result of field.from_json and of setting field.
        """
        # from_json(arg) -> expected
        self.assertEqual(expected, self.FIELD_TO_TEST().from_json(arg))
        # set+get with enforce_type arg -> expected
        self.assertEqual(expected, self.set_and_get_field(arg, True))

    def assertJSONOrSetEquals(self, expected, arg):
        """
        Asserts the result of field.from_json and of setting field.
        """
        self.assertJSONOrSetGetEquals(expected, arg)
        # set+get without enforce_type arg -> arg
        # provoking a warning unless arg == expected
        count = 0 if arg == expected else 1
        with self.assertDeprecationWarning(count):
            self.assertEqual(arg, self.set_and_get_field(arg, False))

    def assertToJSONEquals(self, expected, arg):
        """
        Assert that serialization of `arg` to JSON equals `expected`.
        """
        self.assertEqual(expected, self.FIELD_TO_TEST().to_json(arg))

    def assertJSONOrSetValueError(self, arg):
        """
        Asserts that field.from_json or setting the field throws a ValueError
        for the supplied value.
        """
        # from_json and set+get with enforce_type -> ValueError
        with self.assertRaises(ValueError):
            self.FIELD_TO_TEST().from_json(arg)
        with self.assertRaises(ValueError):
            self.set_and_get_field(arg, True)
        # set+get without enforce_type -> warning
        with self.assertDeprecationWarning():
            self.set_and_get_field(arg, False)

    def assertJSONOrSetTypeError(self, arg):
        """
        Asserts that field.from_json or setting the field throws a TypeError
        for the supplied value.
        """
        # from_json and set+get with enforce_type -> TypeError
        with self.assertRaises(TypeError):
            self.FIELD_TO_TEST().from_json(arg)
        with self.assertRaises(TypeError):
            self.set_and_get_field(arg, True)
        # set+get without enforce_type -> warning
        with self.assertDeprecationWarning():
            self.set_and_get_field(arg, False)


class IntegerTest(FieldTest):
    """
    Tests the Integer Field.
    """
    FIELD_TO_TEST = Integer

    def test_integer(self):
        self.assertJSONOrSetEquals(5, '5')
        self.assertJSONOrSetEquals(0, '0')
        self.assertJSONOrSetEquals(-1023, '-1023')
        self.assertJSONOrSetEquals(7, 7)
        self.assertJSONOrSetEquals(0, False)
        self.assertJSONOrSetEquals(1, True)

    def test_float_converts(self):
        self.assertJSONOrSetEquals(1, 1.023)
        self.assertJSONOrSetEquals(-3, -3.8)

    def test_none(self):
        self.assertJSONOrSetEquals(None, None)
        self.assertJSONOrSetEquals(None, '')

    def test_error(self):
        self.assertJSONOrSetValueError('abc')
        self.assertJSONOrSetValueError('[1]')
        self.assertJSONOrSetValueError('1.023')

        self.assertJSONOrSetTypeError([])
        self.assertJSONOrSetTypeError({})


class FloatTest(FieldTest):
    """
    Tests the Float Field.
    """
    FIELD_TO_TEST = Float

    def test_float(self):
        self.assertJSONOrSetEquals(.23, '.23')
        self.assertJSONOrSetEquals(5, '5')
        self.assertJSONOrSetEquals(0, '0.0')
        self.assertJSONOrSetEquals(-1023.22, '-1023.22')
        self.assertJSONOrSetEquals(0, 0.0)
        self.assertJSONOrSetEquals(4, 4)
        self.assertJSONOrSetEquals(-0.23, -0.23)
        self.assertJSONOrSetEquals(0, False)
        self.assertJSONOrSetEquals(1, True)

    def test_none(self):
        self.assertJSONOrSetEquals(None, None)
        self.assertJSONOrSetEquals(None, '')

    def test_error(self):
        self.assertJSONOrSetValueError('abc')
        self.assertJSONOrSetValueError('[1]')

        self.assertJSONOrSetTypeError([])
        self.assertJSONOrSetTypeError({})


class BooleanTest(FieldTest):
    """
    Tests the Boolean Field.
    """
    FIELD_TO_TEST = Boolean

    def test_false(self):
        self.assertJSONOrSetEquals(False, "false")
        self.assertJSONOrSetEquals(False, "False")
        self.assertJSONOrSetEquals(False, "")
        self.assertJSONOrSetEquals(False, "any other string")
        self.assertJSONOrSetEquals(False, False)

    def test_true(self):
        self.assertJSONOrSetEquals(True, "true")
        self.assertJSONOrSetEquals(True, "TruE")
        self.assertJSONOrSetEquals(True, True)

    def test_none(self):
        self.assertJSONOrSetEquals(False, None)

    def test_everything_converts_to_bool(self):
        self.assertJSONOrSetEquals(True, 123)
        self.assertJSONOrSetEquals(True, ['a'])
        self.assertJSONOrSetEquals(False, [])


class StringTest(FieldTest):
    """
    Tests the String Field.
    """
    FIELD_TO_TEST = String

    def test_json_equals(self):
        self.assertJSONOrSetEquals("false", "false")
        self.assertJSONOrSetEquals("abba", "abba")
        self.assertJSONOrSetEquals('"abba"', '"abba"')
        self.assertJSONOrSetEquals('', '')

    def test_none(self):
        self.assertJSONOrSetEquals(None, None)

    def test_error(self):
        self.assertJSONOrSetTypeError(['a'])
        self.assertJSONOrSetTypeError(1.023)
        self.assertJSONOrSetTypeError(3)
        self.assertJSONOrSetTypeError([1])
        self.assertJSONOrSetTypeError([])
        self.assertJSONOrSetTypeError({})

    def test_control_characters_filtered(self):
        self.assertJSONOrSetGetEquals('', '\v')
        self.assertJSONOrSetGetEquals('', b'\v')
        with self.assertRaises(AssertionError):
            self.assertJSONOrSetGetEquals('\v', b'')
        with self.assertRaises(AssertionError):
            self.assertJSONOrSetGetEquals('\v', '')
        self.assertJSONOrSetGetEquals('\n\r\t', '\n\v\r\b\t')


@ddt.ddt
class XMLStringTest(FieldTest):
    """
    Tests the XMLString Field.
    """
    FIELD_TO_TEST = XMLString

    @ddt.data(
        '<abc>Hello</abc>',
        '<abc attr="yes">Hello</abc>',
        '<xml/>',
        b'<bytes/>',
        b'<unicode>\xc8\x88</unicode>',
        None
    )
    def test_json_equals(self, input_text):
        xml_string = self.FIELD_TO_TEST(enforce_type=True)
        self.assertEqual(xml_string.to_json(input_text), input_text)

    @ddt.data(
        'text',
        '<unfinished_tag',
        '<xml unquoted_attr=3/>',
        '<xml unclosed_attr="3/>',
        '<open>with text',
        '<xml/>trailing text',
        '<open>text</close>',
        '<open>',
        b'<open>',
        b'<invalid_utf8_bytes char="\xe1"/>',
    )
    def test_bad_xml(self, input_text):
        xml_string = self.FIELD_TO_TEST(enforce_type=True)
        self.assertRaises(etree.XMLSyntaxError, xml_string.to_json, input_text)
        unchecked_xml_string = self.FIELD_TO_TEST(enforce_type=False)
        self.assertEqual(unchecked_xml_string.to_json(input_text), input_text)


class DateTest(unittest.TestCase):
    """Tests JSON conversion and type enforcement for Date fields."""

    date = Date()

    def compare_dates(self, dt1, dt2, expected_delta):
        """Assert that two datetime objects differ by the expected timedelta."""
        assert (dt1 - dt2) == expected_delta, (((str(dt1) + "-") + str(dt2)) + "!=") + str(expected_delta)

    def test_from_json(self):
        """Test conversion from iso compatible date strings to struct_time"""
        self.compare_dates(
            DateTest.date.from_json("2013-01-01"), DateTest.date.from_json("2012-12-31"), dt.timedelta(days=1)
        )
        self.compare_dates(
            DateTest.date.from_json("2013-01-01T00"),
            DateTest.date.from_json("2012-12-31T23"),
            dt.timedelta(hours=1),
        )
        self.compare_dates(
            DateTest.date.from_json("2013-01-01T00:00"),
            DateTest.date.from_json("2012-12-31T23:59"),
            dt.timedelta(minutes=1),
        )
        self.compare_dates(
            DateTest.date.from_json("2013-01-01T00:00:00"),
            DateTest.date.from_json("2012-12-31T23:59:59"),
            dt.timedelta(seconds=1),
        )
        self.compare_dates(
            DateTest.date.from_json("2013-01-01T00:00:00Z"),
            DateTest.date.from_json("2012-12-31T23:59:59Z"),
            dt.timedelta(seconds=1),
        )
        self.compare_dates(
            DateTest.date.from_json("2012-12-31T23:00:01-01:00"),
            DateTest.date.from_json("2013-01-01T00:00:00+01:00"),
            dt.timedelta(hours=1, seconds=1),
        )

    def test_enforce_type(self):
        """Test enforcement of input types for Date field."""
        assert DateTest.date.enforce_type(None) is None
        assert DateTest.date.enforce_type("") is None
        assert DateTest.date.enforce_type("2012-12-31T23:00:01") == dt.datetime(2012, 12, 31, 23, 0, 1, tzinfo=pytz.UTC)
        assert DateTest.date.enforce_type(1234567890000) == dt.datetime(2009, 2, 13, 23, 31, 30, tzinfo=pytz.UTC)
        assert DateTest.date.enforce_type(dt.datetime(2014, 5, 9, 21, 1, 27, tzinfo=pytz.UTC)) == dt.datetime(
            2014, 5, 9, 21, 1, 27, tzinfo=pytz.UTC
        )
        with self.assertRaises(TypeError):
            DateTest.date.enforce_type([1])

    def test_return_none(self):
        """Test that invalid or empty inputs return None for Date field."""
        assert DateTest.date.from_json("") is None
        assert DateTest.date.from_json(None) is None
        with self.assertRaises(TypeError):
            DateTest.date.from_json(["unknown value"])

    def test_old_due_date_format(self):
        """Test parsing of non-standard human-readable date formats."""
        current = dt.datetime.today()
        assert dt.datetime(current.year, 3, 12, 12, tzinfo=pytz.UTC) == DateTest.date.from_json("March 12 12:00")
        assert dt.datetime(current.year, 12, 4, 16, 30, tzinfo=pytz.UTC) == DateTest.date.from_json("December 4 16:30")
        assert DateTest.date.from_json("12 12:00") is None

    def test_non_std_from_json(self):
        """
        Test the non-standard args being passed to from_json
        """
        now = dt.datetime.now(pytz.UTC)
        delta = now - dt.datetime.fromtimestamp(0, pytz.UTC)
        assert DateTest.date.from_json(delta.total_seconds() * 1000) == now
        yesterday = dt.datetime.now(pytz.UTC) - dt.timedelta(days=-1)
        assert DateTest.date.from_json(yesterday) == yesterday

    def test_to_json(self):
        """
        Test converting time reprs to iso dates
        """
        assert (
            DateTest.date.to_json(
                dt.datetime.strptime("2012-12-31T23:59:59Z", "%Y-%m-%dT%H:%M:%SZ")
            ) == "2012-12-31T23:59:59Z"
        )

        assert DateTest.date.to_json(DateTest.date.from_json("2012-12-31T23:59:59Z")) == "2012-12-31T23:59:59Z"
        assert (
            DateTest.date.to_json(DateTest.date.from_json("2012-12-31T23:00:01-01:00")) == "2012-12-31T23:00:01-01:00"
        )
        with self.assertRaises(TypeError):
            DateTest.date.to_json("2012-12-31T23:00:01-01:00")


@ddt.ddt
class DateTimeTest(FieldTest):
    """
    Tests of the DateTime field.
    """
    FIELD_TO_TEST = DateTime

    def test_json_equals(self):
        self.assertJSONOrSetEquals(
            dt.datetime(2014, 4, 1, 2, 3, 4, 567890).replace(tzinfo=pytz.utc),
            '2014-04-01T02:03:04.567890'
        )
        self.assertJSONOrSetEquals(
            dt.datetime(2014, 4, 1, 2, 3, 4).replace(tzinfo=pytz.utc),
            '2014-04-01T02:03:04.000000'
        )
        self.assertJSONOrSetEquals(
            dt.datetime(2014, 4, 1, 2, 3, 4).replace(tzinfo=pytz.utc),
            '2014-04-01T02:03:04Z'
        )
        self.assertJSONOrSetEquals(
            dt.datetime(2014, 4, 1, 2, 3, 4).replace(tzinfo=pytz.utc),
            dt.datetime(2014, 4, 1, 2, 3, 4).replace(tzinfo=pytz.utc)
        )
        self.assertJSONOrSetEquals(
            dt.timedelta(days=1, seconds=1),
            dt.timedelta(days=1, seconds=1),
        )
        self.assertJSONOrSetEquals(
            dt.timedelta(days=1, seconds=1),
            dt.timedelta(seconds=86401),
        )
        self.assertJSONOrSetEquals(
            dt.timedelta(days=1, seconds=1),
            86401,
        )
        self.assertJSONOrSetEquals(
            dt.timedelta(days=-2, seconds=86399),
            -86401,
        )
        self.assertJSONOrSetEquals(
            dt.timedelta(days=-1, seconds=86399),
            -1,
        )

    def test_serialize(self):
        self.assertToJSONEquals(
            '2014-04-01T02:03:04.567890',
            dt.datetime(2014, 4, 1, 2, 3, 4, 567890).replace(tzinfo=pytz.utc)
        )

        self.assertToJSONEquals(
            '2014-04-01T02:03:04.000000',
            dt.datetime(2014, 4, 1, 2, 3, 4).replace(tzinfo=pytz.utc)
        )
        self.assertToJSONEquals(
            86401.0,
            dt.timedelta(days=1, seconds=1),
        )
        self.assertToJSONEquals(
            -1.0,
            dt.timedelta(days=-1, seconds=86399),
        )
        self.assertToJSONEquals(
            86401,
            dt.timedelta(days=1, seconds=1),
        )
        self.assertToJSONEquals(
            -1,
            dt.timedelta(days=-1, seconds=86399),
        )

    @ddt.unpack
    @ddt.data(
        (
            dt.datetime(2014, 4, 1, 2, 3, 4).replace(tzinfo=pytz.utc),
            dt.datetime(2014, 4, 1, 2, 3, 5)
        ),
        (
            dt.datetime(2014, 4, 1, 2, 3, 4),
            dt.datetime(2014, 4, 1, 2, 3, 4).replace(tzinfo=pytz.utc),
        )
    )
    def test_naive(self, original, replacement):
        """
        Make sure field comparison doesn't crash when comparing naive and non-naive datetimes.
        """
        for enforce_type in (False, True):
            block = self.get_block(enforce_type)
            block.field_x = original
            block.field_x = replacement

    def test_none(self):
        self.assertJSONOrSetEquals(None, None)
        self.assertJSONOrSetEquals(None, '')
        self.assertEqual(DateTime().to_json(None), None)

    def test_error(self):
        self.assertJSONOrSetTypeError(['a'])

    def test_date_format_error(self):
        with self.assertRaises(ValueError):
            DateTime().from_json('invalid')

    def test_serialize_error(self):
        with self.assertRaises(TypeError):
            DateTime().to_json('not a datetime')


class TimedeltaTest(unittest.TestCase):
    """Tests JSON conversion and type enforcement for Timedelta fields."""

    delta = Timedelta()

    def test_from_json(self):
        """Test conversion from string representations to timedelta objects."""
        assert TimedeltaTest.delta.from_json("1 day 12 hours 59 minutes 59 seconds") == dt.timedelta(
            days=1, hours=12, minutes=59, seconds=59
        )

        assert TimedeltaTest.delta.from_json("1 day 46799 seconds") == dt.timedelta(days=1, seconds=46799)

    def test_enforce_type(self):
        """Test enforcement of input types for Timedelta field."""
        assert TimedeltaTest.delta.enforce_type(None) is None
        assert TimedeltaTest.delta.enforce_type(dt.timedelta(days=1, seconds=46799)) == dt.timedelta(
            days=1, seconds=46799
        )
        assert TimedeltaTest.delta.enforce_type("1 day 46799 seconds") == dt.timedelta(days=1, seconds=46799)
        with self.assertRaises(TypeError):
            TimedeltaTest.delta.enforce_type([1])

    def test_to_json(self):
        """Test converting timedelta objects to string representations."""
        assert "1 days 46799 seconds" == TimedeltaTest.delta.to_json(
            dt.timedelta(days=1, hours=12, minutes=59, seconds=59)
        )


class RelativeTimeTest(unittest.TestCase):
    """Tests JSON conversion and type enforcement for RelativeTime fields."""

    delta = RelativeTime()

    def test_from_json(self):
        """Test conversion from string or numeric values to timedelta objects."""
        assert RelativeTimeTest.delta.from_json("0:05:07") == dt.timedelta(seconds=307)

        assert RelativeTimeTest.delta.from_json(100.0) == dt.timedelta(seconds=100)
        assert RelativeTimeTest.delta.from_json(None) == dt.timedelta(seconds=0)

        with self.assertRaises(TypeError):
            RelativeTimeTest.delta.from_json(1234)  # int

        with self.assertRaises(ValueError):
            RelativeTimeTest.delta.from_json("77:77:77")

    def test_enforce_type(self):
        """Test enforcement of input types for RelativeTime field."""
        assert RelativeTimeTest.delta.enforce_type(None) is None
        assert RelativeTimeTest.delta.enforce_type(dt.timedelta(days=1, seconds=46799)) == dt.timedelta(
            days=1, seconds=46799
        )
        assert RelativeTimeTest.delta.enforce_type("0:05:07") == dt.timedelta(seconds=307)
        with self.assertRaises(TypeError):
            RelativeTimeTest.delta.enforce_type([1])

    def test_to_json(self):
        """Test converting timedelta objects to HH:MM:SS string format."""
        assert "01:02:03" == RelativeTimeTest.delta.to_json(dt.timedelta(seconds=3723))
        assert "00:00:00" == RelativeTimeTest.delta.to_json(None)
        assert "00:01:40" == RelativeTimeTest.delta.to_json(100.0)

        error_msg = "RelativeTime max value is 23:59:59=86400.0 seconds, but 90000.0 seconds is passed"
        with self.assertRaisesRegex(ValueError, error_msg):
            RelativeTimeTest.delta.to_json(dt.timedelta(seconds=90000))

        with self.assertRaises(TypeError):
            RelativeTimeTest.delta.to_json("123")

    def test_str(self):
        """Test that RelativeTime outputs correct HH:MM:SS string representations."""
        assert "01:02:03" == RelativeTimeTest.delta.to_json(dt.timedelta(seconds=3723))
        assert "11:02:03" == RelativeTimeTest.delta.to_json(dt.timedelta(seconds=39723))


class AnyTest(FieldTest):
    """
    Tests the Any Field.
    """
    FIELD_TO_TEST = Any

    def test_json_equals(self):
        self.assertJSONOrSetEquals({'bar'}, {'bar'})
        self.assertJSONOrSetEquals("abba", "abba")
        self.assertJSONOrSetEquals('', '')
        self.assertJSONOrSetEquals('3.2', '3.2')
        self.assertJSONOrSetEquals(False, False)
        self.assertJSONOrSetEquals([3, 4], [3, 4])

    def test_none(self):
        self.assertJSONOrSetEquals(None, None)


class ListTest(FieldTest):
    """
    Tests the List Field.
    """
    FIELD_TO_TEST = List

    def test_json_equals(self):
        self.assertJSONOrSetEquals([], [])
        self.assertJSONOrSetEquals(['foo', 'bar'], ['foo', 'bar'])
        self.assertJSONOrSetEquals([1, 3.4], [1, 3.4])

    def test_none(self):
        self.assertJSONOrSetEquals(None, None)

    def test_error(self):
        self.assertJSONOrSetTypeError('abc')
        self.assertJSONOrSetTypeError('')
        self.assertJSONOrSetTypeError('1.23')
        self.assertJSONOrSetTypeError('true')
        self.assertJSONOrSetTypeError(3.7)
        self.assertJSONOrSetTypeError(True)
        self.assertJSONOrSetTypeError({})


class SetTest(FieldTest):
    """
    Tests the Set Field.
    """
    FIELD_TO_TEST = Set

    def test_json_equals(self):
        self.assertJSONOrSetEquals(set(), set())
        self.assertJSONOrSetEquals({'foo', 'bar'}, {'foo', 'bar'})
        self.assertJSONOrSetEquals({'bar', 'foo'}, {'foo', 'bar'})
        self.assertJSONOrSetEquals({1, 3.14}, {1, 3.14})
        self.assertJSONOrSetEquals({1, 3.14}, {1, 3.14, 1})  # pylint: disable=duplicate-value

    def test_hashable_converts(self):
        self.assertJSONOrSetEquals({1, 3.4}, [1, 3.4])
        self.assertJSONOrSetEquals({'a', 'b'}, 'ab')
        self.assertJSONOrSetEquals({'k1', 'k2'}, {'k1': 1, 'k2': '2'})

    def test_none(self):
        self.assertJSONOrSetEquals(None, None)

    def test_error(self):
        self.assertJSONOrSetTypeError(42)
        self.assertJSONOrSetTypeError(3.7)
        self.assertJSONOrSetTypeError(True)


class ReferenceTest(FieldTest):
    """
    Tests the Reference Field.
    """
    FIELD_TO_TEST = Reference

    def test_json_equals(self):
        self.assertJSONOrSetEquals({'id': 'bar', 'usage': 'baz'}, {'id': 'bar', 'usage': 'baz'})
        self.assertJSONOrSetEquals("i4x://myu/mycourse/problem/myproblem", "i4x://myu/mycourse/problem/myproblem")
        self.assertJSONOrSetEquals('', '')
        self.assertJSONOrSetEquals(3.2, 3.2)
        self.assertJSONOrSetEquals(False, False)
        self.assertJSONOrSetEquals([3, 4], [3, 4])

    def test_none(self):
        self.assertJSONOrSetEquals(None, None)


class ReferenceListTest(FieldTest):
    """
    Tests the ReferenceList Field.
    """
    FIELD_TO_TEST = ReferenceList

    def test_json_equals(self):
        self.assertJSONOrSetEquals([], [])
        self.assertJSONOrSetEquals(['foo', 'bar'], ['foo', 'bar'])
        self.assertJSONOrSetEquals([1, 3.4], [1, 3.4])

    def test_none(self):
        self.assertJSONOrSetEquals(None, None)

    def test_error(self):
        self.assertJSONOrSetTypeError('abc')
        self.assertJSONOrSetTypeError('')
        self.assertJSONOrSetTypeError('1.23')
        self.assertJSONOrSetTypeError('true')
        self.assertJSONOrSetTypeError(3.7)
        self.assertJSONOrSetTypeError(True)
        self.assertJSONOrSetTypeError({})


class DictTest(FieldTest):
    """
    Tests the Dict Field.
    """
    FIELD_TO_TEST = Dict

    def test_json_equals(self):
        self.assertJSONOrSetEquals({}, {})
        self.assertJSONOrSetEquals({'a': 'b', 'c': 3}, {'a': 'b', 'c': 3})

    def test_none(self):
        self.assertJSONOrSetEquals(None, None)

    def test_error(self):
        self.assertJSONOrSetTypeError(['foo', 'bar'])
        self.assertJSONOrSetTypeError([])
        self.assertJSONOrSetTypeError('abc')
        self.assertJSONOrSetTypeError('1.23')
        self.assertJSONOrSetTypeError('true')
        self.assertJSONOrSetTypeError(3.7)
        self.assertJSONOrSetTypeError(True)


def test_field_name_defaults():
    # Tests field display name default values
    attempts = Integer()
    attempts.__name__ = "max_problem_attempts"
    assert attempts.display_name == 'max_problem_attempts'

    class TestBlock(XBlock):
        """
        Block for testing
        """
        field_x = List()

    assert TestBlock.field_x.display_name == "field_x"


def test_scope_key():
    # Tests field display name default values
    class TestBlock(XBlock):
        """
        Block for testing
        """
        field_x = List(scope=Scope.settings, name='')
        settings_lst = List(scope=Scope.settings, name='')
        uss_lst = List(scope=Scope.user_state_summary, name='')
        user_lst = List(scope=Scope.user_state, name='')
        pref_lst = List(scope=Scope.preferences, name='')
        user_info_lst = List(scope=Scope.user_info, name='')

    sids = ScopeIds(user_id="_bob",
                    block_type="b.12#ob",
                    def_id="..",
                    usage_id="..")

    field_data = DictFieldData({})

    runtime = TestRuntime(Mock(), services={'field-data': field_data})
    block = TestBlock(runtime, None, sids)

    # Format: usage or block ID/field_name/user_id
    for item, correct_key in [[TestBlock.field_x, "__..../field__x/NONE.NONE"],
                              [TestBlock.user_info_lst, "NONE.NONE/user__info__lst/____bob"],
                              [TestBlock.pref_lst, "b..12_35_ob/pref__lst/____bob"],
                              [TestBlock.user_lst, "__..../user__lst/____bob"],
                              [TestBlock.uss_lst, "__..../uss__lst/NONE.NONE"],
                              [TestBlock.settings_lst, "__..../settings__lst/NONE.NONE"]]:
        key = scope_key(item, block)
        assert key == correct_key


def test_field_display_name():
    attempts = Integer(display_name='Maximum Problem Attempts')
    attempts._name = "max_problem_attempts"
    assert attempts.display_name == "Maximum Problem Attempts"

    boolean_field = Boolean(display_name="boolean field")
    assert boolean_field.display_name == "boolean field"

    class TestBlock(XBlock):
        """
        Block for testing
        """
        field_x = List(display_name="Field Known as X")

    assert TestBlock.field_x.display_name == "Field Known as X"


def test_unique_id_default():
    class TestBlock(XBlock):
        """
        Block for testing
        """
        field_a = String(default=UNIQUE_ID, scope=Scope.settings)
        field_b = String(default=UNIQUE_ID, scope=Scope.user_state)

    sids = ScopeIds(user_id="bob",
                    block_type="bobs-type",
                    def_id="definition-id",
                    usage_id="usage-id")

    runtime = TestRuntime(services={'field-data': DictFieldData({})})
    block = TestBlock(runtime, DictFieldData({}), sids)
    unique_a = block.field_a
    unique_b = block.field_b
    # Create another instance of the same block. Unique ID defaults should not change.
    runtime = TestRuntime(services={'field-data': DictFieldData({})})
    block = TestBlock(runtime, DictFieldData({}), sids)
    assert unique_a == block.field_a
    assert unique_b == block.field_b
    # Change the user id. Unique ID default should change for field_b with
    # user_state scope, but not for field_a with scope=settings.
    runtime = TestRuntime(services={'field-data': DictFieldData({})})
    block = TestBlock(runtime, DictFieldData({}), sids._replace(user_id='alice'))
    assert unique_a == block.field_a
    assert unique_b != block.field_b
    # Change the usage id. Unique ID default for both fields should change.
    runtime = TestRuntime(services={'field-data': DictFieldData({})})
    block = TestBlock(runtime, DictFieldData({}), sids._replace(usage_id='usage-2'))
    assert unique_a != block.field_a
    assert unique_b != block.field_b


def test_values():
    # static return value
    field_values = ['foo', 'bar']
    test_field = String(values=field_values)
    assert field_values == test_field.values

    # function to generate values
    test_field = String(values=lambda: [1, 4])
    assert [1, 4] == test_field.values

    # default if nothing specified
    assert String().values is None


def test_values_boolean():
    # Test Boolean, which has values defined
    test_field = Boolean()
    assert ({'display_name': "True", "value": True}, {'display_name': "False", "value": False}) == \
        test_field.values


def test_values_dict():
    # Test that the format expected for integers is allowed
    test_field = Integer(values={"min": 1, "max": 100})
    assert {"min": 1, "max": 100} == test_field.values


def test_set_incomparable_fields():
    # if we can't compare a field's value to the value it's going to be reset to
    # (i.e. timezone aware and unaware datetimes), just reset the value.

    class FieldTester(XBlock):
        """Test block for this test."""
        incomparable = Field(scope=Scope.settings)

    not_timezone_aware = dt.datetime(2015, 1, 1)
    timezone_aware = dt.datetime(2015, 1, 1, tzinfo=pytz.UTC)
    runtime = TestRuntime(services={'field-data': DictFieldData({})})
    field_tester = FieldTester(runtime, scope_ids=Mock(spec=ScopeIds))
    field_tester.incomparable = not_timezone_aware
    field_tester.incomparable = timezone_aware
    assert field_tester.incomparable == timezone_aware


def test_twofaced_field_access():
    # Check that a field with different to_json and from_json representations
    # persists and saves correctly.
    class TwoFacedField(Field):
        """A field that emits different 'json' than it parses."""
        def from_json(self, value):
            """Store an int, the length of the string parsed."""
            return len(value)

        def to_json(self, value):
            """Emit some number of X's."""
            return "X" * value

    class FieldTester(XBlock):
        """Test block for TwoFacedField."""
        how_many = TwoFacedField(scope=Scope.settings)

    original_json = "YYY"
    runtime = TestRuntime(services={'field-data': DictFieldData({'how_many': original_json})})
    field_tester = FieldTester(runtime, scope_ids=Mock(spec=ScopeIds))

    # Test that the native value isn't equal to the original json we specified.
    assert field_tester.how_many != original_json
    # Test that the native -> json value isn't equal to the original json we specified.
    assert TwoFacedField().to_json(field_tester.how_many) != original_json

    # The previous accesses will mark the field as dirty (via __get__)
    assert len(field_tester._dirty_fields) == 1
    # However, the field should not ACTUALLY be marked as a field that is needing to be saved.
    assert 'how_many' not in field_tester._get_fields_to_save()   # pylint: disable=W0212


def test_setting_the_same_value_marks_field_as_dirty():
    """
    Check that setting field to the same value marks mutable fields as dirty.
    However, since the value hasn't changed, these fields won't be saved.
    """
    # pylint: disable=unsubscriptable-object
    class FieldTester(XBlock):
        """Test block for set - get test."""
        non_mutable = String(scope=Scope.settings)
        list_field = List(scope=Scope.settings)
        dict_field = Dict(scope=Scope.settings)

    runtime = TestRuntime(services={'field-data': DictFieldData({})})
    field_tester = FieldTester(runtime, scope_ids=Mock(spec=ScopeIds))

    # precondition checks
    assert len(field_tester._dirty_fields) == 0
    assert not field_tester.fields['list_field'].is_set_on(field_tester)
    assert not field_tester.fields['dict_field'].is_set_on(field_tester)
    assert not field_tester.fields['non_mutable'].is_set_on(field_tester)

    field_tester.non_mutable = field_tester.non_mutable
    field_tester.list_field = field_tester.list_field
    field_tester.dict_field = field_tester.dict_field

    assert not field_tester.fields['non_mutable'] in field_tester._dirty_fields
    assert field_tester.fields['list_field'] in field_tester._dirty_fields
    assert field_tester.fields['dict_field'] in field_tester._dirty_fields

    assert not field_tester.fields['non_mutable'].is_set_on(field_tester)
    assert not field_tester.fields['list_field'].is_set_on(field_tester)
    assert not field_tester.fields['dict_field'].is_set_on(field_tester)


class SentinelTest(unittest.TestCase):
    """
    Tests of :ref:`xblock.fields.Sentinel`.
    """
    def test_equality(self):
        base = Sentinel('base')
        self.assertEqual(base, base)
        self.assertEqual(base, Sentinel('base'))
        self.assertNotEqual(base, Sentinel('foo'))
        self.assertNotEqual(base, 'base')

    def test_hashing(self):
        base = Sentinel('base')
        a_dict = {base: True}
        self.assertEqual(a_dict[Sentinel('base')], True)
        self.assertEqual(a_dict[base], True)
        self.assertNotIn(Sentinel('foo'), a_dict)
        self.assertNotIn('base', a_dict)


@ddt.ddt
class FieldSerializationTest(unittest.TestCase):
    """
    Tests field.from_string and field.to_string methods.
    """
    def assert_to_string(self, _type, value, string):
        """
        Helper method: checks if _type's to_string given instance of _type returns expected string
        """
        result = _type().to_string(value)
        self.assertEqual(result, string)

    def assert_from_string(self, _type, string, value):
        """
        Helper method: checks if _type's from_string given string representation of type returns expected value
        """
        result = _type().from_string(string)
        self.assertEqual(result, value)

    # Serialisation test data that is tested both ways, i.e. whether serialisation of the value
    # yields the string and deserialisation of the string yields the value.
    @ddt.unpack
    @ddt.data(
        (DateTime, None, None)
    )
    def test_to_string(self, _type, value, string):
        self.assert_to_string(_type, value, string)

    @ddt.unpack
    @ddt.data(
        (Integer, 0, '0'),
        (Integer, 5, '5'),
        (Integer, -1023, '-1023'),
        (Integer, 12345678, "12345678"),
        (Float, 5.321, '5.321'),
        (Float, -1023.35, '-1023.35'),
        (Float, 1e+100, '1e+100'),
        (Float, float('inf'), 'Infinity'),
        (Float, float('-inf'), '-Infinity'),
        (Boolean, True, "true"),
        (Boolean, False, "false"),
        (Integer, True, 'true'),
        (String, "", ""),
        (String, "foo", 'foo'),
        (String, "bar", 'bar'),
        (Dict, {}, '{}'),
        (List, [], '[]'),
        (Dict, {"foo": 1, "bar": 2}, textwrap.dedent("""\
            {
              "bar": 2,
              "foo": 1
            }""")),
        (List, [1, 2, 3], textwrap.dedent("""\
            [
              1,
              2,
              3
            ]""")),
        (Dict, {"foo": [1, 2, 3], "bar": 2}, textwrap.dedent("""\
            {
              "bar": 2,
              "foo": [
                1,
                2,
                3
              ]
            }""")),
        (DateTime, dt.datetime(2014, 4, 1, 2, 3, 4, 567890).replace(tzinfo=pytz.utc), '2014-04-01T02:03:04.567890'),
        (DateTime, dt.datetime(2014, 4, 1, 2, 3, 4).replace(tzinfo=pytz.utc), '2014-04-01T02:03:04.000000'),
    )
    def test_both_directions(self, _type, value, string):
        """Easy cases that work in both directions."""
        self.assert_to_string(_type, value, string)
        self.assert_from_string(_type, string, value)

    @ddt.unpack
    @ddt.data(
        (Float, 0.0, r"0|0\.0*"),
        (Float, 1.0, r"1|1\.0*"),
        (Float, -10.0, r"-10|-10\.0*"))
    def test_to_string_regexp_matches(self, _type, value, regexp):
        result = _type().to_string(value)
        self.assertRegex(result, regexp)

    # Test data for non-canonical serialisations of values that we should be able to correctly
    # deserialise.  These values are not serialised to the representation given here for various
    # reasons; some of them are non-standard number representations, others are YAML data that
    # isn't valid JSON, yet others use non-standard capitalisation.
    @ddt.unpack
    @ddt.data(
        (Integer, "0xff", 0xff),
        (Integer, "0b01", 1),
        (Integer, "0b10", 2),
        (Float, '0', 0.0),
        (Float, '0.0', 0.0),
        (Float, '-10', -10.0),
        (Float, '-10.0', -10.0),
        (Boolean, 'TRUE', True),
        (Boolean, 'FALSE', False),
        (
            Dict,
            textwrap.dedent("""\
                foo: 1
                bar: 2.124
                baz: True
                kuu: some string
            """),
            {"foo": 1, "bar": 2.124, "baz": True, "kuu": "some string"}
        ),
        (
            List,
            textwrap.dedent("""\
                - 1
                - 2.345
                - true
                - false
                - null
                - some string
            """),
            [1, 2.345, True, False, None, "some string"]
        ),
        (
            Dict,
            textwrap.dedent("""\
                foo: 1
                bar: [1, 2, 3]
            """),
            {"foo": 1, "bar": [1, 2, 3]}
        ),
        (
            Dict,
            textwrap.dedent("""\
                foo: 1
                bar:
                    - 1
                    - 2
                    - meow: true
                      woof: false
                      kaw: null
            """),
            {"foo": 1, "bar": [1, 2, {"meow": True, "woof": False, "kaw": None}]}
        ),
        (
            List,
            textwrap.dedent("""\
                - 1
                - 2.345
                - {"foo": true, "bar": [1,2,3]}
                - meow: false
                  woof: true
                  kaw: null
            """),
            [1, 2.345, {"foo": True, "bar": [1, 2, 3]}, {"meow": False, "woof": True, "kaw": None}]
        ),
        # Test that legacy DateTime format including double quotes can still be imported for compatibility with
        # old data export tar balls.
        (DateTime, '"2014-04-01T02:03:04.567890"', dt.datetime(2014, 4, 1, 2, 3, 4, 567890).replace(tzinfo=pytz.utc)),
        (DateTime, '"2014-04-01T02:03:04.000000"', dt.datetime(2014, 4, 1, 2, 3, 4).replace(tzinfo=pytz.utc)),
        (DateTime, '', None),
    )
    def test_from_string(self, _type, string, value):
        self.assert_from_string(_type, string, value)

    def test_float_from_NaN_is_nan(self):  # pylint: disable=invalid-name
        """Test parsing of NaN.

        This special test case is necessary since
        float('nan') compares inequal to everything.
        """
        result = Float().from_string('NaN')
        self.assertTrue(math.isnan(result))

    @ddt.unpack
    @ddt.data(*itertools.product(
        [Integer, Float],
        ['{"foo":"bar"}', '[1, 2, 3]', 'baz', '1.abc', 'defg']))
    def test_from_string_errors(self, _type, string):
        """ Cases that raises various exceptions."""
        with self.assertRaises(Exception):
            _type().from_string(string)


@ddt.ddt
class ScoreFieldTest(unittest.TestCase):
    """
    Tests for ScoreField and ListScoreField.
    """

    FIELD_TO_TEST = ScoreField

    def test_score_field_basic_serialization(self):
        """Test basic JSON -> Score object conversion."""
        field = ScoreField()
        data = {"raw_earned": 5, "raw_possible": 10}

        result = field.from_json(data)

        self.assertIsInstance(result, Score)
        self.assertEqual(result.raw_earned, 5)
        self.assertEqual(result.raw_possible, 10)

    def test_score_field_idempotency(self):
        """Test that passing a Score object returns it unchanged."""
        field = ScoreField()
        score = Score(raw_earned=5, raw_possible=10)
        self.assertEqual(field.from_json(score), score)

    def test_score_field_none(self):
        """Test that None is handled correctly."""
        field = ScoreField()
        self.assertIsNone(field.from_json(None))

    @ddt.data(
        {"raw_earned": 5},  # Missing key
        {"raw_possible": 10},  # Missing key
        {"raw_earned": 5, "raw_possible": 10, "extra": 1},  # Extra key
    )
    def test_score_field_invalid_structure(self, data):
        """Test TypeError is raised for incorrect dictionary structure."""
        field = ScoreField()
        with self.assertRaises(TypeError):
            field.from_json(data)

    @ddt.data(
        {"raw_earned": -1, "raw_possible": 10},  # Negative earned
        {"raw_earned": 5, "raw_possible": -1},  # Negative possible
        {"raw_earned": 11, "raw_possible": 10},  # Earned > Possible
    )
    def test_score_field_validation_logic(self, data):
        """Test ValueError is raised for logic violations."""
        field = ScoreField(display_name="Test Score")
        # The error message relies on display_name, so we set it to ensure formatting works
        with self.assertRaises(ValueError):
            field.from_json(data)

    def test_list_score_field_success(self):
        """Test deserializing a list of score dictionaries."""
        field = ListScoreField()
        data = [{"raw_earned": 5, "raw_possible": 10}, {"raw_earned": 0, "raw_possible": 5}]

        results = field.from_json(data)

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], Score)
        self.assertIsInstance(results[1], Score)
        self.assertEqual(results[0].raw_earned, 5)
        self.assertEqual(results[1].raw_possible, 5)

    def test_list_score_field_empty(self):
        """Test handling of empty lists."""
        field = ListScoreField()
        self.assertEqual(field.from_json([]), [])

    def test_list_score_field_none(self):
        """Test handling of None for the list field."""
        field = ListScoreField()
        self.assertIsNone(field.from_json(None))

    def test_list_score_field_type_error(self):
        """Test that passing a non-list raises TypeError."""
        field = ListScoreField()
        with self.assertRaisesRegex(TypeError, "Value must be a list"):
            field.from_json({"not": "a list"})

    def test_list_score_field_propagates_validation_error(self):
        """
        Test that if a single item in the list is invalid,
        the specific validation error from ScoreField bubbles up.
        """
        field = ListScoreField()
        data = [
            {"raw_earned": 5, "raw_possible": 10},  # Valid
            {"raw_earned": 15, "raw_possible": 10},  # Invalid (Earned > Possible)
        ]

        with self.assertRaises(ValueError):
            field.from_json(data)
