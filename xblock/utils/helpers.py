"""
Useful helper methods
"""


def child_isinstance(block, child_id, block_class_or_mixin):
    """
    Efficiently check if a child of an XBlock is an instance of the given class.

    Arguments:
    block -- the parent (or ancestor) of the child block in question
    child_id -- the usage key of the child block we are wondering about
    block_class_or_mixin -- We return true if block's child indentified by child_id is an
    instance of this.

    This method is equivalent to

        isinstance(block.runtime.get_block(child_id), block_class_or_mixin)

    but is far more efficient, as it avoids the need to instantiate the child.
    """
    def_id = block.runtime.id_reader.get_definition_id(child_id)
    type_name = block.runtime.id_reader.get_block_type(def_id)
    child_class = block.runtime.load_block_type(type_name)
    return issubclass(child_class, block_class_or_mixin)
