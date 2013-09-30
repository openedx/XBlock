"""
Tools for testing XBlocks
"""

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


def blocks_are_equivalent(block1, block2):
    """Compare two blocks for equivalence.
    """
    # The two blocks have to be the same class.
    if block1.__class__ != block2.__class__:
        return False

    # They have to have the same fields.
    if set(block1.fields) != set(block2.fields):
        return False

    # The data fields have to have the same values.
    for field_name in block1.fields:
        if field_name in ('parent', 'children'):
            continue
        if getattr(block1, field_name) != getattr(block2, field_name):
            return False

    # The children need to be equal.
    if block1.has_children != block2.has_children:
        return False

    if block1.has_children:
        if len(block1.children) != len(block2.children):
            return False

        for child_id1, child_id2 in zip(block1.children, block2.children):
            if child_id1 == child_id2:
                # Equal ids mean they must be equal, check the next child.
                continue

            # Load up the actual children to see if they are equal.
            child1 = block1.runtime.get_block(child_id1)
            child2 = block2.runtime.get_block(child_id2)
            if not blocks_are_equivalent(child1, child2):
                return False

    return True
