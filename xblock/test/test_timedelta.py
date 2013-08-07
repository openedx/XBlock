"""
The Timedelta ModelType of edx-platform has an issue where the
json -> native -> json roundtrip doesn't give back the same json value.
This seems to be due to how Timedeltas internally store things - they
only have a days and seconds attributes, whereas we also recognize hours and minutes.
"""

from mock import MagicMock
from nose.tools import assert_equals, assert_not_equals, assert_not_in  # pylint: disable=E0611

import re
from xblock.core import ModelType, Scope, XBlock
import datetime

TIMEDELTA_REGEX = re.compile(r'^((?P<days>\d+?) day(?:s?))?(\s)?((?P<hours>\d+?) hour(?:s?))?(\s)?((?P<minutes>\d+?) minute(?:s)?)?(\s)?((?P<seconds>\d+?) second(?:s)?)?$')


class Timedelta(ModelType):
    """
    A modeltype that contains a Timedelta.

    From edx-platform/common/lib/xmodule/xmodule/fields.py
    """
    def from_json(self, time_str):
        """
        time_str: A string with the following components:
            <D> day[s] (optional)
            <H> hour[s] (optional)
            <M> minute[s] (optional)
            <S> second[s] (optional)

        Returns a datetime.timedelta parsed from the string
        """
        if time_str is None:
            return None
        parts = TIMEDELTA_REGEX.match(time_str)
        if not parts:
            return
        parts = parts.groupdict()
        time_params = {}
        for (name, param) in parts.iteritems():
            if param:
                time_params[name] = int(param)
        return datetime.timedelta(**time_params)

    def to_json(self, value):
        values = []
        for attr in ('days', 'hours', 'minutes', 'seconds'):
            cur_value = getattr(value, attr, 0)
            if cur_value > 0:
                values.append("%d %s" % (cur_value, attr))
        return ' '.join(values)


def test_timedelta_field_access():
    # Check that a field with different to_json and from_json representations
    # persists and saves correctly
    class FieldTester(XBlock):
        """Test XBlock for field access testing"""
        graceperiod = Timedelta(scope=Scope.settings)

    original_json_date = '2 days 5 hours 10 minutes 59 seconds'
    field_tester = FieldTester(MagicMock(), {'graceperiod': original_json_date})

    # Access the Timedelta field without modifying it

    # Test that the native value isn't equal to the original json we specified
    assert_not_equals(field_tester.graceperiod, original_json_date)
    # Test that the native -> json value isn't equal to the original json we specified
    assert_not_equals(Timedelta().to_json(field_tester.graceperiod), original_json_date)

    # The previous accesses will mark the field as dirty (via __get__)
    assert_equals(len(field_tester._dirty_fields), 1)  # pylint: disable=W0212
    # However, the field should not ACTUALLY be marked as a field that is needing to be saved.
    assert_not_in('graceperiod', field_tester._get_fields_to_save())  # pylint: disable=W0212
