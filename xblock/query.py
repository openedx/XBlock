"""
    Define Query and Shared objects. Query supports ad-hoc queries via get, find, set operators.
    Shared uses `bind` functions to access data from pre-defined entities.  
"""

from xblock.exceptions import SharedFieldAccessDeniedError

class Query(object):
    """
    Class for handling remote query operations
    """

    def __init__(self, field_name):
        self._queryable = Queryable(field_name=field_name, remote_scope=None)

    def __get__(self, xblock, xblock_class):
        if xblock is None:
            return self

        self._queryable.attach_current_block(xblock)
        return self._queryable

    def __set__(self, xblock, val):
        pass

class Shared(object):
    """
    Class for handling shared field operations
    """
    def __init__(self, field_name, bind_attr_name):
        self._bind_attr_name = bind_attr_name
        self._queryable = Queryable(field_name=field_name)
    
    def __get__(self, xblock, xblock_class):
        if xblock is None:
            return self

        bind = getattr(xblock, self._bind_attr_name)
        self._queryable.attach_current_block(xblock)
        return self._queryable.get(**bind)

    def __set__(self, xblock, value):
        bind = getattr(xblock, self._bind_attr_name)
        self._queryable.attach_current_block(xblock)
        return self._queryable.set(value=value, **bind)


class Queryable(object):
    """
    Class for Queryable objects
    """

    def __init__(self, field_name=None, remote_scope=None):
        self._field_name = field_name
        self._remote_scope = remote_scope
        self.current_block = None

    @property
    def remote_scope(self):
        return self._remote_scope
    
    @property
    def field_name(self):
        return self._field_name

    def attach_current_block(self, block):
        self.current_block = block

    def _attach_query_to_field(self, xblock, field_name):
        xblock.fields[field_name].queryable = self

    def _detach_query_to_field(self, xblock, field_name):
        xblock.fields[field_name].queryable = None

    def _get_target_block(self, current_block, user_id, usage_id):

        if usage_id is None:
            target_block = current_block.runtime.get_remote_block(user_id, current_block.scope_ids.usage_id)
        else:
            target_block = current_block.runtime.get_remote_block(user_id, usage_id)

        print target_block.scope_ids

        return target_block

    def _check_remote_scope_premission(self, field_name, current_block, target_block):
        from xblock.fields import RemoteScope

        try:
            target_remote_scope = target_block.fields[field_name].remote_scope
        except KeyError:
            raise SharedFieldAccessDeniedError
        current_scope_ids = current_block.scope_ids
        target_scope_ids = target_block.scope_ids

        ## TODO: finish these checks
        if target_remote_scope is None:
            raise SharedFieldAccessDeniedError
        
        if target_remote_scope == RemoteScope.course_users:
            if current_scope_ids.def_id != target_scope_ids.def_id:
                raise SharedFieldAccessDeniedError
        
        elif target_remote_scope == RemoteScope.my_block_type:
            if current_scope_ids.user_id != target_remote_scope.user_id:
                raise SharedFieldAccessDeniedError
            if current_scope_ids.block_type != target_remote_scope.block_type:
                raise SharedFieldAccessDeniedError

    def get(self, user_id=None, usage_id=None):
        """
        The get operator for Queryable class
        """
        field_name = self._field_name
        current_block = self.current_block
        target_block = self._get_target_block(current_block, user_id, usage_id)
     
        try:
            self._check_remote_scope_premission(field_name, current_block, target_block)
        except SharedFieldAccessDeniedError:
            return None

        field_data = target_block._field_data

        self._attach_query_to_field(target_block, field_name)
        try:
            target_field = target_block.fields[field_name]
            value = target_field.from_json(field_data.get(target_block, field_name))
        except KeyError:
            try:
                value = target_block.fields[field_name].default
            except KeyError:
                value = None
        self._detach_query_to_field(target_block, field_name)

        return value

    def set(self, value, user_id=None, usage_id=None):
        """
        The set operator for Queryable class
        """
        field_name = self._field_name
        current_block = self.current_block
        target_block = self._get_target_block(current_block, user_id, usage_id)

        field_data = target_block._field_data

        try:
            self._check_remote_scope_premission(field_name, current_block, target_block)
        except SharedFieldAccessDeniedError:
            return

        self._attach_query_to_field(target_block, field_name)
        field_data.set(target_block, field_name, value)
        self._detach_query_to_field(target_block, field_name)