"""
Module for all xblock exception classes
"""

class XBlockSaveError(Exception):
    """
    Raised to indicated an error in saving an XBlock
    """
    def __init__(self, saved_fields, dirty_fields):
        """
        Create a new XBlockSaveError

        `saved_fields` - a set of fields that were successfully
        saved before the error occured
        `dirty_fields` - a set of fields that were left dirty after the save
        """
        # Exception is an old-style class, so can't use super
        Exception.__init__(self)

        self.saved_fields = saved_fields
        self.dirty_fields = dirty_fields


class KeyValueMultiSaveError(Exception):
    """
    Raised to indicated an error in saving multiple fields in a KeyValueStore
    """
    def __init__(self, saved_field_names):
        """
        Create a new KeyValueMultiSaveError

        `saved_field_names` - an iterable of field names (strings) that were
        successfully saved before the exception occured
        """
        # Exception is an old-style class, so can't use super
        Exception.__init__(self)

        self.saved_field_names = saved_field_names
