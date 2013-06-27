from xblock.runtime import KeyValueStore

class DictKeyValueStore(KeyValueStore):
    """
    Mock key value store backed by a dictionary.
    """
    def __init__(self):
        self.db = {}

    def get(self, key):
        return self.db[key]

    def set(self, key, value):
        self.db[key] = value

    def update(self, d):
        for key in d:
            self.db[key] = d[key]

    def delete(self, key):
        del self.db[key]

    def has(self, key):
        return key in self.db
