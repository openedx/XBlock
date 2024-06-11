"""
Validation information for an xblock instance.
"""
from __future__ import annotations

import typing as t


class ValidationMessage:
    """
    A message containing validation information about an xblock.
    """

    WARNING = "warning"
    ERROR = "error"

    TYPES = [WARNING, ERROR]

    def __init__(self, message_type: str, message_text: str):
        """
        Create a new message.

        Args:
            message_type: The type associated with this message. Must be included in `TYPES`.
            message_text: The textual message.
        """
        if message_type not in self.TYPES:
            raise TypeError("Unknown message_type: " + message_type)
        if not isinstance(message_text, str):
            raise TypeError("Message text must be unicode")
        self.type = message_type
        self.text = message_text

    def to_json(self) -> dict[str, str]:
        """
        Convert to a json-serializable representation.

        Returns:
            dict: A dict representation that is json-serializable.
        """
        return {
            "type": self.type,
            "text": self.text
        }


class Validation:
    """
    An object containing validation information for an xblock instance.

    An instance of this class can be used as a boolean to determine if the xblock has validation issues,
    where `True` signifies that the xblock passes validation.
    """

    def __init__(self, xblock_id: object):
        """
        Create a `Validation` instance.

        Args:
            xblock_id: An identification object that must support conversion to unicode.
        """
        self.messages: list[ValidationMessage] = []
        self.xblock_id = xblock_id

    @property
    def empty(self) -> bool:
        """
        Is this object empty (contains no messages)?

        Returns:
            bool: True iff this instance has no validation issues and therefore has no messages.
        """
        return not self.messages

    def __bool__(self) -> bool:
        """
        Extended to return True if `empty` returns True

         Returns:
            True iff this instance has no validation issues.
        """
        return self.empty

    __nonzero__ = __bool__

    def add(self, message: ValidationMessage) -> None:
        """
        Add a new validation message to this instance.

        Args:
            message: A validation message to add to this instance's list of messages.
        """
        if not isinstance(message, ValidationMessage):
            raise TypeError("Argument must of type ValidationMessage")
        self.messages.append(message)

    def add_messages(self, validation: Validation) -> None:
        """
        Adds all the messages in the specified `Validation` object to this instance's
        messages array.

        Args:
            validation: An object containing the messages to add to this instance's messages.
        """
        if not isinstance(validation, Validation):
            raise TypeError("Argument must be of type Validation")

        self.messages.extend(validation.messages)

    def to_json(self) -> dict[str, t.Any]:
        """
        Convert to a json-serializable representation.

        Returns:
            dict: A dict representation that is json-serializable.
        """
        return {
            "xblock_id": str(self.xblock_id),
            "messages": [message.to_json() for message in self.messages],
            "empty": self.empty
        }
