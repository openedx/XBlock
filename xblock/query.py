


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
        print "in get"
        if xblock is None:
            return self
        return self._queryable

    def __set__(self, xblock, val):
        print val
        pass
    
    @property
    def field(self):
        """
        Returns the outer field object
        """
        return self._field

    def get_bind(self):
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

    def __init__(self, values = None):
        self._values = values
        pass

    @property
    def values(self):

        if callable(self._values):
            return self._values()
        else:
            return self._values


    def get(self, selector):
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
