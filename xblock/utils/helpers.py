"""
Useful helper methods
"""
from opaque_keys.edx.keys import UsageKey, DefinitionKey

from xblock.core import XBlock


def child_isinstance(block: XBlock, child_id: UsageKey, block_class_or_mixin: type):
    """
    Efficiently check if a child of an XBlock is an instance of the given class.

    Arguments:
    block -- the parent (or ancestor) of the child block in question
    child_id -- the usage key of the child block we are wondering about
    block_class_or_mixin -- We return true if block's child identified by child_id is an
    instance of this.

    This method is equivalent to

        isinstance(block.runtime.get_block(child_id), block_class_or_mixin)

    but is far more efficient, as it avoids the need to instantiate the child.
    """
    def_id: DefinitionKey = block.runtime.id_reader.get_definition_id(child_id)
    type_name: str = block.runtime.id_reader.get_block_type(def_id)
    child_class: type[XBlock] = block.runtime.load_block_type(type_name)
    return issubclass(child_class, block_class_or_mixin)
