"""
PublishEventMixin: A mixin for publishing events from an XBlock
"""

from xblock.core import XBlock


class PublishEventMixin:
    """
    A mixin for publishing events from an XBlock

    Requires the object to have a runtime.publish method.
    """
    additional_publish_event_data = {}

    @XBlock.json_handler
    def publish_event(self, data, suffix=''):  # pylint: disable=unused-argument
        """
        AJAX handler to allow client-side code to publish a server-side event
        """
        try:
            event_type = data.pop('event_type')
        except KeyError:
            return {'result': 'error', 'message': 'Missing event_type in JSON data'}

        return self.publish_event_from_dict(event_type, data)

    def publish_event_from_dict(self, event_type, data):
        """
        Combine 'data' with self.additional_publish_event_data and publish an event
        """
        for key, value in self.additional_publish_event_data.items():
            if key in data:
                return {'result': 'error', 'message': f'Key should not be in publish_event data: {key}'}
            data[key] = value

        self.runtime.publish(self, event_type, data)
        return {'result': 'success'}
