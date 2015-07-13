"""
    Define Query and Shared objects. Query supports ad-hoc queries via get, find, set operators.
    Shared uses `bind` functions to access data from pre-defined entities.  
"""

from copy import deepcopy

from xblock.field_data import SplitFieldData


class Query(object):
    """
    Class for handling remote query operations
    """

    def __init__(self):
        self._queryable = Queryable()

    def __get__(self, field, field_class):
        """Get the queryable instance
        
        Args:
            xblock (TYPE): Description
            xblock_class (TYPE): Description
        
        Returns:
            TYPE: Description
        """
        if field is None:
            return self

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
        self._field = None
        self._name = "_"
        self._remote_scope = None
        self._xblock = None
        self._values = None

    @property
    def field(self):
        """
        Returns the outer field object
        """
        return self._field

    @property
    def remote_scope(self):
        return self._remote_scope

    @property
    def xblock(self):
        return self._xblock

    @property
    def name(self):
        return self._name
    

    def bind(self, xblock, field, remote_scope, bind):
        """Bind necesary information and object to this queryable instance
        
        Args:
            xblock (TYPE): Description
            field (TYPE): Description
            remote_scope (TYPE): Description
            bind (TYPE): Description
        
        Returns:
            TYPE: Description
        """
        self._field = field
        self._xblock = xblock
        self._name = field.name
        self._remote_scope = remote_scope
        self._bind = bind

    def _replace_xblock_user_id(self, user_id):
        new_block = deepcopy(self._xblock)
        new_block.scope_ids.user_id = user_id
        return new_block

    def get(self, user_name_selector=None, value_selector=None):
        """
        The get operator for Queryable class
        """
        ## TODO: build a scope id by using user_name_selector
        field_data = self._xblock._field_data

        if isinstance(field_data, SplitFieldData) == False:
            raise TypeError

        if isinstance(user_selector, basestring):
            new_block = self._replace_xblock_user_id(user_selector)
            value = field_data.get(new_block, self._name)
        elif all(isinstance(item, basestring) for item in user_selector):
            # handle a list of ids
            raise NotImplementedError
        else:
            raise TypeError

    def find(self, user_selector=None, value_selector=None):
        """
        The find operator for Queryable class
        """
        pass

    def set(self, user_name_selector, values):
        """
        The set operator for Queryable class
        """
        self._values = values
