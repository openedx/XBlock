"""
PublishEventMixin: A mixin for publishing events from an XBlock
"""
import typing as t

from xblock.core import XBlockMixin, XBlock


class PublishEventMixin(XBlockMixin):
    """
    A mixin for publishing events from an XBlock

    Requires the object to have a runtime.publish method.
    """
    additional_publish_event_data: dict[str, t.Any] = {}

    @XBlock.json_handler
    def publish_event(self, data: dict[str, t.Any], suffix: str = '') -> dict[str, t.Any]:  # pylint: disable=unused-argument
        """
        AJAX handler to allow client-side code to publish a server-side event
        """
        if not isinstance(data, dict):
            return {'result': 'error', 'message': 'Request data must be a JSON object'}
        try:
            event_type = data.pop('event_type')
        except KeyError:
            return {'result': 'error', 'message': 'Missing event_type in JSON data'}

        return self.publish_event_from_dict(event_type, data)

    def publish_event_from_dict(self, event_type: str, data: dict) -> dict[str, t.Any]:
        """
        Combine 'data' with self.additional_publish_event_data and publish an event
        """
        for key, value in self.additional_publish_event_data.items():
            if key in data:
                return {'result': 'error', 'message': f'Key should not be in publish_event data: {key}'}
            data[key] = value

        self.runtime.publish(self, event_type, data)
        return {'result': 'success'}
