"""
Tools for testing XBlocks
"""

import copy

from xblock.fields import UNSET
from xblock.runtime import FieldData, KeyValueStore


class DictModel(FieldData):
    """
    A field_data that just uses a single supplied dictionary to store fields by name
    """
    def __init__(self, data):
        self._data = data

    def get(self, block, name, default=UNSET):
        if default is UNSET:
            return copy.deepcopy(self._data[name])
        else:
            return copy.deepcopy(self._data.get(name, default))

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


class DictKeyValueStore(KeyValueStore):
    """
    Mock key value store backed by a dictionary.
    """
    def __init__(self):
        self.db_dict = {}

    def get(self, key):
        return self.db_dict[key]

    def set(self, key, value):
        self.db_dict[key] = value

    def set_many(self, other_dict):
        self.db_dict.update(other_dict)

    def delete(self, key):
        del self.db_dict[key]

    def has(self, key):
        return key in self.db_dict
