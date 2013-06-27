""" Simple test for the view counter that verifies that it is updating properly """
from nose.tools import assert_in, assert_equals
from mock import Mock
from xblock.view_counter import ViewCounter
from xblock.runtime import DbModel
from xblock.test import DictKeyValueStore
from collections import namedtuple

TestUsage = namedtuple('TestUsage', 'id, def_id')


def test_view_counter_state():
    key_store = DictKeyValueStore()
    db_model = DbModel(key_store, ViewCounter, 's0', TestUsage('u0', 'd0'))
    tester = ViewCounter(Mock(), db_model)

    assert_equals(tester.views, 0)

    # view the xblock five times
    for i in xrange(5):
        generated_html = tester.student_view({})
        assert_in('{0}'.format(i + 1), generated_html.body_html())
        assert_equals(tester.views, i + 1)
