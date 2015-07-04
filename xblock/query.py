"""Summary"""


class Query(object):
    """
    Class for handling remote query operations
    """

    def __init__(self, field, remote_scope, bind):
        self._field = field
        self.remote_scope = remote_scope
        self._bind = bind
        self._queryable = Queryable()

    def __get__(self, xblock, xblock_class):
        if xblock is None:
            return self
        return self._queryable

    def __set__(self, xblock, val):
        print val
    
    @property
    def field(self):
        """
        Returns the outer field object
        """
        return self._field

    def get_bind(self):
        """Summary
        
        Returns:
            TYPE: Description
        """
        return self._bind

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

    def __init__(self, values=None):
        self._values = values

    @property
    def values(self):
        """Summary
        
        Returns:
            TYPE: Description
        """
        if callable(self._values):
            return self._values()
        else:
            return self._values


    def get(self, user_selector=None, value_selector=None):
        """
        The get operator for Queryable class
        """
        if isinstance(user_selector, basestring):
            # handle a id
            pass
        elif all(isinstance(item, basestring) for item in user_selector):
            # handle a list of ids
            pass
        else:
            raise TypeError

    def find(self, user_selector=None, value_selector=None):
        """
        The find operator for Queryable class
        """
        pass

    def set(self, values):
        """
        The set operator for Queryable class
        """
        self._values = values
