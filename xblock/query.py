"""
    Define Query and Shared objects. Query supports ad-hoc queries via get and set operators.
    Shared uses `bind` functions to access data from pre-defined entities.  
"""

from xblock.exceptions import SharedFieldAccessDeniedError

class Query(object):
    """ 
    A query object for accessing shared field in XBlock with Queryable operators

    Parameters:

        field_name (str): the name of the shared field
    """
    def __init__(self, field_name):
        self._file_name = field_name

    def __get__(self, xblock, xblock_class):
        if xblock is None:
            return self

        self._queryable = Queryable(field_name=self._file_name)
        # pylint: disable=protected-access
        self._queryable._attach_current_block(xblock)
        return self._queryable

    def __set__(self, xblock, val):
        raise AttributeError("can't set attribute")

class Shared(object):
    """
    A shared object for accesing shared fields in XBlock with descriptor protocol

    Parameters:

        field_name (str): the name of the shared field
        bind_attr_name (str): the name of XBlock instance property. 
            This property is used to get query information.  
    """
    def __init__(self, field_name, bind_attr_name):
        self._file_name = field_name
        self._bind_attr_name = bind_attr_name
    
    def __get__(self, xblock, xblock_class):
        if xblock is None:
            return self
        
        self._queryable = Queryable(field_name=self._file_name)
        bind = getattr(xblock, self._bind_attr_name)
        # pylint: disable=protected-access
        self._queryable._attach_current_block(xblock)
        return self._queryable.get(**bind)

    def __set__(self, xblock, value):
        self._queryable = Queryable(field_name=self._file_name)
        bind = getattr(xblock, self._bind_attr_name)
        # pylint: disable=protected-access
        self._queryable._attach_current_block(xblock)
        return self._queryable.set(value=value, **bind)


class Queryable(object):
    """
    A Queryable object that contains operations for reading and writing to shared fields.
    
    Parameters:
        field_name (str): the name of a shared field

    """

    def __init__(self, field_name=None):
        self._field_name = field_name
        self.current_block = None

    @property
    def field_name(self):
        """
        Return the name of shared field that this queryable object is working on
        
        Returns:
            str: a field name
        """
        return self._field_name

    def _attach_current_block(self, block):
        """
        Attach the current XBlock instance to this queryable object
        
        Args:
            block (XBlock): the current XBlock instance
        
        Returns:
            None
        """
        self.current_block = block

    def _attach_queryable_to_field(self, xblock, field_name):
        """
        Attach this queryable instance to xblock. The queryable
        instance is used by platform to know this is a call to
        a shared field.
        
        Args:
            xblock (XBlock): the target XBlock that is being queried
            field_name (str): the name of shared field
        
        Returns:
            None
        """
        xblock.fields[field_name].queryable = self

    def _detach_queryable_to_field(self, xblock, field_name):
        """
        Detach the queryable instance from a XBlock after queryies
        
        Args:
            xblock (XBlock): the target XBlock that has being queried
            field_name (TYPE): the name of shared field
        
        Returns:
            None
        """
        xblock.fields[field_name].queryable = None

    def _get_target_block(self, current_block, user_id, usage_id):
        """
        This method builds the target XBlock that is being queried 
        from user_id and usage_id
        
        Args:
            current_block (XBlock): Description
            user_id (str): the id of user that is being queried
            usage_id (str): the usage id of XBlock that is being queried
        
        Returns:
            XBlock: the target XBlock that is being queried
        """
        if usage_id is None:
            usage_id = current_block.scope_ids.usage_id

        return current_block.runtime.get_remote_block(user_id, usage_id)

    def _check_remote_scope_premission(self, field_name, current_block, target_block):
        """
        This method checks the defined remote scope in shared field
        with current xblock to determine if current xblock has the 
        permission to access the shared field in target xblock.

        Rise SharedFieldAccessDeniedError if permission denied. 
        
        Args:
            field_name (str): the name of shared field in target xblock
            current_block (XBlock): the current XBlock instance 
            target_block (XBlock): the target XBlock instance
        
        Returns:
            None
        """
        shared = target_block.fields[field_name].shared

        current_scope_ids = current_block.scope_ids
        target_scope_ids = target_block.scope_ids

        if shared:
        # We are not allowing cross-course sharing due to:
        # 1) Security concerns
        # 2) Demonstrates fine-grained access control
            if current_scope_ids.def_id.course_key != target_scope_ids.def_id.course_key:
                raise SharedFieldAccessDeniedError
        else:
            raise SharedFieldAccessDeniedError

    def get(self, user_id=None, usage_id=None):
        """
        The get operator for Queryable class
        
        Args:
            user_id (str): the id of user that is being queried
            usage_id (str, optional): the usage id of XBlock that is being queried
        """
        field_name = self._field_name
        current_block = self.current_block
        target_block = self._get_target_block(current_block, user_id, usage_id)
     
        try:
            self._check_remote_scope_premission(field_name, current_block, target_block)
        except SharedFieldAccessDeniedError:
            return None

        # pylint: disable=protected-access
        field_data = target_block._field_data

        self._attach_queryable_to_field(target_block, field_name)
        try:
            target_field = target_block.fields[field_name]
            value = target_field.from_json(field_data.get(target_block, field_name))
        except KeyError:
            try:
                value = target_block.fields[field_name].default
            except KeyError:
                value = None
        self._detach_queryable_to_field(target_block, field_name)

        return value

    def set(self, value, user_id=None, usage_id=None):
        """
        The set operator for Queryable class
        
        Args:
            value (any): the new value
            user_id (str): the id of user that is being queried
            usage_id (str, optional): the usage id of XBlock that is being queried
        """
        field_name = self._field_name
        current_block = self.current_block
        target_block = self._get_target_block(current_block, user_id, usage_id)

        # pylint: disable=protected-access
        field_data = target_block._field_data

        try:
            self._check_remote_scope_premission(field_name, current_block, target_block)
        except SharedFieldAccessDeniedError:
            return

        self._attach_queryable_to_field(target_block, field_name)
        field_data.set(target_block, field_name, value)
        self._detach_queryable_to_field(target_block, field_name)
