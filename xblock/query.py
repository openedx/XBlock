"""
    Define Query and Shared objects. Query supports ad-hoc queries via get, find, set operators.
    Shared uses `bind` functions to access data from pre-defined entities.  
"""

from copy import deepcopy

class Query(object):
    """
    Class for handling remote query operations
    """

    def __init__(self, field_name, remote_scope):
        self._queryable = Queryable(field_name, remote_scope)

    def __get__(self, field, field_class):
        """Summary
        
        Args:
            field (TYPE): Description
            field_class (TYPE): Description
        
        Returns:
            TYPE: Description
        """
        return self._queryable

    def __set__(self, field, val):
        print val

class Shared(object):
    """
    Class for handling shared field operations
    """
    def __init__(self, field_name, remote_scope, bind_attr):
        self._bind_attr = bind_attr
        self._queryable = Queryable(field_name, remote_scope)
    
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

    def __init__(self, field_name, remote_scope):
        self._field_name = field_name
        self._remote_scope = remote_scope

    @property
    def field_name(self):
        return self._field_name

    @property
    def remote_scope(self):
        return self._remote_scope

    def _replace_xblock_user_id(self, xblock, user_id):
        from xblock.fields import ScopeIds

        new_block = deepcopy(xblock)
        new_scope_ids = ScopeIds(user_id, xblock.scope_ids.block_type, xblock.scope_ids.def_id, xblock.scope_ids.usage_id)
        new_block.scope_ids = new_scope_ids
        return new_block

    def _attach_query_to_field(self, xblock):
        xblock.fields[self._field_name].query = self

    def _detach_query_to_field(self, xblock):
        xblock.fields[self._field_name].query = None

    def get(self, xblock=None, user_id=None):
        """
        The get operator for Queryable class
        """
        field_data = xblock._field_data

        if isinstance(user_id, basestring):
            # attach the query to field so lower call knows this is a query get (so that it can disable some assert checks)
            new_block = self._replace_xblock_user_id(xblock, user_id)

            try:
                self._attach_query_to_field(new_block)
                value = field_data.get(new_block, self._field_name)
                self._detach_query_to_field(new_block)
            except KeyError:
                value = None
            del new_block
            
            return value
        
        elif all(isinstance(item, basestring) for item in user_id):
            # handle a list of ids
            raise NotImplementedError
        
        else:
            raise TypeError

    def find(self, user_id=None):
        """
        The find operator for Queryable class
        """
        pass

    def set(self, value, xblock=None, user_id=None):
        """
        The set operator for Queryable class
        """
        field_data = xblock._field_data

        if isinstance(user_id, basestring):
            self._attach_query_to_field(xblock)
            new_block = self._replace_xblock_user_id(xblock, user_id)
            field_data.set(new_block, self._field_name, value)
            self._detach_query_to_field(xblock)
            del new_block

        elif all(isinstance(item, basestring) for item in user_id):
            # handle a list of ids
            raise NotImplementedError
        
        else:
            raise TypeError
