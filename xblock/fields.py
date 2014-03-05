"""
Fields declare storage for XBlock data.  They use abstract notions of
**scopes** to associate each field with particular sets of blocks and users.
The hosting runtime application decides what actual storage mechanism to use
for each scope.

"""

import copy
from collections import namedtuple


# __all__ controls what classes end up in the docs, and in what order.
__all__ = [
    'BlockScope', 'UserScope', 'Scope', 'ScopeIds',
    'Field',
    'Boolean', 'Dict', 'Float', 'Integer', 'List', 'String',
    'XBlockMixin',
]


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

    @property
    def attr_name(self):
        return self.name.lower().replace('.', '_')

    def __eq__(self, other):
        return isinstance(other, Sentinel) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


class BlockScope(object):
    """
    Enumeration of block scopes.

    The block scope specifies how a field relates to blocks.  A
    :class:`.BlockScope` and a :class:`.UserScope` are combined to make a
    :class:`.Scope` for a field.

    USAGE: The data is related to a particular use of a block in a course.

    DEFINITION: The data is related to the definition of the block.  Although
        unusual, one block definition can be used in more than one place in a
        course.

    TYPE: The data is related to all instances of this type of XBlock.

    ALL: The data is common to all blocks.  This can be useful for storing
        information that is purely about the student.

    """
    USAGE = Sentinel('BlockScope.USAGE')
    DEFINITION = Sentinel('BlockScope.DEFINITION')
    TYPE = Sentinel('BlockScope.TYPE')
    ALL = Sentinel('BlockScope.ALL')

    @classmethod
    def scopes(cls):
        return [cls.USAGE, cls.DEFINITION, cls.TYPE, cls.ALL]


class UserScope(object):
    """
    Enumeration of user scopes.

    The user scope specifies how a field relates to users.  A
    :class:`.BlockScope` and a :class:`.UserScope` are combined to make a
    :class:`.Scope` for a field.

    NONE: Identifies data agnostic to the user of the :class:`.XBlock`.  The
        data is related to no particular user.  All users see the same data.
        For instance, the definition of a problem.

    ONE: Identifies data particular to a single user of the :class:`.XBlock`.
        For instance, a student's answer to a problem.

    ALL: Identifies data aggregated while the block is used by many users.
        The data is related to all the users.  For instance, a count of how
        many students have answered a question, or a histogram of the answers
        submitted by all students.

    """
    NONE = Sentinel('UserScope.NONE')
    ONE = Sentinel('UserScope.ONE')
    ALL = Sentinel('UserScope.ALL')

    @classmethod
    def scopes(cls):
        return [cls.NONE, cls.ONE, cls.ALL]


UNSET = Sentinel("fields.UNSET")


ScopeBase = namedtuple('ScopeBase', 'user block name')  # pylint: disable=C0103


class Scope(ScopeBase):
    """
    Defines six types of scopes to be used: `content`, `settings`,
    `user_state`, `preferences`, `user_info`, and `user_state_summary`.

    The `content` scope is used to save data for all users, for one particular
    block, across all runs of a course. An example might be an XBlock that
    wishes to tabulate user "upvotes", or HTML content ti display literally on
    the page (this example being the reason this scope is named `content`).

    The `settings` scope is used to save data for all users, for one particular
    block, for one specific run of a course. This is like the `content` scope,
    but scoped to one run of a course. An example might be a due date for a
    problem.

    The `user_state` scope is used to save data for one user, for one block,
    for one run of a course. An example might be how many points a user scored
    on one specific problem.

    The `preferences` scope is used to save data for one user, for all
    instances of one specific TYPE of block, across the entire platform. An
    example might be that a user can set their preferred default speed for the
    video player. This default would apply to all instances of the video
    player, across the whole platform, but only for that student.

    The `user_info` scope is used to save data for one user, across the entire
    platform. An example might be a user's time zone or language preference.

    The `user_state_summary` scope is used to save data aggregated across many
    users of a single block. For example, a block might store a histogram of
    the points scored by all users attempting a problem.

    """
    content = ScopeBase(UserScope.NONE, BlockScope.DEFINITION, u'content')
    settings = ScopeBase(UserScope.NONE, BlockScope.USAGE, u'settings')
    user_state = ScopeBase(UserScope.ONE, BlockScope.USAGE, u'user_state')
    preferences = ScopeBase(UserScope.ONE, BlockScope.TYPE, u'preferences')
    user_info = ScopeBase(UserScope.ONE, BlockScope.ALL, u'user_info')
    user_state_summary = ScopeBase(UserScope.ALL, BlockScope.USAGE, u'user_state_summary')

    @classmethod
    def named_scopes(cls):
        """Return all named Scopes."""
        return [
            cls.content,
            cls.settings,
            cls.user_state,
            cls.preferences,
            cls.user_info,
            cls.user_state_summary
        ]

    @classmethod
    def scopes(cls):
        """Return all possible Scopes."""
        named_scopes = cls.named_scopes()
        return named_scopes + [
            cls(user, block)
            for user in UserScope.scopes()
            for block in BlockScope.scopes()
            if cls(user, block) not in named_scopes
        ]

    def __new__(cls, user, block, name=None):
        """Create a new Scope, with an optional name."""

        if name is None:
            name = u'{}_{}'.format(user, block)

        return ScopeBase.__new__(cls, user, block, name)

    children = Sentinel('Scope.children')
    parent = Sentinel('Scope.parent')

    def __unicode__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, Scope) and self.user == other.user and self.block == other.block


ScopeIds = namedtuple('ScopeIds', 'user_id block_type def_id usage_id')  # pylint: disable=C0103


# define a placeholder ('nil') value to indicate when nothing has been stored
# in the cache ("None" may be a valid value in the cache, so we cannot use it).
NO_CACHE_VALUE = Sentinel("fields.NO_CACHE_VALUE")

# define a placeholder value that indicates that a value is explicitly dirty,
# because it was explicitly set
EXPLICITLY_SET = Sentinel("fields.EXPLICITLY_SET")

# Fields that cannot have runtime-generated defaults. These are special,
# because they define the structure of XBlock trees.
NO_GENERATED_DEFAULTS = ('parent', 'children')


class Field(object):
    """
    A field class that can be used as a class attribute to define what data the
    class will want to refer to.

    When the class is instantiated, it will be available as an instance
    attribute of the same name, by proxying through to self._field_data on
    the containing object.

    Parameters:

        help (str): documentation for the field, suitable for presenting to a
            user (defaults to None).

        default: static value to default to if not otherwise specified
            (defaults to None).

        scope: this field's scope (defaults to Scope.content).

        display_name: the display name for the field, suitable for presenting
            to a user (defaults to name of the field).

        values: a specification of the valid values for this field. This can be
            specified as either a static specification, or a function that
            returns the specification. For example specification formats, see
            the values property definition.

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

        * A finite set of elements::

            [1, 2, 3]

        * A finite set of elements where the display names differ from the
          values::

            [
             {"display_name": "Always", "value": "always"},
             {"display_name": "Past Due", "value": "past_due"},
            ]

        * A range for floating point numbers with specific increments::

            {"min": 0 , "max": 10, "step": .1}

        If this field class does not define a set of valid values, this
        property will return None.

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
        # pylint: disable=protected-access
        if not hasattr(xblock, '_field_data_cache'):
            xblock._field_data_cache = {}
        xblock._field_data_cache[self.name] = value

    def _del_cached_value(self, xblock):
        """Remove a value from the xblock's cache, if the cache exists."""
        # pylint: disable=protected-access
        if hasattr(xblock, '_field_data_cache') and self.name in xblock._field_data_cache:
            del xblock._field_data_cache[self.name]

    def _mark_dirty(self, xblock, value):
        """Set this field to dirty on the xblock."""
        # pylint: disable=protected-access

        # Deep copy the value being marked as dirty, so that there
        # is a baseline to check against when saving later
        if self not in xblock._dirty_fields:
            xblock._dirty_fields[self] = copy.deepcopy(value)

    def _is_dirty(self, xblock):
        """
        Return whether this field should be saved when xblock.save() is called
        """
        # pylint: disable=protected-access
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
        # pylint: disable=protected-access
        if xblock is None:
            return self

        value = self._get_cached_value(xblock)
        if value is NO_CACHE_VALUE:
            if xblock._field_data.has(xblock, self.name):
                value = self.from_json(xblock._field_data.get(xblock, self.name))
            elif self.name not in NO_GENERATED_DEFAULTS:
                # Cache default value
                try:
                    value = self.from_json(xblock._field_data.default(xblock, self.name))
                except KeyError:
                    value = self.default
            else:
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
        # pylint: disable=protected-access

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
        # pylint: disable=protected-access
        return self._is_dirty(xblock) or xblock._field_data.has(xblock, self.name)

    def __hash__(self):
        return hash(self.name)


class Integer(Field):
    """
    A field that contains an integer.

    The value, as stored, can be None, '' (which will be treated as None), a
    Python integer, or a value that will parse as an integer, ie., something
    for which int(value) does not throw an error.

    Note that a floating point value will convert to an integer, but a string
    containing a floating point number ('3.48') will throw an error.

    """
    MUTABLE = False

    def from_json(self, value):
        if value is None or value == '':
            return None
        return int(value)


class Float(Field):
    """
    A field that contains a float.

    The value, as stored, can be None, '' (which will be treated as None), a
    Python float, or a value that will parse as an float, ie., something for
    which float(value) does not throw an error.

    """
    MUTABLE = False

    def from_json(self, value):
        if value is None or value == '':
            return None
        return float(value)


class Boolean(Field):
    """
    A field class for representing a boolean.

    The stored value can be either a Python bool, a string, or any value that
    will then be converted to a bool in the from_json method.

    Examples:

    ::

        True -> True
        'true' -> True
        'TRUE' -> True
        'any other string' -> False
        [] -> False
        ['123'] -> True
        None - > False

    """
    MUTABLE = False

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
            raise TypeError('Value stored in a Dict must be None or a dict, found %s' % type(value))


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
            raise TypeError('Value stored in an List must be None or a list, found %s' % type(value))


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
            raise TypeError('Value stored in a String must be None or a string, found %s' % type(value))


class Any(Field):
    """
    A field class for representing any piece of data; type is not enforced.

    All methods are inherited directly from `Field`.

    """
    pass


class Reference(Field):
    """
    An xblock reference. That is, a pointer to another xblock.

    It's up to the runtime to know how to dereference this field type, but the field type enables the
    runtime to know that it must do the interpretation.
    """
    pass


class ReferenceList(List):
    """
    An list of xblock references. That is, pointers to xblocks.

    It's up to the runtime to know how to dereference the elements of the list. The field type enables the
    runtime to know that it must do the interpretation.
    """
    # this could define from_json and to_json as list comprehensions calling from/to_json on the list eles,
    # but since Reference doesn't stipulate a definition for from/to, that seems unnecessary at this time.
    pass


class ReferenceValueDict(Dict):
    """
    A dictionary where the values are xblock references. That is, pointers to xblocks.

    It's up to the runtime to know how to dereference the elements of the list. The field type enables the
    runtime to know that it must do the interpretation.
    """
    # this could define from_json and to_json as list comprehensions calling from/to_json on the list eles,
    # but since Reference doesn't stipulate a definition for from/to, that seems unnecessary at this time.
    pass


class ModelMetaclass(type):
    """
    A metaclass for using Fields as class attributes to define data access.

    All class attributes that are Fields will be added to the 'fields'
    attribute on the class.

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
                    attr_value._name = attr_name  # pylint: disable=protected-access

        new_class.fields = fields

        return new_class


class ChildrenModelMetaclass(type):
    """
    A metaclass that transforms the attribute `has_children = True` into a List
    field with a children scope.

    """
    def __new__(mcs, name, bases, attrs):
        if (attrs.get('has_children', False) or
                any(getattr(base, 'has_children', False) for base in bases)):
            attrs['children'] = ReferenceList(
                help='The ids of the children of this XBlock',
                scope=Scope.children)
        else:
            attrs['has_children'] = False

        return super(ChildrenModelMetaclass, mcs).__new__(mcs, name, bases, attrs)


class XBlockMixin(object):
    """
    Base class for XBlock Mixin classes.

    XBlockMixin classes can add new fields and new properties to all XBlocks
    created by a particular runtime.

    """
    # This doesn't use the ChildrenModelMetaclass, because it doesn't seem
    # sensible to add children to a module not written to use them.
    __metaclass__ = ModelMetaclass
