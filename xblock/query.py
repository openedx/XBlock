"""
    Define Query and Shared objects. Query supports ad-hoc queries via get, find, set operators.
    Shared uses `bind` functions to access data from pre-defined entities.  
"""

from copy import deepcopy

class Query(object):
    """
    Class for handling remote query operations
    """

    def __init__(self, field_name, remote_scope, bind):
        self._queryable = Queryable()
        self._queryable.bind(field_name, remote_scope, bind)

    def __get__(self, field, field_class):
        """Get the queryable instance
        
        Args:
            xblock (TYPE): Description
            xblock_class (TYPE): Description
        
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
    def __init__(self):
        pass


class Queryable(object):
    """
    Class for Queryable objects
    """

    def __init__(self):
        self._field_name = "unknown"
        self._remote_scope = None
        self._bind = None

    @property
    def field_name(self):
        return self._field_name

    @property
    def remote_scope(self):
        return self._remote_scope
    

    def bind(self, field_name, remote_scope, bind):
        """Summary
        
        Args:
            field_name (TYPE): Description
            remote_scope (TYPE): Description
            bind (TYPE): Description
        
        Returns:
            TYPE: Description
        """
        self._field_name = field_name
        self._remote_scope = remote_scope
        self._bind = bind

    def _replace_xblock_user_id(self, xblock, user_id):
        new_block = deepcopy(xblock)
        from xblock.fields import ScopeIds
        new_scope_ids = ScopeIds(user_id, xblock.scope_ids.block_type, xblock.scope_ids.def_id, xblock.scope_ids.usage_id)
        new_block.scope_ids = new_scope_ids
        return new_block

    def _attach_query_to_field(self, xblock):
        xblock.fields[self._field_name].query = self

    def _detach_query_to_field(self, xblock):
        xblock.fields[self._field_name].query = None

    def get(self, xblock, user_name_selector=None, value_selector=None):
        """
        The get operator for Queryable class
        """
        field_data = xblock._field_data

        if isinstance(user_name_selector, basestring):
            # attach the query to field so lower call knows this is a remote get
            self._attach_query_to_field(xblock)
            new_block = self._replace_xblock_user_id(xblock, user_name_selector)
            value = field_data.get(new_block, self._field_name)
            # detach the query
            self._detach_query_to_field(xblock)
            del new_block
            return value
        
        elif all(isinstance(item, basestring) for item in user_name_selector):
            # handle a list of ids
            raise NotImplementedError
        
        else:
            raise TypeError

    def find(self, user_selector=None, value_selector=None):
        """
        The find operator for Queryable class
        """
        pass

    def set(self, xblock, user_name_selector, new_value):
        """
        The set operator for Queryable class
        """
        field_data = xblock._field_data

        if isinstance(user_name_selector, basestring):
            self._attach_query_to_field(xblock)
            new_block = self._replace_xblock_user_id(xblock, user_name_selector)
            field_data.set(new_block, self._field_name, new_value)
            self._detach_query_to_field(xblock)
            del new_block

        elif all(isinstance(item, basestring) for item in user_name_selector):
            # handle a list of ids
            raise NotImplementedError
        
        else:
            raise TypeError
