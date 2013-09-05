"""
Fields are used to provide XBlocks with a storage mechanism that provides
abstract notions of scopes (per-user vs global, across all blocks vs local to a particular
block), while allowing the hosting Runtime Application to decide what the actual
storage mechanism is.
"""

import copy
from collections import namedtuple

UNSET = object()


class BlockScope(object):
    """Enumeration defining BlockScopes"""
    USAGE, DEFINITION, TYPE, ALL = xrange(4)


class UserScope(object):
    """
    Enumeration of valid UserScopes

    NONE: This scope identifies data agnostic to the user of the xblock
        For instance, the definition of a randomized problem
    ONE: This scope identifies data supplied by a single user of the xblock
        For instance, a students answer to a randomized problem
    ALL: This scope identifies data aggregated while the block is used
        by many users.
        For instance, a histogram of the answers submitted by all students
    """
    NONE, ONE, ALL = xrange(3)


class Sentinel(object):
    """
    Class for implementing sentinel objects (only equal to themselves).
    """
    def __init__(self, name):
        """
        `name` is the name used to identify the sentinel (which will
            be displayed as the __repr__) of the sentinel.
        """
        self.name = name

    def __repr__(self):
        return self.name


ScopeBase = namedtuple('ScopeBase', 'user block')  # pylint: disable=C0103


class Scope(ScopeBase):
    """
    Defines six types of Scopes to be used: `content`, `settings`,
    `user_state`, `preferences`, `user_info`, and `user_state_summary`.

    The `content` scope is used to save data for all users, for one particular
    block, across all runs of a course. An example might be an XBlock that
    wishes to tabulate user "upvotes", or HTML content ti display literally on
    the page (this example being the reason this scope is named `content`).

    The `settings` scope is used to save data for all users, for one particular block,
    for one specific run of a course. This is like the `content` scope, but scoped to
    one run of a course. An example might be a due date for a problem.

    The `user_state` scope is used to save data for one user, for one block, for one run
    of a course. An example might be how many points a user scored on one specific problem.

    The `preferences` scope is used to save data for one user, for all instances of one
    specific TYPE of block, across the entire platform. An example might be that a user
    can set their preferred default speed for the video player. This default would apply
    to all instances of the video player, across the whole platform, but only for that student.

    The `user_info` scope is used to save data for one user, across the entire platform. An
    example might be a user's time zone or language preference.

    The `user_state_summary` scope is used to save data aggregated across many users of a
    single block. For example, a block might store a histogram of the points scored by all
    users attempting a problem.

    """

    content = ScopeBase(user=UserScope.NONE, block=BlockScope.DEFINITION)
    settings = ScopeBase(user=UserScope.NONE, block=BlockScope.USAGE)
    user_state = ScopeBase(user=UserScope.ONE, block=BlockScope.USAGE)
    preferences = ScopeBase(user=UserScope.ONE, block=BlockScope.TYPE)
    user_info = ScopeBase(user=UserScope.ONE, block=BlockScope.ALL)
    user_state_summary = ScopeBase(user=UserScope.ALL, block=BlockScope.USAGE)

    children = Sentinel('Scope.children')
    parent = Sentinel('Scope.parent')


ScopeIds = namedtuple('ScopeIds', 'student_id block_type def_id usage_id')  # pylint: disable=C0103


# define a placeholder ('nil') value to indicate when nothing has been stored
# in the cache ("None" may be a valid value in the cache, so we cannot use it).
NO_CACHE_VALUE = object()

# define a placeholder value that indicates that a value is explicitly dirty,
# because it was explicitly set
EXPLICITLY_SET = object()


class Field(object):
    """
    A field class that can be used as a class attribute to define what data the
    class will want to refer to.

    When the class is instantiated, it will be available as an instance
    attribute of the same name, by proxying through to self._field_data on
    the containing object.

    Parameters:
      `help` : documentation of field class, suitable for presenting in a GUI
          (defaults to None).
      `default` : static value to default to if not otherwise specified
          (defaults to None).
      `scope` : the scope in which this field class is used (defaults to
          Scope.content).
      `display_name` : the display name for the field class, suitable for
          presenting in a GUI (defaults to name of class).
      `values` : for field classes with a known set of valid values, provides
          the ability to explicitly specify the valid values. This can
          be specified as either a static return value, or a function
          that generates the valid values. For example formats, see the
          values property definition.
    """
    MUTABLE = True
    _default = None

    # We're OK redefining built-in `help`
    # pylint: disable=W0622
    def __init__(self, help=None, default=UNSET, scope=Scope.content,
                 display_name=None, values=None):
        self._name = "unknown"
        self.help = help
        if default is not UNSET:
            self._default = default
        self.scope = scope
        self._display_name = display_name
        self._values = values
    # pylint: enable=W0622

    @property
    def default(self):
        """Returns the static value that this defaults to."""
        if self.MUTABLE:
            return copy.deepcopy(self._default)
        else:
            return self._default

    @property
    def name(self):
        """Returns the name of this field."""
        # This is set by ModelMetaclass
        return self._name

    @property
    def values(self):
        """
        Returns the valid values for this class. This is useful
        for representing possible values in a UI.

        Example formats:
            `[1, 2, 3]` : a finite set of elements
            `[{"display_name": "Always", "value": "always"},
              {"display_name": "Past Due", "value": "past_due"}]` :
                a finite set of elements where the display names differ from
                the values
            `{"min" : 0 , "max" : 10, "step": .1}` :
                a range for floating point numbers with increment .1

        If this field class does not define a set of valid values, this method
        will return None.
        """
        if callable(self._values):
            return self._values()
        else:
            return self._values

    @property
    def display_name(self):
        """
        Returns the display name for this class, suitable for use in a GUI.

        If no display name has been set, returns the name of the class.
        """
        return self._display_name if self._display_name is not None else self.name

    def _get_cached_value(self, xblock):
        """
        Return a value from the xblock's cache, or a marker value if either the cache
        doesn't exist or the value is not found in the cache.
        """
        return getattr(xblock, '_field_data_cache', {}).get(self.name, NO_CACHE_VALUE)

    def _set_cached_value(self, xblock, value):
        """Store a value in the xblock's cache, creating the cache if necessary."""
        # Allow this method to access the `_field_data_cache` of `xblock`
        # pylint: disable=W0212
        if not hasattr(xblock, '_field_data_cache'):
            xblock._field_data_cache = {}
        xblock._field_data_cache[self.name] = value

    def _del_cached_value(self, xblock):
        """Remove a value from the xblock's cache, if the cache exists."""
        # Allow this method to access the `_field_data_cache` of `xblock`
        # pylint: disable=W0212
        if hasattr(xblock, '_field_data_cache') and self.name in xblock._field_data_cache:
            del xblock._field_data_cache[self.name]

    def _mark_dirty(self, xblock, value):
        """Set this field to dirty on the xblock."""
        # Allow this method to access the `_dirty_fields` of `xblock`
        # pylint: disable=W0212

        # Deep copy the value being marked as dirty, so that there
        # is a baseline to check against when saving later
        if self not in xblock._dirty_fields:
            xblock._dirty_fields[self] = copy.deepcopy(value)

    def _is_dirty(self, xblock):
        """
        Return whether this field should be saved when xblock.save() is called
        """
        if self not in xblock._dirty_fields:
            return False

        baseline = xblock._dirty_fields[self]
        return baseline is EXPLICITLY_SET or xblock._field_data_cache[self.name] != baseline

    def __get__(self, xblock, xblock_class):
        """
        Gets the value of this xblock. Prioritizes the cached value over
        obtaining the value from the _field_data. Thus if a cached value
        exists, that is the value that will be returned.
        """
        # Allow this method to access the `_field_data_cache` of `xblock`
        # pylint: disable=W0212
        if xblock is None:
            return self

        value = self._get_cached_value(xblock)
        if value is NO_CACHE_VALUE:
            if xblock._field_data.has(xblock, self.name):
                value = self.from_json(xblock._field_data.get(xblock, self.name))
            else:
                # Cache default value
                try:
                    value = self.from_json(xblock._field_data.default(xblock, self.name))
                except KeyError:
                    value = self.default

            self._set_cached_value(xblock, value)

        # If this is a mutable type, mark it as dirty, since mutations can occur without an
        # explicit call to __set__ (but they do require a call to __get__)
        if self.MUTABLE:
            self._mark_dirty(xblock, value)

        return value

    def __set__(self, xblock, value):
        """
        Sets the `xblock` to the given `value`.
        Setting a value does not update the underlying data store; the
        new value is kept in the cache and the xblock is marked as
        dirty until `save` is explicitly called.
        """
        # Mark the field as dirty and update the cache:
        self._mark_dirty(xblock, EXPLICITLY_SET)
        self._set_cached_value(xblock, value)

    def __delete__(self, xblock):
        """
        Deletes `xblock` from the underlying data store.
        Deletes are not cached; they are performed immediately.
        """
        # Allow this method to access the `_field_data` and `_dirty_fields` of `xblock`
        # pylint: disable=W0212

        # Try to perform the deletion on the field_data, and accept
        # that it's okay if the key is not present.  (It may never
        # have been persisted at all.)
        try:
            xblock._field_data.delete(xblock, self.name)
        except KeyError:
            pass

        # We also need to clear this item from the dirty fields, to prevent
        # an erroneous write of its value on implicit save. OK if it was
        # not in the dirty fields to begin with.
        try:
            del xblock._dirty_fields[self]
        except KeyError:
            pass

        # Since we know that the field_data no longer contains the value, we can
        # avoid the possible database lookup that a future get() call would
        # entail by setting the cached value now to its default value.
        self._set_cached_value(xblock, copy.deepcopy(self.default))

    def __repr__(self):
        return "<{0.__class__.__name__} {0._name}>".format(self)

    def to_json(self, value):
        """
        Return value in the form of nested lists and dictionaries (suitable
        for passing to json.dumps).

        This is called during field writes to convert the native python
        type to the value stored in the database
        """
        return value

    def from_json(self, value):
        """
        Return value as a native full featured python type (the inverse of to_json)

        Called during field reads to convert the stored value into a full featured python
        object
        """
        return value

    def read_from(self, xblock):
        """
        Retrieve the value for this field from the specified xblock
        """
        return self.__get__(xblock, xblock.__class__)

    def read_json(self, xblock):
        """
        Retrieve the serialized value for this field from the specified xblock
        """
        return self.to_json(self.read_from(xblock))

    def write_to(self, xblock, value):
        """
        Set the value for this field to value on the supplied xblock
        """
        self.__set__(xblock, value)

    def delete_from(self, xblock):
        """
        Delete the value for this field from the supplied xblock
        """
        self.__delete__(xblock)

    def is_set_on(self, xblock):
        """
        Return whether this field has a non-default value on the supplied xblock
        """
        return self._is_dirty(xblock) or xblock._field_data.has(xblock, self.name)

    def __hash__(self):
        return hash(self.name)


class Integer(Field):
    """
    A field that contains an integer.

    The value, as stored, can be None, '' (which will be treated as None), a Python integer,
    or a value that will parse as an integer, ie., something for which int(value) does not throw an Error.

    Note that a floating point value will convert to an integer, but a string containing a floating point
    number ('3.48') will throw an Error.
    """
    MUTABLE = False

    def from_json(self, value):
        if value is None or value == '':
            return None
        return int(value)


class Float(Field):
    """
    A field that contains a float.

    The value, as stored, can be None, '' (which will be treated as None), a Python float,
    or a value that will parse as an float, ie., something for which float(value) does not throw an Error.
    """
    MUTABLE = False

    def from_json(self, value):
        if value is None or value == '':
            return None
        return float(value)


class Boolean(Field):
    """
    A field class for representing a boolean.

    The stored value can be either a Python bool, a string, or any value that will then be converted
    to a bool in the from_json method.

    Examples:
        True -> True
        'true' -> True
        'TRUE' -> True
        'any other string' -> False
        [] -> False
        ['123'] -> True
        None - > False

    This class has the 'values' property defined.
    """
    MUTABLE = False

    # We're OK redefining built-in `help`
    # pylint: disable=W0622
    def __init__(self, help=None, default=None, scope=Scope.content, display_name=None):
        super(Boolean, self).__init__(help, default, scope, display_name,
                                      values=({'display_name': "True", "value": True},
                                              {'display_name': "False", "value": False}))
    # pylint: enable=W0622

    def from_json(self, value):
        if isinstance(value, basestring):
            return value.lower() == 'true'
        else:
            return bool(value)


class Dict(Field):
    """
    A field class for representing a Python dict.

    The stored value must be either be None or a dict.
    """
    _default = {}

    def from_json(self, value):
        if value is None or isinstance(value, dict):
            return value
        else:
            raise TypeError('Value stored in a Dict must be None or a dict.')


class List(Field):
    """
    A field class for representing a list.

    The stored value can either be None or a list.
    """
    _default = []

    def from_json(self, value):
        if value is None or isinstance(value, list):
            return value
        else:
            raise TypeError('Value stored in an List must be None or a list.')


class String(Field):
    """
    A field class for representing a string.

    The stored value can either be None or a basestring instance.
    """
    MUTABLE = False

    def from_json(self, value):
        if value is None or isinstance(value, basestring):
            return value
        else:
            raise TypeError('Value stored in a String must be None or a string.')


class Any(Field):
    """
    A field class for representing any piece of data; type is not enforced.

    All methods are inherited directly from `Field`.
    """
    pass


class ModelMetaclass(type):
    """
    A metaclass to be used for classes that want to use Fields as class attributes
    to define data access.

    All class attributes that are Fields will be added to the 'fields' attribute on
    the instance.
    """
    def __new__(mcs, name, bases, attrs):
        new_class = super(ModelMetaclass, mcs).__new__(mcs, name, bases, attrs)

        fields = {}
        # Pylint tries to do fancy inspection for class methods/properties, and
        # in this case, gets it wrong

        # Loop through all of the baseclasses of cls, in
        # the order that methods are resolved (Method Resolution Order / mro)
        # and find all of their defined fields.
        #
        # Only save the first such defined field (as expected for method resolution)
        for base_class in new_class.mro():  # pylint: disable=E1101
            # We can't use inspect.getmembers() here, because that would
            # call the fields property again, and generate an infinite loop.
            # Instead, we loop through all of the attribute names, exclude the
            # 'fields' attribute, and then retrieve the value
            for attr_name in dir(base_class):
                attr_value = getattr(base_class, attr_name)
                if isinstance(attr_value, Field):
                    fields.setdefault(attr_name, attr_value)

                    # Allow the field to know what its name is
                    attr_value._name = attr_name  # pylint: disable=W0212

        new_class.fields = fields

        return new_class


class ChildrenModelMetaclass(type):
    """
    A ModelMetaclass that transforms the attribute `has_children = True`
    into a List field with an empty scope.
    """
    def __new__(mcs, name, bases, attrs):
        if (attrs.get('has_children', False) or
                any(getattr(base, 'has_children', False) for base in bases)):
            attrs['children'] = List(help='The ids of the children of this XBlock',
                                     scope=Scope.children)
        else:
            attrs['has_children'] = False

        return super(ChildrenModelMetaclass, mcs).__new__(mcs, name, bases, attrs)


class XBlockMixin(object):
    """
    Base class for XBlock Mixin classes. These classes can add new fields
    and new properties to all XBlocks created by a particular runtime.

    This doesn't use the ChildrenModelMetaclass, because it doesn't seem sensible
    to add children to a module not written to use them.
    """
    __metaclass__ = ModelMetaclass
