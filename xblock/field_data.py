"""
A :class:`FieldData` is used by :class:`~xblock.core.XBlock` to read and write
data to particular scoped fields by name. This allows individual runtimes to
provide varied persistence backends while keeping the API used by the `XBlock`
simple.
"""

import copy


class FieldData(object):
    """
    An interface allowing access to an XBlock's field values indexed by field names
    """
    def get(self, block, name):
        """
        Retrieve the value for the field named `name` for the XBlock `block`.

        If no value is set, raise a `KeyError`

        The value returned may be mutated without modifying the backing store

        :param block: block to inspect
        :type block: :class:`~xblock.core.XBlock`
        :param name: field name to look up
        :type name: str
        """
        raise NotImplementedError

    def set(self, block, name, value):
        """
        Set the value of the field named `name` for XBlock `block`.

        `value` may be mutated after this call without affecting the backing store

        :param block: block to modify
        :type block: :class:`~xblock.core.XBlock`
        :param name: field name to set
        :type name: str
        :param value: value to set
        """
        raise NotImplementedError

    def delete(self, block, name):
        """
        Reset the value of the field named `name` to the default for XBlock `block`.

        :param block: block to modify
        :type block: :class:`~xblock.core.XBlock`
        :param name: field name to delete
        :type name: str
        """
        raise NotImplementedError

    def has(self, block, name):
        """
        Return whether or not the field named `name` has a non-default value for the XBlock `block`

        :param block: block to check
        :type block: :class:`~xblock.core.XBlock`
        :param name: field name
        :type name: str
        """
        raise NotImplementedError

    def set_many(self, block, update_dict):
        """
        Update many fields on an XBlock simultaneously.

        :param block: the block to update
        :type block: :class:`~xblock.core.XBlock`
        :param update_dict: A map of field names to their new values
        :type update_dict: dict
        """
        for key, value in update_dict.items():
            self.set(block, key, value)

    def default(self, block, name):
        """
        Get the default value for this field which may depend on context or may just be the field's global
        default. The default behavior is to raise KeyError which will cause the caller to return the field's
        global default.

        :param block: the block containing the field being defaulted
        :type block: :class:`~xblock.core.XBlock`
        :param name: the field's name
        :type name: `str`
        """
        raise KeyError(name)


class DictFieldData(FieldData):
    """
    A field_data that just uses a single supplied dictionary to store fields by name
    """
    def __init__(self, data):
        self._data = data

    def get(self, block, name):
        return copy.deepcopy(self._data[name])

    def set(self, block, name, value):
        self._data[name] = copy.deepcopy(value)

    def delete(self, block, name):
        del self._data[name]

    def has(self, block, name):
        return name in self._data

    def set_many(self, block, update_dict):
        self._data.update(copy.deepcopy(update_dict))

    def default(self, block, name):
        raise KeyError

