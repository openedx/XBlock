"""
Test cases for xblock/utils/publish_event.py
"""


import unittest

import simplejson as json

from xblock.utils.publish_event import PublishEventMixin


class EmptyMock():
    pass


class RequestMock:
    method = "POST"

    def __init__(self, data):
        self.body = json.dumps(data).encode('utf-8')


class RuntimeMock:
    last_call = None

    def publish(self, block, event_type, data):
        self.last_call = (block, event_type, data)


class XBlockMock:
    def __init__(self):
        self.runtime = RuntimeMock()


class ObjectUnderTest(XBlockMock, PublishEventMixin):
    pass


class TestPublishEventMixin(unittest.TestCase):
    """
    Test cases for PublishEventMixin
    """
    def assert_no_calls_made(self, block):
        self.assertFalse(block.last_call)

    def assert_success(self, response):
        self.assertEqual(json.loads(response.body)['result'], 'success')

    def assert_error(self, response):
        self.assertEqual(json.loads(response.body)['result'], 'error')

    def test_error_when_no_event_type(self):
        block = ObjectUnderTest()

        response = block.publish_event(RequestMock({}))

        self.assert_error(response)
        self.assert_no_calls_made(block.runtime)

    def test_uncustomized_publish_event(self):
        block = ObjectUnderTest()

        event_data = {"one": 1, "two": 2, "bool": True}
        data = dict(event_data)
        data["event_type"] = "test.event.uncustomized"

        response = block.publish_event(RequestMock(data))

        self.assert_success(response)
        self.assertEqual(block.runtime.last_call, (block, "test.event.uncustomized", event_data))

    def test_publish_event_with_additional_data(self):
        block = ObjectUnderTest()
        block.additional_publish_event_data = {"always_present": True, "block_id": "the-block-id"}

        event_data = {"foo": True, "bar": False, "baz": None}
        data = dict(event_data)
        data["event_type"] = "test.event.customized"

        response = block.publish_event(RequestMock(data))

        expected_data = dict(event_data)
        expected_data.update(block.additional_publish_event_data)

        self.assert_success(response)
        self.assertEqual(block.runtime.last_call, (block, "test.event.customized", expected_data))

    def test_publish_event_fails_with_duplicate_data(self):
        block = ObjectUnderTest()
        block.additional_publish_event_data = {"good_argument": True, "clashing_argument": True}

        event_data = {"fine_argument": True, "clashing_argument": False}
        data = dict(event_data)
        data["event_type"] = "test.event.clashing"

        response = block.publish_event(RequestMock(data))

        self.assert_error(response)
        self.assert_no_calls_made(block.runtime)
