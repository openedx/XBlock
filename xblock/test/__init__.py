"""Provide `DictKeyValueStore` for all XBlock/xblock tests"""
from xblock.runtime import KeyValueStore


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
