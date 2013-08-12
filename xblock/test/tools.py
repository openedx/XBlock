"""
Tools for testing XBlocks
"""

from xblock.fields import UNSET
from xblock.runtime import ModelData


class DictModel(ModelData):
    """
    A model_data that just uses a single supplied dictionary to store fields by name
    """
    def __init__(self, data):
        self._data = data

    def get(self, block, name, default=UNSET):
        if default is UNSET:
            return self._data[name]
        else:
            return self._data.get(name, default)

    def set(self, block, name, value):
        self._data[name] = value

    def delete(self, block, name):
        del self._data[name]

    def has(self, block, name):
        return name in self._data

    def set_many(self, block, update_dict):
        self._data.update(update_dict)

    def default(self, block, name):
        raise KeyError
