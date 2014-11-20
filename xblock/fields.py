"""
Fields declare storage for XBlock data.  They use abstract notions of
**scopes** to associate each field with particular sets of blocks and users.
The hosting runtime application decides what actual storage mechanism to use
for each scope.

"""
import ast

from collections import namedtuple
import copy
import datetime
import dateutil.parser
import itertools
import json
import logging
import pytz
import traceback
import warnings
import json
import yaml


# __all__ controls what classes end up in the docs, and in what order.
__all__ = [
    'BlockScope', 'UserScope', 'Scope', 'ScopeIds',
    'Field',
    'Boolean', 'Dict', 'Float', 'Integer', 'List', 'String',
    'XBlockMixin',
]


class FailingEnforceTypeWarning(DeprecationWarning):
    """
    A warning triggered when enforce_type would cause a exception if enabled
    """
    pass


class ModifyingEnforceTypeWarning(DeprecationWarning):
    """
    A warning triggered when enforce_type would change a value if enabled
    """
    pass


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
        """ TODO: Look into namespace collisions. block.name_space == block_name.space
        """
        return self.name.lower().replace('.', '_')

    def __eq__(self, other):
        """ Equality is based on being of the same class, and having same name
        """
        return isinstance(other, Sentinel) and self.name == other.name

    def __hash__(self):
        """
        Use a hash of the name of the sentinel
        """
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
        """
        Return a list of valid/understood class scopes.
        """
        # Why do we need this? This should either
        # * Be bubbled to the places where it is used (AcidXBlock).
        # * Be automatic. Look for all members of a type.
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
        """
        Return a list of valid/understood class scopes.
        Why do we need this? I believe it is not used anywhere.
        """
        return [cls.NONE, cls.ONE, cls.ALL]


UNSET = Sentinel("fields.UNSET")


ScopeBase = namedtuple('ScopeBase', 'user block name')


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


ScopeIds = namedtuple('ScopeIds', 'user_id block_type def_id usage_id')


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
    attribute of the same name, by proxying through to the field-data service on
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

        enforce_type: whether the type of the field value should be enforced
            on set, using self.enforce_type, raising an exception if it's not
            possible to convert it. This provides a guarantee on the stored
            value type.

        xml_node: if set, the field will be serialized as a
            separate node instead of an xml attribute (default: False).

        kwargs: optional runtime-specific options/metadata. Will be stored as
            runtime_options.

    """
    MUTABLE = True
    _default = None

    # We're OK redefining built-in `help`
    def __init__(self, help=None, default=UNSET, scope=Scope.content,  # pylint:disable=redefined-builtin
                 display_name=None, values=None, enforce_type=False,
                 xml_node=False, **kwargs):
        self._name = "unknown"
        self.help = help
        self._enable_enforce_type = enforce_type
        if default is not UNSET:
            self._default = self._check_or_enforce_type(default)
        self.scope = scope
        self._display_name = display_name
        self._values = values
        self.runtime_options = kwargs
        self.xml_node = xml_node

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

    def _check_or_enforce_type(self, value):
        """
        Depending on whether enforce_type is enabled call self.enforce_type and
        return the result or call it and trigger a silent warning if the result
        is different or a Traceback

        To aid with migration, enable the warnings with:
            warnings.simplefilter("always", FailingEnforceTypeWarning)
            warnings.simplefilter("always", ModifyingEnforceTypeWarning)
        """
        if self._enable_enforce_type:
            return self.enforce_type(value)

        try:
            new_value = self.enforce_type(value)
        except:  # pylint: disable=bare-except
            message = u"The value {} could not be enforced ({})".format(
                value, traceback.format_exc().splitlines()[-1])
            warnings.warn(message, FailingEnforceTypeWarning, stacklevel=3)
        else:
            if value != new_value:
                message = u"The value {} would be enforced to {}".format(
                    value, new_value)
                warnings.warn(message, ModifyingEnforceTypeWarning, stacklevel=3)

        return value

    def __get__(self, xblock, xblock_class):
        """
        Gets the value of this xblock. Prioritizes the cached value over
        obtaining the value from the field-data service. Thus if a cached value
        exists, that is the value that will be returned.
        """
        # pylint: disable=protected-access
        if xblock is None:
            return self

        field_data = xblock._field_data

        value = self._get_cached_value(xblock)
        if value is NO_CACHE_VALUE:
            if field_data.has(xblock, self.name):
                value = self.from_json(field_data.get(xblock, self.name))
            elif self.name not in NO_GENERATED_DEFAULTS:
                # Cache default value
                try:
                    value = self.from_json(field_data.default(xblock, self.name))
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
        value = self._check_or_enforce_type(value)
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

    def _warn_deprecated_outside_JSONField(self):  # pylint: disable=invalid-name
        """Certain methods will be moved to JSONField.

        This warning marks calls when the object is not
        derived from that class.
        """
        if not isinstance(self, JSONField):
            logging.warn("Deprecated. JSONifiable fields should derive from JSONField")

    def to_json(self, value):
        """
        Return value in the form of nested lists and dictionaries (suitable
        for passing to json.dumps).

        This is called during field writes to convert the native python
        type to the value stored in the database
        """
        self._warn_deprecated_outside_JSONField()
        return value

    def from_json(self, value):
        """
        Return value as a native full featured python type (the inverse of to_json)

        Called during field reads to convert the stored value into a full featured python
        object
        """
        self._warn_deprecated_outside_JSONField()
        return value

    def to_string(self, value):
        """
        Return a JSON serialized string representation of the value.
        """
        self._warn_deprecated_outside_JSONField()
        value = json.dumps(
            self.to_json(value), indent=2,
            sort_keys=True, separators=(',', ': '))
        return value

    def from_string(self, serialized):
        """
        Returns a native value from a YAML serialized string representation.
        Since YAML is a superset of JSON, this is the inverse of to_string.)
        """
        self._warn_deprecated_outside_JSONField()
        value = yaml.safe_load(serialized)
        return self._check_or_enforce_type(value)

    def enforce_type(self, value):
        """
        Coerce the type of the value, if necessary

        Called on field sets to ensure that the stored type is consistent if the
        field was initialized with enforce_type=True

        This must not have side effects, since it will be executed to trigger
        a DeprecationWarning even if enforce_type is disabled
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
        self._warn_deprecated_outside_JSONField()
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


class JSONField(Field):
    """
    Field type which has a convenient JSON representation.
    """
    @classmethod
    def coerce_value(cls, value, goal_types):
        """
        When loading from XML, a more complex data structure may be serialized
        into a string. Attempt to load the value both from a JSON parser and
        from an AST literal, since some export functions just run str() on the
        values.

        If the result is not the right type, throw an error.
        """
        try:
            value = json.loads(value)
        except ValueError:
            try:
                value = ast.literal_eval(value)
            except (SyntaxError, ValueError):
                raise TypeError("Could not deserialize string {0}. Please ensure it is valid JSON.".format(repr(value)))
        if not isinstance(value, goal_types):
            raise TypeError("Value stored on {0} must be of types: {1}. Found {2}.".format(
                cls.__name__, repr(goal_types), type(value)))
        return value


class Integer(JSONField):
    """
    A field that contains an integer.

    The value, as loaded or enforced, can be None, '' (which will be treated as
    None), a Python integer, or a value that will parse as an integer, ie.,
    something for which int(value) does not throw an error.

    Note that a floating point value will convert to an integer, but a string
    containing a floating point number ('3.48') will throw an error.

    """
    MUTABLE = False

    def from_json(self, value):
        if value is None or value == '':
            return None
        return int(value)

    enforce_type = from_json


class Float(JSONField):
    """
    A field that contains a float.

    The value, as loaded or enforced, can be None, '' (which will be treated as
    None), a Python float, or a value that will parse as an float, ie.,
    something for which float(value) does not throw an error.

    """
    MUTABLE = False

    def from_json(self, value):
        if value is None or value == '':
            return None
        return float(value)

    enforce_type = from_json


class Boolean(JSONField):
    """
    A field class for representing a boolean.

    The value, as loaded or enforced, can be either a Python bool, a string, or
    any value that will then be converted to a bool in the from_json method.

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

    # We're OK redefining built-in `help`
    def __init__(self, help=None, default=UNSET, scope=Scope.content, display_name=None, **kwargs):  # pylint: disable=redefined-builtin
        super(Boolean, self).__init__(help, default, scope, display_name,
                                      values=({'display_name': "True", "value": True},
                                              {'display_name': "False", "value": False}),
                                      **kwargs)

    def from_json(self, value):
        if isinstance(value, basestring):
            return value.lower() == 'true'
        else:
            return bool(value)

    enforce_type = from_json


class Dict(JSONField):
    """
    A field class for representing a Python dict.

    The value, as loaded or enforced, must be either be None or a dict.

    """
    _default = {}

    def from_json(self, value):
        if value is None or isinstance(value, dict):
            return value
        elif isinstance(value, basestring):
            value = self.coerce_value(value, (dict, type(None)))
        else:
            raise TypeError('Value stored in a Dict must be None or a dict, found %s' % type(value))
        return value

    enforce_type = from_json


class List(JSONField):
    """
    A field class for representing a list.

    The value, as loaded or enforced, can either be None or a list.

    """
    _default = []

    def from_json(self, value):
        if value is None or isinstance(value, list):
            return value
        elif isinstance(value, basestring):
            value = self.coerce_value(value, (list, type(None)))
        else:
            raise TypeError('Value stored in a List must be None or a list, found %s' % type(value))
        return value

    enforce_type = from_json


class String(JSONField):
    """
    A field class for representing a string.

    The value, as loaded or enforced, can either be None or a basestring instance.

    """
    MUTABLE = False

    def from_json(self, value):
        if value is None or isinstance(value, basestring):
            return value
        else:
            raise TypeError('Value stored in a String must be None or a string, found %s' % type(value))

    def from_string(self, value):
        """String gets serialized and deserialized without quote marks."""
        return self.from_json(value)

    def to_string(self, value):
        """String gets serialized and deserialized without quote marks."""
        return self.to_json(value)

    enforce_type = from_json


class DateTime(JSONField):
    """
    A field for representing a datetime.

    The value, as loaded or enforced, can either be an ISO-formatted date string, a native datetime,
    or None.
    """

    DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'

    def from_json(self, value):
        """
        Parse the date from an ISO-formatted date string, or None.
        """
        if isinstance(value, basestring):

            # Parser interprets empty string as now by default
            if value == "":
                return None

            try:
                parsed_date = dateutil.parser.parse(value)
            except (TypeError, ValueError):
                raise ValueError("Could not parse {} as a date".format(value))

            if parsed_date.tzinfo is not None:  # pylint: disable=maybe-no-member
                parsed_date.astimezone(pytz.utc)  # pylint: disable=maybe-no-member
            else:
                parsed_date = parsed_date.replace(tzinfo=pytz.utc)  # pylint: disable=maybe-no-member

            return parsed_date

        if value is None:
            return None

        if isinstance(value, datetime.datetime):
            return value

        raise TypeError("Value should be loaded from a string, not {}".format(type(value)))

    def to_json(self, value):
        """
        Serialize the date as an ISO-formatted date string, or None.
        """
        if isinstance(value, datetime.datetime):
            return value.strftime(self.DATETIME_FORMAT)
        if value is None:
            return None
        raise TypeError("Value stored must be a datetime object, not {}".format(type(value)))

    def enforce_type(self, value):
        if isinstance(value, datetime.datetime) or value is None:
            return value

        return self.from_json(value)


class Any(JSONField):
    """
    A field class for representing any piece of data; type is not enforced.

    All methods are inherited directly from `Field`.

    THIS SHOULD BE DEPRECATED. THIS SHOULD EITHER BE ANY JSON DATA, OR IT MAKES NO SENSE
    """
    pass


class Reference(JSONField):
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


def scope_key(instance, xblock):
    """Generate a unique key for a scope that can be used as a
    filename, in a URL, or in a KVS.

    Our goal is to have a pretty, human-readable 1:1 encoding.

    This encoding is as good as we can do. It's reversable, but not
    trivial to reverse.

    Encoding scheme:
    Posix allows [A-Z][a-z][0-9]._-
    We'd like to have a _concise_ representation for common punctuation
    We're okay with a _non-concise_ representation for repeated or uncommon characters
    We keep [A-z][a-z][0-9] as is.
    We encode other common punctuation as pairs of ._-. This gives a total of 3*3=9 combinations.
    We're pretty careful to keep this nice. Where possible, we double characters. The most common
    other character (' ' and ':') are encoded as _- and -_
    We seperate field portions with /. This gives a natural directory
    tree. This is nice in URLs and filenames (although not so nice in
    urls.py)
    If a field starts with punctuatation, we prefix a _. This prevents hidden files.

    Uncommon characters, we encode as their ordinal value, surrounded by -.
    For example, tilde would be -126-.

    If a field is not used, we call it NONE.NONE. This does not
    conflict with fields with the same name, since they are escaped to
    NONE..NONE.

    Sample keys:

    Settings scope:
      animationxblock..animation..d0..u0/settings__fs/NONE.NONE
    User summary scope:
      animationxblock..animation..d0..u0/uss__fs/NONE.NONE
    User preferences, username is Aan.!a
      animation/pref__fs/Aan.._33_a

    """
    scope_key_dict = {}
    scope_key_dict['name'] = instance.name
    if instance.scope.user == UserScope.NONE or instance.scope.user == UserScope.ALL:
        pass
    elif instance.scope.user == UserScope.ONE:
        scope_key_dict['user'] = unicode(xblock.scope_ids.user_id)
    else:
        raise NotImplementedError()

    if instance.scope.block == BlockScope.TYPE:
        scope_key_dict['block'] = unicode(xblock.scope_ids.block_type)
    elif instance.scope.block == BlockScope.USAGE:
        scope_key_dict['block'] = unicode(xblock.scope_ids.usage_id)
    elif instance.scope.block == BlockScope.DEFINITION:
        scope_key_dict['block'] = unicode(xblock.scope_ids.def_id)
    elif instance.scope.block == BlockScope.ALL:
        pass
    else:
        raise NotImplementedError()

    replacements = list(itertools.product("._-", "._-"))
    substitution_list = dict(zip("./\\,_ +:-", ("".join(x) for x in replacements)))
    # Above runs in 4.7us, and generates a list of common substitutions:
    # {' ': '_-', '+': '-.', '-': '--', ',': '_.', '/': '._', '.': '..', ':': '-_', '\\': '.-', '_': '__'}

    key_list = []

    def encode(char):
        """
        Replace all non-alphanumeric characters with -n- where n
        is their UTF8 code.
        TODO: Test for UTF8 which is not ASCII
        """
        if char.isalnum():
            return char
        elif char in substitution_list:
            return substitution_list[char]
        else:
            return "_{}_".format(ord(char))

    for item in ['block', 'name', 'user']:
        if item in scope_key_dict:
            field = scope_key_dict[item]
            # Prevent injection of "..", hidden files, or similar.
            # First part adds a prefix. Second part guarantees
            # continued uniqueness.
            if field.startswith(".") or field.startswith("_"):
                field = "_" + field
            field = "".join(encode(char) for char in field)
        else:
            field = "NONE.NONE"
        key_list.append(field)

    key = "/".join(key_list)
    return key
