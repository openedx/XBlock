"""
    Define Query and Shared objects. Query supports ad-hoc queries via get, find, set operators.
    Shared uses `bind` functions to access data from pre-defined entities.  
"""

from copy import deepcopy
from xblock.exceptions import InvalidScopeError

class Query(object):
    """
    Class for handling remote query operations
    """

    def __init__(self, remote_scope):
        self._queryable = Queryable(remote_scope)

    def __get__(self, field, field_class):
        return self._queryable

    def __set__(self, field, val):
        print val

class Shared(object):
    """
    Class for handling shared field operations
    """
    def __init__(self, remote_scope, bind_attr):
        self._bind_attr = bind_attr
        self._queryable = Queryable(remote_scope)
    
    def __get__(self, xblock, xblock_class):
        if xblock is None:
            return self
        bind = getattr(xblock, self._bind_attr)
        return self._queryable.get(xblock = xblock, **bind)

    def __set__(self, xblock, value):
        bind = getattr(xblock, self._bind_attr)
        return self._queryable.set(value = value, xblock = xblock, **bind)


class Queryable(object):
    """
    Class for Queryable objects
    """

    def __init__(self, remote_scope):
        self._remote_scope = remote_scope

    @property
    def remote_scope(self):
        return self._remote_scope

    def _replace_xblock_user_id(self, xblock, user_id):
        from xblock.fields import ScopeIds

        new_block = deepcopy(xblock)
        new_scope_ids = ScopeIds(user_id, xblock.scope_ids.block_type, xblock.scope_ids.def_id, xblock.scope_ids.usage_id)
        new_block.scope_ids = new_scope_ids
        return new_block

    def _attach_query_to_field(self, xblock, field_name):
        xblock.fields[field_name].query = self

    def _detach_query_to_field(self, xblock, field_name):
        xblock.fields[field_name].query = None

    def check_remote_scope_premission(self, field_name, current_block, target_block):
        ## TODO: finish this part with check if the target has the current remote_scope for sharing
        if target_block.fields[field_name].remote_scope is None:
            return False
        current_scope_ids = current_block.scope_ids
        target_scope_ids = target_block.scope_ids
        ## TODO: compare the information of these two scope ids based on target_block.remote_scope permission
        return True

    def get(self, xblock, field_name, user_id=None, usage_id=None):
        """
        The get operator for Queryable class
        """
        current_block = xblock
        if usage_id is None:
            target_block = xblock.runtime.get_remote_block(user_id, current_block.scope_ids.usage_id)
        else:
            target_block = xblock.runtime.get_remote_block(user_id, usage_id)

        if self.check_remote_scope_premission(field_name, current_block, target_block) == False:
            raise InvalidScopeError

        # TODO: handle usage_id and other block type
        field_data = target_block._field_data

        new_block = self._replace_xblock_user_id(target_block, user_id)
        # attach the query to field so field data calls know this is a query get 
        # (so that it can disable some assert checks)
        # FIXME: key error may happen here
        self._attach_query_to_field(new_block, field_name)
        if field_data.has(new_block, field_name):
            value = field_data.get(new_block, field_name)
        else:
            try:
                value = field_data.default(new_block, field_name)
            except KeyError:
                value = None
        self._detach_query_to_field(new_block, field_name)
        del new_block

        return value

    def set(self, value, xblock, field_name, user_id=None, usage_id=None):
        """
        The set operator for Queryable class
        """
        # TODO: handle usage_id
        field_data = xblock._field_data

        # FIXME: key error may happen here
        self._attach_query_to_field(xblock, field_name)
        new_block = self._replace_xblock_user_id(xblock, user_id)
        field_data.set(new_block, field_name, value)
        self._detach_query_to_field(xblock, field_name)
        del new_block