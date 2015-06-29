


class Query(object):
    """
    Class for handling remote query operations
    """
    def __init__(self, field, remote_scope, bind):
        self._field = field
        self.remote_scope = remote_scope
        self._bind = bind
        self._queryable = Queryable()
    
    @property
    def field(self):
        """
        Returns the outer field object
        """
        return self._field

    def get_bind(self):
        return self._bind

    def __get__(self, obj, objtype):
        if obj in None:
            return self
        return self._queryable

    def __set__(self, obj, val):
        pass

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

    def __init__(self, values):
        self._values = values
        pass

    @property
    def values(self):

        if callable(self._values):
            return self._values()
        else:
            return self._values


    def get(self, **args):
        """
        The get operator for Queryable class
        """
        pass

    def find(self):
        """
        The find operator for Queryable class
        """
        pass

    def set(self, values):
        """
        The set operator for Queryable class
        """
        self._values = values
        pass