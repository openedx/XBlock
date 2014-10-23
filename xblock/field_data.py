"""
A :class:`FieldData` is used by :class:`~xblock.core.XBlock` to read and write
data to particular scoped fields by name. This allows individual runtimes to
provide varied persistence backends while keeping the API used by the `XBlock`
simple.
"""

import copy

from abc import ABCMeta, abstractmethod
from collections import defaultdict
from itertools import imap

from xblock.exceptions import InvalidScopeError, InvalidXBlockForRoutingError, FieldDataError, BadFieldDataComponent


class FieldData(object):
    """
    An interface allowing access to an XBlock's field values indexed by field names.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, block, name):
        """
        Retrieve the value for the field named `name` for the XBlock `block`.

        If no value is set, raise a `KeyError`.

        The value returned may be mutated without modifying the backing store.

        :param block: block to inspect
        :type block: :class:`~xblock.core.XBlock`
        :param name: field name to look up
        :type name: str
        """
        raise NotImplementedError

    @abstractmethod
    def set(self, block, name, value):
        """
        Set the value of the field named `name` for XBlock `block`.

        `value` may be mutated after this call without affecting the backing store.

        :param block: block to modify
        :type block: :class:`~xblock.core.XBlock`
        :param name: field name to set
        :type name: str
        :param value: value to set
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, block, name):
        """
        Reset the value of the field named `name` to the default for XBlock `block`.

        :param block: block to modify
        :type block: :class:`~xblock.core.XBlock`
        :param name: field name to delete
        :type name: str
        """
        raise NotImplementedError

    @abstractmethod
    def has(self, block, name):
        """
        Return whether or not the field named `name` has a non-default value for the XBlock `block`.

        It is expected that `has` does not raise `KeyError`s and (subclasses of) `FieldDataError`s that
        it can handle

        :param block: block to check
        :type block: :class:`~xblock.core.XBlock`
        :param name: field name
        :type name: str
        """
        try:
            self.get(block, name)
            return True
        except KeyError:
            return False

    def set_many(self, block, update_dict):
        """
        Update many fields on an XBlock simultaneously.

        :param block: the block to update
        :type block: :class:`~xblock.core.XBlock`
        :param update_dict: A map of field names to their new values
        :type update_dict: dict
        """
        for key, value in update_dict.items():
            self.set(block, key, value)

    def default(self, block, name):  # pylint: disable=unused-argument
        """
        Get the default value for this field which may depend on context or may just be the field's global
        default. The default behavior is to raise KeyError which will cause the caller to return the field's
        global default.

        :param block: the block containing the field being defaulted
        :type block: :class:`~xblock.core.XBlock`
        :param name: the field's name
        :type name: `str`
        """
        raise KeyError(repr(name))


class DictFieldData(FieldData):
    """
    A FieldData that uses a single supplied dictionary to store fields by name.
    """
    def __init__(self, data):
        self._data = data

    def get(self, block, name):
        return copy.deepcopy(self._data[name])

    def set(self, block, name, value):
        self._data[name] = copy.deepcopy(value)

    def delete(self, block, name):
        del self._data[name]

    def has(self, block, name):
        return name in self._data

    def set_many(self, block, update_dict):
        self._data.update(copy.deepcopy(update_dict))


class SplitFieldData(FieldData):
    """
    A FieldData that uses divides particular scopes between
    several backing FieldData objects.
    """

    def __init__(self, scope_mappings):
        """
        `scope_mappings` defines :class:`~xblock.field_data.FieldData` objects to use
        for each scope. If a scope is not a key in `scope_mappings`, then using
        a field of that scope will raise an :class:`~xblock.exceptions.InvalidScopeError`.

        :param scope_mappings: A map from Scopes to backing FieldData instances
        :type scope_mappings: `dict` of :class:`~xblock.fields.Scope` to :class:`~xblock.field_data.FieldData`
        """
        self._scope_mappings = scope_mappings

    def _field_data(self, block, name):
        """Return the field data for the field `name` on the :class:`~xblock.core.XBlock` `block`"""
        scope = block.fields[name].scope

        if scope not in self._scope_mappings:
            raise InvalidScopeError(scope)

        return self._scope_mappings[scope]

    def get(self, block, name):
        return self._field_data(block, name).get(block, name)

    def set(self, block, name, value):
        self._field_data(block, name).set(block, name, value)

    def set_many(self, block, update_dict):
        update_dicts = defaultdict(dict)
        for key, value in update_dict.items():
            update_dicts[self._field_data(block, key)][key] = value
        for field_data, update_dict in update_dicts.items():
            field_data.set_many(block, update_dict)

    def delete(self, block, name):
        self._field_data(block, name).delete(block, name)

    def has(self, block, name):
        return self._field_data(block, name).has(block, name)

    def default(self, block, name):
        return self._field_data(block, name).default(block, name)


class ReadOnlyFieldData(FieldData):
    """
    A FieldData that wraps another FieldData an makes all calls to set and delete
    raise :class:`~xblock.exceptions.InvalidScopeError`s.
    """
    def __init__(self, source):
        self._source = source

    def get(self, block, name):
        return self._source.get(block, name)

    def set(self, block, name, value):
        raise InvalidScopeError("{block}.{name} is read-only, cannot set".format(block=block, name=name))

    def delete(self, block, name):
        raise InvalidScopeError("{block}.{name} is read-only, cannot delete".format(block=block, name=name))

    def has(self, block, name):
        return self._source.has(block, name)

    def default(self, block, name):
        return self._source.default(block, name)


class OrderedFieldDataList(FieldData):
    """
    A FieldData composed of an ordered list of subordinate FieldDatas.

    Any operation that fails on one subordinate field data will be tried on the next.
    """
    HANDLED_EXCEPTIONS = (FieldDataError, KeyError)

    def __init__(self, field_data_list):
        """
        instantiation method.  `field_data_list` is the ordered list of subordinate field datas
        """
        if not field_data_list:
            raise BadFieldDataComponent()
        self._fd_list = field_data_list

    def get(self, block, name):
        """
        get cascades down all subordinates.

        This handle self.HANDLED_EXCEPTIONS so that cascading can continue.  If the name is not found in any field_data
        in self._fd_list, get raises KeyError (like a DictFieldData does)
        """
        for field_data in self._fd_list:
            try:
                return field_data.get(block, name)
            except self.HANDLED_EXCEPTIONS:
                continue
        raise KeyError(repr(name))

    def set(self, block, name, value):
        """
        set always goes to the first subordinate for now.  Setting all subordinates could be another possibility
        """
        self._fd_list[0].set(block, name, value)

    def delete(self, block, name):
        """
        delete cascades down all subordinates.

        This handles self.HANDLED_EXCEPTIONS so that cascading can continue
        """
        for field_data in self._fd_list:
            try:
                field_data.delete(block, name)
            except self.HANDLED_EXCEPTIONS:
                continue

    def has(self, block, name):
        """
        checks all subordinate field datas in turn if `name` can be found

        doesn't do special error handling b/c subordinate field datas are supposed to handle those cases.
        does use imap instead of map or list comprehension to do short-cutting
        """
        return any(imap(lambda field_data: field_data.has(block, name), self._fd_list))

    def set_many(self, block, update_dict):
        """
        set_many always goes to the first subordinate for now.  Setting all subordinates could be another possibility.
        """
        self._fd_list[0].set_many(block, update_dict)

    def default(self, block, name):
        """
        Try each component field data in turn.  KeyError indicates no default can be supplied by component field data.

        If default can't be supplied by any component field data, raise KeyError ourselves.
        """
        for field_data in self._fd_list:
            try:
                return field_data.default(block, name)
            except KeyError:
                continue
        raise KeyError(repr(name))


class XBlockRoutedFieldData(FieldData):
    """
    An FieldData that routes to subordinate FieldDatas by some key derived from the xblock being operated on

    This class contains a default implementation for _get_routing_key, which returns block.__class__, but overriding
    that can yield other desirable behavior in subclasses
    """
    KeyNotInMappingsExceptionClass = InvalidXBlockForRoutingError

    def __init__(self, mappings, routing_key_fn, unmapped_key_exception_class=None):
        """
        Initializes XBLockRoutedFieldData

        `mappings` is a dict with keys derived from some attribute of an xblock instance, and values that are FieldData
        `routing_key_fn` is a function of 1 argument, which should be an xblock instance, that returns a routing key
        `unmapped_key_exception_class` is the class of errors that this FieldData should raise when a routing key
            is not found in mappings
        """
        self._mappings = mappings
        self._routing_key_fn = routing_key_fn
        if unmapped_key_exception_class:
            self.KeyNotInMappingsExceptionClass = unmapped_key_exception_class

    def _get_routing_key(self, block):
        """
        returns the routing key derived from xblock instance `block`

        The default implementation is to return block.__class__.
        """
        return self._routing_key_fn(block)

    def _field_data(self, block):
        """
        Return the field data matching the key derived from the :class:`~xblock.core.XBlock` `block`
        """
        key = self._get_routing_key(block)
        if key not in self._mappings:
            raise self.KeyNotInMappingsExceptionClass(key)
        return self._mappings[key]

    def get(self, block, name):
        try:
            return self._field_data(block).get(block, name)
        except self.KeyNotInMappingsExceptionClass:
            raise KeyError(repr(name))

    def set(self, block, name, value):
        self._field_data(block).set(block, name, value)

    def set_many(self, block, update_dict):
        self._field_data(block).set_many(block, update_dict)

    def delete(self, block, name):
        self._field_data(block).delete(block, name)

    def has(self, block, name):
        try:
            return self._field_data(block).has(block, name)
        except self.KeyNotInMappingsExceptionClass:
            # If the appropriate subordinate FieldData doesn't exist, we want to indicate that this
            # field data doesn't have the name
            return False

    def default(self, block, name):
        try:
            return self._field_data(block).default(block, name)
        except self.KeyNotInMappingsExceptionClass:
            # If the appropriate subordinate FieldData doesn't exist, we want to indicate that this
            # field data can't provide a default by raising KeyError
            raise KeyError(repr(name))


def get_xblock_plugin_name(xblock):
    """
    Returns the plugin name of an xblock.

    This function is sometimes used to derive a xblock-routing key for XBlockRoutedFieldData
    """
    return xblock.plugin_name


def get_configuration_field_data(config_dict):
    """
    Returns a composed field data for Scope.configuration that's ordered, routed by xblock type, and read-only
    example `config_dict` is :
    {
        '_default': {
            'key1': 'val1'
            'key2': 'val2'
        },
        'thumbs': {
            'key2': 'val3',
        },
    }
    """
    default_fd = DictFieldData({})
    mappings = {}
    for key in config_dict:
        if key == "_default":
            default_fd = DictFieldData(config_dict[key])
        else:
            mappings[key] = DictFieldData(config_dict[key])
    return ReadOnlyFieldData(
        OrderedFieldDataList(
            [XBlockRoutedFieldData(mappings, get_xblock_plugin_name), default_fd]
        )
    )
