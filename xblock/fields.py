"""
Fields declare storage for XBlock data.  They use abstract notions of
**scopes** to associate each field with particular sets of blocks and users.
The hosting runtime application decides what actual storage mechanism to use
for each scope.

"""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
import re
import traceback
import typing as t
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

import dateutil.parser
import pytz
import yaml
from lxml import etree
from opaque_keys.edx.keys import DefinitionKey, UsageKey


if t.TYPE_CHECKING:
    from xblock.core import Blocklike


# __all__ controls what classes end up in the docs, and in what order.
__all__ = [
    'BlockScope', 'UserScope', 'Scope', 'ScopeIds',
    'Field',
    'Boolean', 'Dict', 'Float', 'Integer', 'List', 'Set', 'String', 'XMLString',
]


class FailingEnforceTypeWarning(DeprecationWarning):
    """
    A warning triggered when enforce_type would cause a exception if enabled
    """


class ModifyingEnforceTypeWarning(DeprecationWarning):
    """
    A warning triggered when enforce_type would change a value if enabled
    """


class Sentinel:
    """
    Base class for a 'sentinel': i.e., a special value object which is entirely identified by its name.
    """

    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        """
        A string that uniquely and entirely identifies this sentinel.
        """
        return self._name

    def __repr__(self) -> str:
        return self._name

    def __eq__(self, other: object) -> bool:
        """
        Two sentinel instances are equal if they have same name (even if their concrete classes differ).
        """
        # In the original XBlock API, all sentinels were directly constructed from Sentinel class;
        # there were no subclasses. So, to preserve backwards compatibility, we must allow for equality
        # regardless of the exact Sentinel subclass, unless we DEPR the public Sentinel class.
        # For example, we need to ensure that `Sentinel("fields.NO_CACHE_VALUE") == NoCacheValue()`.
        return isinstance(other, Sentinel) and self.name == other.name

    @property
    def attr_name(self) -> str:
        """
        Same as `self.name`, but with dots (.) replace with underscores (_).
        """
        # TODO: I don't think is used outside of the toy runtime. Consider DEPR'ing it next time
        #       breaking changes are made to the XBlock API.
        # NOTE: Theoretically, two different scopes could have colliding `attr_name` values.
        return self.name.lower().replace('.', '_')

    def __hash__(self) -> int:
        """
        Use a hash of the name of the sentinel
        """
        return hash(self.name)


class BlockScope(Sentinel, Enum):
    """
    Enumeration of block scopes.

    The block scope specifies how a field relates to blocks.  A
    :class:`.BlockScope` and a :class:`.UserScope` are combined to make a
    :class:`.Scope` for a field.

    USAGE: The data is related to a particular use of a block in a course.

    DEFINITION: The data is related to the definition of the block.  Although
        unusual, one block definition can be used in more than one place in a
        course.

    TYPE: The data is related to all instances of this type of Blocklike.

    ALL: The data is common to all blocks.  This can be useful for storing
        information that is purely about the student.
    """

    # In the original version of the XBlock API, all BlockScopes and UserScopes were
    # directly constructed as Sentinel objects. Later, we turned Sentinel into an
    # abstract class, with concerete subclasses for different types of Sentinels,
    # allowing for richer type definitions (e.g., ensuring that nobody can set a
    # BlockScope variable to NO_CACHE_VALUE, etc.). With that change made, BlockScope
    # and UserScope don't really need to inherit from Sentinel... Enum is sufficient.
    # But, removing Sentinel from their inheritance chains could theoretically break
    # some edge-cases uses of the XBlock API. In the future, through the DEPR process,
    # it might make sense to removal Sentinel from the public XBlock API entirely;
    # API users should only need to know about Sentinel's subclasses.

    USAGE = 'BlockScope.USAGE'
    DEFINITION = 'BlockScope.DEFINITION'
    TYPE = 'BlockScope.TYPE'
    ALL = 'BlockScope.ALL'

    @classmethod
    def scopes(cls) -> list[BlockScope]:
        """
        Return a list of valid/understood class scopes.
        """
        return list(cls)

    @property
    def name(self) -> str:  # pylint: disable=function-redefined
        """
        A string the uniquely and entirely identifies this object.

        Equivalent to `self.value`.
        """
        # For backwards compatibility with Sentinel, name must return "BlockScope.<BLAH>",
        # overriding the default Enum.name property which would just return "<BLAH>".
        return self._name


class UserScope(Sentinel, Enum):
    """
    Enumeration of user scopes.

    The user scope specifies how a field relates to users.  A
    :class:`.BlockScope` and a :class:`.UserScope` are combined to make a
    :class:`.Scope` for a field.

    NONE: Identifies data agnostic to the user of the :class:`.Blocklike`.  The
        data is related to no particular user.  All users see the same data.
        For instance, the definition of a problem.

    ONE: Identifies data particular to a single user of the :class:`.Blocklike`.
        For instance, a student's answer to a problem.

    ALL: Identifies data aggregated while the block is used by many users.
        The data is related to all the users.  For instance, a count of how
        many students have answered a question, or a histogram of the answers
        submitted by all students.

    """
    # (See the comment in BlockScope for historical context on this class and Sentinel)

    NONE = 'UserScope.NONE'
    ONE = 'UserScope.ONE'
    ALL = 'UserScope.ALL'

    @classmethod
    def scopes(cls) -> list[UserScope]:
        """
        Return a list of valid/understood class scopes.
        Why do we need this? I believe it is not used anywhere.
        """
        return list(cls)

    @property
    def name(self) -> str:  # pylint: disable=function-redefined
        """
        A string the uniquely and entirely identifies this object.

        Equivalent to `self.value`.
        """
        # For backwards compatibility with Sentinel, name must return "UserScope.<BLAH>",
        # overriding the default Enum.name property which would just return "<BLAH>".
        return self._name


class ParentScope(Sentinel):
    """
    A sentinel identifying a special Scope for the `parent` XBlock field.
    """
    def __init__(self):
        super().__init__("Scopes.parent")


class ChildrenScope(Sentinel):
    """
    A sentinel identifying a special Scope for the `children` XBlock field.
    """
    def __init__(self):
        super().__init__("Scopes.children")


@dataclass
class Scope:
    """
    Defines six types of scopes to be used: `content`, `settings`,
    `user_state`, `preferences`, `user_info`, and `user_state_summary`.

    The `content` scope is used to save data for all users, for one particular
    block, across all runs of a course. An example might be an XBlock that
    wishes to tabulate user "upvotes", or HTML content to display literally on
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
    # Fields
    user: UserScope
    block: BlockScope
    name: str | None = None

    # Predefined User+Block scopes (declard here, defined below)
    content: t.ClassVar[t.Self]
    settings: t.ClassVar[t.Self]
    user_state: t.ClassVar[t.Self]
    preferences: t.ClassVar[t.Self]
    user_info: t.ClassVar[t.Self]
    user_state_summary: t.ClassVar[t.Self]

    # Predefined special scopes
    children: t.ClassVar = ChildrenScope()
    parent: t.ClassVar = ParentScope()

    def __post_init__(self):
        """
        Set a fallback scope name if none is provided.
        """
        self.name = self.name or f"{self.user}_{self.block}"

    @property
    def scope_name(self) -> str:
        """
        Alias to `self.name`.

        Note: `self.name` and `self.scope_name` will always be equivalent and non-None, but for historical reasons,
        only `self.scope_name` can guarantee its non-None-ness to the type checker.
        """
        return self.name  # type: ignore

    @classmethod
    def named_scopes(cls) -> list[Scope]:
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
    def scopes(cls) -> list[Scope]:
        """Return all possible Scopes."""
        named_scopes = cls.named_scopes()
        return named_scopes + [
            cls(user, block)
            for user in UserScope.scopes()
            for block in BlockScope.scopes()
            if cls(user, block) not in named_scopes
        ]

    def __str__(self) -> str:
        return self.scope_name

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Scope) and self.user == other.user and self.block == other.block

    def __hash__(self) -> int:
        return hash(('xblock.fields.Scope', self.user, self.block))


Scope.content = Scope(UserScope.NONE, BlockScope.DEFINITION, 'content')
Scope.settings = Scope(UserScope.NONE, BlockScope.USAGE, 'settings')
Scope.user_state = Scope(UserScope.ONE, BlockScope.USAGE, 'user_state')
Scope.preferences = Scope(UserScope.ONE, BlockScope.TYPE, 'preferences')
Scope.user_info = Scope(UserScope.ONE, BlockScope.ALL, 'user_info')
Scope.user_state_summary = Scope(UserScope.ALL, BlockScope.USAGE, 'user_state_summary')


# Originally, ScopeBase and Scope were two separate classes, so that Scope could
# override ScopeBase.__new__ to provide a default name. Now that we have dataclasses,
# such a hack is unneccessary. We merge the classes, but keep ScopeBase as an alias
# for backwards compatibility.
ScopeBase = Scope


class ScopeIds(t.NamedTuple):
    """
    A simple wrapper to collect all of the ids needed to correctly identify an XBlock
    (or other classes deriving from ScopedStorageMixin) to a FieldData.
    These identifiers match up with BlockScope and UserScope attributes, so that,
    for instance, the `def_id` identifies scopes that use BlockScope.DEFINITION.
    """
    user_id: int | str | None
    block_type: str
    def_id: DefinitionKey
    usage_id: UsageKey


ScopeIds.__slots__ = ()  # type: ignore


class Unset(Sentinel):
    """
    Indicates that default value has not been provided.
    """
    def __init__(self):
        super().__init__("fields.UNSET")


class UniqueIdPlaceholder(Sentinel):
    """
    A special reference that can be used as a field's default in field
    definition to signal that the field should default to a unique string value
    calculated at runtime.
    """
    def __init__(self):
        super().__init__("fields.UNIQUE_ID")


class NoCacheValue(Sentinel):
    """
    Placeholder ('nil') value to indicate when nothing has been stored
    in the cache ("None" may be a valid value in the cache, so we cannot use it).
    """
    def __init__(self):
        super().__init__("fields.NO_CACHE_VALUE")


class ExplicitlySet(Sentinel):
    """
    Placeholder value that indicates that a value is explicitly dirty,
    because it was explicitly set.
    """
    def __init__(self):
        super().__init__("fields.EXPLICITLY_SET")


# For backwards API compatibility, define an instance of each Field-related sentinel.
# These could be be removed in favor of just constructing the class (e.g., every use of
# `UNIQUE_ID` could be replaced with `UniqueIdPlaceholder()`) but that would require a
# DEPR ticket.
UNSET = Unset()
UNIQUE_ID = UniqueIdPlaceholder()
NO_CACHE_VALUE = NoCacheValue()
EXPLICITLY_SET = ExplicitlySet()


# Fields that cannot have runtime-generated defaults. These are special,
# because they define the structure of XBlock trees.
NO_GENERATED_DEFAULTS = ('parent', 'children')

# Type parameters of Fields. These only matter for static type analysis (mypy).
FieldValue = t.TypeVar("FieldValue")  # What does the field hold?
InnerFieldValue = t.TypeVar("InnerFieldValue")  # For Dict/List/Set fields: What do they contain?


class Field(t.Generic[FieldValue]):
    """
    A field class that can be used as a class attribute to define what data the
    class will want to refer to.

    When the class is instantiated, it will be available as an instance
    attribute of the same name, by proxying through to the field-data service on
    the containing object.

    Parameters:

        help (str): documentation for the field, suitable for presenting to a
            user (defaults to None).

        default: field's default value. Can be a static value or the special
            xblock.fields.UNIQUE_ID reference. When set to xblock.fields.UNIQUE_ID,
            the field defaults to a unique string that is deterministically calculated
            for the field in the given scope (defaults to None).

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

        force_export: if set, the field value will be exported to XML even if normal
            export conditions are not met (i.e. the field has no explicit value set)

        kwargs: optional runtime-specific options/metadata. Will be stored as
            runtime_options.

    """
    MUTABLE: bool = True
    _default: FieldValue | None | UniqueIdPlaceholder = None
    __name__: str | None = None

    # Indicates if a field's None value should be sent to the XML representation.
    none_to_xml: bool = False

    def __init__(
        self,
        help: str | None = None,  # pylint:disable=redefined-builtin
        default: FieldValue | None | UniqueIdPlaceholder | Unset = Unset(),
        scope: Scope = Scope.content,
        display_name: str | None = None,
        values: list[object] | None = None,
        enforce_type: bool = False,
        xml_node: bool = False,
        force_export: bool = False,
        **kwargs
    ):
        self.warned = False
        self.help = help
        self._enable_enforce_type = enforce_type
        if not isinstance(default, Unset):
            if isinstance(default, UniqueIdPlaceholder):
                self._default = UniqueIdPlaceholder()
            else:
                self._default = self._check_or_enforce_type(default)
        self.scope = scope
        self._display_name = display_name
        self._values = values
        self.runtime_options = kwargs
        self.xml_node = xml_node
        self.force_export = force_export

    def __set_name__(self, owner: type, name: str):
        """
        Automatically record the name of this Field as it is defined on a class.
        """
        self.__name__ = name

    @property
    def default(self) -> FieldValue | None | UniqueIdPlaceholder:
        """Returns the static value that this defaults to."""
        if self.MUTABLE:
            return copy.deepcopy(self._default)
        else:
            return self._default

    @staticmethod
    def needs_name(field) -> bool:
        """
        Returns whether the given field is yet to be named.
        """
        return not field.__name__

    @property
    def name(self) -> str:
        """Returns the name of this field."""
        # This is set by ModelMetaclass
        return self.__name__ or 'unknown'

    @property
    def values(self) -> t.Any:
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
    def display_name(self) -> str:
        """
        Returns the display name for this class, suitable for use in a GUI.

        If no display name has been set, returns the name of the class.
        """
        return self._display_name if self._display_name is not None else self.name

    def _get_cached_value(self, xblock: Blocklike) -> FieldValue | None | NoCacheValue:
        """
        Return a value from the xblock's cache, or a marker value if either the cache
        doesn't exist or the value is not found in the cache.
        """
        # pylint: disable=protected-access
        return xblock._field_data_cache.get(self.name, NoCacheValue())

    def _set_cached_value(self, xblock: Blocklike, value: FieldValue | None):
        """Store a value in the xblock's cache, creating the cache if necessary."""
        # pylint: disable=protected-access
        xblock._field_data_cache[self.name] = value

    def _del_cached_value(self, xblock: Blocklike):
        """Remove a value from the xblock's cache, if the cache exists."""
        # pylint: disable=protected-access
        if self.name in xblock._field_data_cache:
            del xblock._field_data_cache[self.name]

    def _mark_dirty(self, xblock: Blocklike, value: FieldValue | None | ExplicitlySet):
        """Set this field to dirty on the xblock."""
        # pylint: disable=protected-access

        # Deep copy the value being marked as dirty, so that there
        # is a baseline to check against when saving later
        if self not in xblock._dirty_fields:
            xblock._dirty_fields[self] = copy.deepcopy(value)

    def _is_dirty(self, xblock: Blocklike) -> bool:
        """
        Return whether this field should be saved when xblock.save() is called
        """
        # pylint: disable=protected-access
        if self not in xblock._dirty_fields:
            return False

        baseline = xblock._dirty_fields[self]
        return isinstance(baseline, ExplicitlySet) or xblock._field_data_cache[self.name] != baseline

    def _is_lazy(self, value: FieldValue | None) -> bool:
        """
        Detect if a value is being evaluated lazily by Django.
        """
        return 'django.utils.functional.' in str(type(value))

    def _check_or_enforce_type(self, value: t.Any) -> FieldValue | None:
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
            message = "The value {!r} could not be enforced ({})".format(
                value, traceback.format_exc().splitlines()[-1])
            warnings.warn(message, FailingEnforceTypeWarning, stacklevel=3)
        else:
            try:
                equal = value == new_value
            except TypeError:
                equal = False
            if not equal:
                message = "The value {!r} would be enforced to {!r}".format(
                    value, new_value)
                warnings.warn(message, ModifyingEnforceTypeWarning, stacklevel=3)

        return value  # type: ignore

    def _calculate_unique_id(self, xblock: Blocklike) -> str:
        """
        Provide a default value for fields with `default=UNIQUE_ID`.

        Returned string is a SHA1 hex digest that is deterministically calculated
        for the field in its given scope.
        """
        key = scope_key(self, xblock)
        return hashlib.sha1(key.encode('utf-8')).hexdigest()

    def _get_default_value_to_cache(self, xblock: Blocklike) -> FieldValue | None:
        """
        Perform special logic to provide a field's default value for caching.
        """
        try:
            # pylint: disable=protected-access
            return self.from_json(xblock._field_data.default(xblock, self.name))
        except KeyError:
            if isinstance(self.default, UniqueIdPlaceholder):
                return self._check_or_enforce_type(self._calculate_unique_id(xblock))
            else:
                return self.default

    def _sanitize(self, value: FieldValue | None) -> FieldValue | None:
        """
        Allow the individual fields to sanitize the value being set -or- "get".
        For example, a String field wants to remove control characters.
        """
        return value

    def __get__(self, xblock: Blocklike, xblock_class: type[Blocklike]) -> FieldValue | None:
        """
        Gets the value of this xblock. Prioritizes the cached value over
        obtaining the value from the field-data service. Thus if a cached value
        exists, that is the value that will be returned.
        """
        if xblock is None:
            # Special case: When accessing the field directly on the class, return the field, not the value.
            # e.g., `MyXBlock.my_field` returns a `Field` instance.
            # This is standard Python descriptor behavior.
            return self

        field_data = xblock._field_data

        cache_value = self._get_cached_value(xblock)
        value: FieldValue | None
        if isinstance(cache_value, NoCacheValue):
            if field_data.has(xblock, self.name):
                value = self.from_json(field_data.get(xblock, self.name))
            elif self.name not in NO_GENERATED_DEFAULTS:
                # Cache default value
                value = self._get_default_value_to_cache(xblock)
            else:
                # Special handling for 'parent' and 'children' fields.
                # The type checker complains that `self.default` could be a UniqueIdPlaceholder,
                # but that's not possible here.
                value = self.default  # type: ignore[assignment]
            self._set_cached_value(xblock, value)
        else:
            value = cache_value

        # If this is a mutable type, mark it as dirty, since mutations can occur without an
        # explicit call to __set__ (but they do require a call to __get__)
        if self.MUTABLE:
            self._mark_dirty(xblock, value)

        return self._sanitize(value)

    def __set__(self, xblock: Blocklike, value: FieldValue | None) -> None:
        """
        Sets the `xblock` to the given `value`.
        Setting a value does not update the underlying data store; the
        new value is kept in the cache and the xblock is marked as
        dirty until `save` is explicitly called.

        Note, if there's already a cached value and it's equal to the value
        we're trying to cache, we won't do anything.
        """
        value = self._check_or_enforce_type(value)
        value = self._sanitize(value)
        cached_value = self._get_cached_value(xblock)  # note: could be NoCacheValue
        try:
            value_has_changed = cached_value != value
        except Exception:  # pylint: disable=broad-except
            # if we can't compare the values for whatever reason
            # (i.e. timezone aware and unaware datetimes), just reset the value.
            value_has_changed = True
        if value_has_changed:
            # Mark the field as dirty and update the cache
            self._mark_dirty(xblock, ExplicitlySet())
            self._set_cached_value(xblock, value)

    def __delete__(self, xblock: Blocklike):
        """
        Deletes `xblock` from the underlying data store.
        Deletes are not cached; they are performed immediately.
        """

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
        self._set_cached_value(xblock, self._get_default_value_to_cache(xblock))

    def __repr__(self):
        return "<{0.__class__.__name__} {0.name}>".format(self)

    def _warn_deprecated_outside_JSONField(self):  # pylint: disable=invalid-name
        """Certain methods will be moved to JSONField.

        This warning marks calls when the object is not
        derived from that class.
        """
        if not isinstance(self, JSONField) and not self.warned:
            warnings.warn(
                f"Deprecated. JSONifiable fields should derive from JSONField ({self.name})",
                DeprecationWarning,
                stacklevel=3
            )
            self.warned = True

    def to_json(self, value: FieldValue | None) -> t.Any:
        """
        Return value in the form of nested lists and dictionaries (suitable
        for passing to json.dumps).

        This is called during field writes to convert the native python
        type to the value stored in the database
        """
        self._warn_deprecated_outside_JSONField()
        return value

    def from_json(self, value) -> FieldValue | None:
        """
        Return value as a native full featured python type (the inverse of to_json)

        Called during field reads to convert the stored value into a full featured python
        object
        """
        self._warn_deprecated_outside_JSONField()
        return value  # type: ignore

    def to_string(self, value: FieldValue | None) -> str:
        """
        Return a JSON serialized string representation of the value.
        """
        self._warn_deprecated_outside_JSONField()
        return json.dumps(
            self.to_json(value),
            indent=2,
            sort_keys=True,
            separators=(',', ': '),
        )

    def from_string(self, serialized: str) -> FieldValue | None:
        """
        Returns a native value from a YAML serialized string representation.
        Since YAML is a superset of JSON, this is the inverse of to_string.)
        """
        self._warn_deprecated_outside_JSONField()
        value = yaml.safe_load(serialized)
        return self.enforce_type(value)

    def enforce_type(self, value: t.Any) -> FieldValue | None:
        """
        Coerce the type of the value, if necessary

        Called on field sets to ensure that the stored type is consistent if the
        field was initialized with enforce_type=True

        This must not have side effects, since it will be executed to trigger
        a DeprecationWarning even if enforce_type is disabled
        """
        return value  # type: ignore

    def read_from(self, xblock: Blocklike) -> FieldValue | None:
        """
        Retrieve the value for this field from the specified xblock
        """
        return self.__get__(xblock, xblock.__class__)  # pylint: disable=unnecessary-dunder-call

    def read_json(self, xblock: Blocklike) -> FieldValue | None:
        """
        Retrieve the serialized value for this field from the specified xblock
        """
        self._warn_deprecated_outside_JSONField()
        return self.to_json(self.read_from(xblock))

    def write_to(self, xblock: Blocklike, value: FieldValue | None) -> None:
        """
        Set the value for this field to value on the supplied xblock
        """
        self.__set__(xblock, value)  # pylint: disable=unnecessary-dunder-call

    def delete_from(self, xblock: Blocklike) -> None:
        """
        Delete the value for this field from the supplied xblock
        """
        self.__delete__(xblock)   # pylint: disable=unnecessary-dunder-call

    def is_set_on(self, xblock: Blocklike) -> bool:
        """
        Return whether this field has a non-default value on the supplied xblock
        """
        # pylint: disable=protected-access
        return self._is_dirty(xblock) or xblock._field_data.has(xblock, self.name)

    def __hash__(self) -> int:
        return hash(self.name)


class JSONField(Field, t.Generic[FieldValue]):
    """
    Field type which has a convenient JSON representation.
    """
    # for now; we'll bubble functions down when we finish deprecation in Field


class Integer(JSONField[int]):
    """
    A field that contains an integer.

    The value, as loaded or enforced, can be None, '' (which will be treated as
    None), a Python integer, or a value that will parse as an integer, ie.,
    something for which int(value) does not throw an error.

    Note that a floating point value will convert to an integer, but a string
    containing a floating point number ('3.48') will throw an error.

    """
    MUTABLE = False

    def from_json(self, value) -> int | None:
        if value is None or value == '':
            return None
        return int(value)

    enforce_type = from_json


class Float(JSONField[float]):
    """
    A field that contains a float.

    The value, as loaded or enforced, can be None, '' (which will be treated as
    None), a Python float, or a value that will parse as an float, ie.,
    something for which float(value) does not throw an error.

    """
    MUTABLE = False

    def from_json(self, value) -> float | None:
        if value is None or value == '':
            return None
        return float(value)

    enforce_type = from_json


class Boolean(JSONField[bool]):
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
    def __init__(self, help=None, default=UNSET, scope=Scope.content, display_name=None,
                 **kwargs):  # pylint: disable=redefined-builtin
        super().__init__(help, default, scope, display_name,
                         values=({'display_name': "True", "value": True},
                                 {'display_name': "False", "value": False}), **kwargs)

    def from_json(self, value) -> bool | None:
        if isinstance(value, bytes):
            value = value.decode('ascii', errors='replace')
        if isinstance(value, str):
            return value.lower() == 'true'
        else:
            return bool(value)

    enforce_type = from_json


class Dict(JSONField[t.Dict[str, InnerFieldValue]], t.Generic[InnerFieldValue]):
    """
    A field class for representing a Python dict.

    The value, as loaded or enforced, must be either be None or a dict.

    """
    _default = {}

    def from_json(self, value) -> dict[str, InnerFieldValue] | None:
        if value is None or isinstance(value, dict):
            return value
        else:
            raise TypeError('Value stored in a Dict must be None or a dict, found %s' % type(value))

    enforce_type = from_json

    def to_string(self, value) -> str:
        """
        In python3, json.dumps() cannot sort keys of different types,
        so preconvert None to 'null'.
        """
        self.enforce_type(value)
        if isinstance(value, dict) and None in value:
            value = value.copy()
            value['null'] = value[None]
            del value[None]
        return super().to_string(value)


class List(JSONField[t.List[InnerFieldValue]], t.Generic[InnerFieldValue]):
    """
    A field class for representing a list.

    The value, as loaded or enforced, can either be None or a list.

    """
    _default = []

    def from_json(self, value) -> list[InnerFieldValue] | None:
        if value is None or isinstance(value, list):
            return value
        else:
            raise TypeError('Value stored in a List must be None or a list, found %s' % type(value))

    enforce_type = from_json


class Set(JSONField[t.List[InnerFieldValue]], t.Generic[InnerFieldValue]):
    """
    A field class for representing a set.

    The stored value can either be None or a set.

    """
    _default = set()

    def __init__(self, *args, **kwargs):
        """
        Set class constructor.

        Redefined in order to convert default values to sets.
        """
        super().__init__(*args, **kwargs)

        self._default = set(self._default)

    def from_json(self, value) -> set[InnerFieldValue] | None:
        if value is None or isinstance(value, set):
            return value
        else:
            return set(value)

    enforce_type = from_json


class String(JSONField[str]):
    """
    A field class for representing a string.

    The value, as loaded or enforced, can either be None or a basestring instance.

    """
    MUTABLE = False
    BAD_REGEX = re.compile('[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]', flags=re.UNICODE)

    def _sanitize(self, value) -> str | None:
        """
        Remove the control characters that are not allowed in XML:
        https://www.w3.org/TR/xml/#charsets
        Leave all other characters.
        """
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        if isinstance(value, str):
            if re.search(self.BAD_REGEX, value):
                new_value = re.sub(self.BAD_REGEX, "", value)
                # The new string will be equivalent to the original string if no control characters are present.
                # If equivalent, return the original string - some tests
                # check for object equality instead of string equality.
                return value if value == new_value else new_value
            else:
                return value
        else:
            return value

    def from_json(self, value) -> str | None:
        if value is None:
            return None
        elif isinstance(value, (bytes, str)):
            return self._sanitize(value)
        elif self._is_lazy(value):
            # Allow lazily translated strings to be used as String default values.
            # The translated values are *not* sanitized.
            return value
        else:
            raise TypeError('Value stored in a String must be None or a string, found %s' % type(value))

    def from_string(self, serialized) -> str | None:
        """String gets serialized and deserialized without quote marks."""
        return self.from_json(serialized)

    def to_string(self, value) -> str:
        """String gets serialized and deserialized without quote marks."""
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        return self.to_json(value)

    def enforce_type(self, value: t.Any) -> str | None:
        """
        (no-op override just to make mypy happy about XMLString.enforce_type)
        """
        return super().enforce_type(value)

    none_to_xml = True  # Use an XML node for the field, and represent None as an attribute.

    enforce_type = from_json


class XMLString(String):
    """
    A field class for representing an XML string.

    The value, as loaded or enforced, can either be None or a basestring instance.
    If it is a basestring instance, it must be valid XML.  If it is not valid XML,
    an lxml.etree.XMLSyntaxError will be raised.
    """

    def to_json(self, value) -> t.Any:
        """
        Serialize the data, ensuring that it is valid XML (or None).

        Raises an lxml.etree.XMLSyntaxError if it is a basestring but not valid
        XML.
        """
        if self._enable_enforce_type:
            value = self.enforce_type(value)
        return super().to_json(value)

    def enforce_type(self, value: t.Any) -> str | None:
        if value is not None:
            etree.XML(value)
        return value  # type: ignore


class DateTime(JSONField[t.Union[datetime, timedelta]]):
    """
    A field for representing a datetime.

    The value, as loaded or enforced, can either be an ISO-formatted date string, a native datetime,
    a timedelta (for a time relative to course start), or None.
    """

    DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'

    def from_json(self, value) -> datetime | timedelta | None:
        """
        Parse the date from an ISO-formatted date string, or None.
        """
        if value is None:
            return None

        if isinstance(value, bytes):
            value = value.decode('utf-8')

        if isinstance(value, str):
            # Parser interprets empty string as now by default
            if value == "":
                return None

            try:
                value = dateutil.parser.parse(value)
            except (TypeError, ValueError):
                raise ValueError(f"Could not parse {value} as a date")  # pylint: disable= raise-missing-from

        # Interpret raw numbers as a relative dates
        if isinstance(value, (int, float)):
            value = timedelta(seconds=value)

        if not isinstance(value, (datetime, timedelta)):
            raise TypeError(
                "Value should be loaded from a string, a datetime object, a timedelta object, or None, not {}".format(
                    type(value)
                )
            )

        if isinstance(value, datetime):
            if value.tzinfo is not None:
                return value.astimezone(pytz.utc)
            else:
                return value.replace(tzinfo=pytz.utc)
        else:
            return value

    def to_json(self, value) -> t.Any:
        """
        Serialize the date as an ISO-formatted date string, or None.
        """
        if isinstance(value, datetime):
            return value.strftime(self.DATETIME_FORMAT)

        if isinstance(value, timedelta):
            return value.total_seconds()

        if value is None:
            return None

        raise TypeError(f"Value stored must be a datetime or timedelta object, not {type(value)}")

    def to_string(self, value) -> str:
        """DateTime fields get serialized without quote marks."""
        return self.to_json(value)

    enforce_type = from_json


class Any(JSONField[t.Any]):
    """
    A field class for representing any piece of data; type is not enforced.

    All methods are inherited directly from `Field`.

    THIS SHOULD BE DEPRECATED. THIS SHOULD EITHER BE ANY JSON DATA, OR IT MAKES NO SENSE
    """


class Reference(JSONField[UsageKey]):
    """
    An xblock reference. That is, a pointer to another xblock.

    It's up to the runtime to know how to dereference this field type, but the field type enables the
    runtime to know that it must do the interpretation.
    """


class ReferenceList(List[UsageKey]):
    """
    An list of xblock references. That is, pointers to xblocks.

    It's up to the runtime to know how to dereference the elements of the list. The field type enables the
    runtime to know that it must do the interpretation.
    """
    # this could define from_json and to_json as list comprehensions calling from/to_json on the list elements,
    # but since Reference doesn't stipulate a definition for from/to, that seems unnecessary at this time.


class ReferenceListNotNone(ReferenceList):
    """
    An list of xblock references. Should not equal None.

    Functionally, this is exactly equivalent to ReferenceList.
    To the type-checker, this adds that guarantee that accessing the field will always return
    a list of UsageKeys, rather than None OR a list of UsageKeys.
    """
    def __get__(self, xblock: Blocklike, xblock_class: type[Blocklike]) -> list[UsageKey]:
        return super().__get__(xblock, xblock_class)  # type: ignore


class ReferenceValueDict(Dict[UsageKey]):
    """
    A dictionary where the values are xblock references. That is, pointers to xblocks.

    It's up to the runtime to know how to dereference the elements of the list. The field type enables the
    runtime to know that it must do the interpretation.
    """
    # this could define from_json and to_json as list comprehensions calling from/to_json on the list elements,
    # but since Reference doesn't stipulate a definition for from/to, that seems unnecessary at this time.


def scope_key(instance: Field, xblock: Blocklike) -> str:
    """
    Generate a unique key for a scope that can be used as a
    filename, in a URL, or in a KVS.

    Our goal is to have a pretty, human-readable 1:1 encoding.

    This encoding is as good as we can do. It's reversible, but not
    trivial to reverse.

    Encoding scheme:
    Posix allows [A-Z][a-z][0-9]._-
    We'd like to have a _concise_ representation for common punctuation
    We're okay with a _non-concise_ representation for repeated or uncommon characters
    We keep [A-z][a-z][0-9] as is.
    We encode other common punctuation as pairs of ._-. This gives a total of 3*3=9 combinations.
    We're pretty careful to keep this nice. Where possible, we double characters. The most common
    other character (' ' and ':') are encoded as _- and -_
    We separate field portions with /. This gives a natural directory
    tree. This is nice in URLs and filenames (although not so nice in
    urls.py)
    If a field starts with punctuation, we prefix a _. This prevents hidden files.

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
    if instance.scope.user in [UserScope.NONE, UserScope.ALL]:
        pass
    elif instance.scope.user == UserScope.ONE:
        scope_key_dict['user'] = str(xblock.scope_ids.user_id)
    else:
        raise NotImplementedError()

    if instance.scope.block == BlockScope.TYPE:
        scope_key_dict['block'] = str(xblock.scope_ids.block_type)
    elif instance.scope.block == BlockScope.USAGE:
        scope_key_dict['block'] = str(xblock.scope_ids.usage_id)
    elif instance.scope.block == BlockScope.DEFINITION:
        scope_key_dict['block'] = str(xblock.scope_ids.def_id)
    elif instance.scope.block == BlockScope.ALL:
        pass
    else:
        raise NotImplementedError()

    replacements = itertools.product("._-", "._-")
    substitution_list = dict(zip("./\\,_ +:-", ("".join(x) for x in replacements)))
    # Above runs in 4.7us, and generates a list of common substitutions:
    # {' ': '_-', '+': '-.', '-': '--', ',': '_.', '/': '._', '.': '..', ':': '-_', '\\': '.-', '_': '__'}

    key_list = []

    def encode(char: str) -> str:
        """
        Replace all non-alphanumeric characters with -n- where n
        is their Unicode codepoint.
        """
        if char.isalnum():
            return char
        elif char in substitution_list:
            return substitution_list[char]
        else:
            return f"_{ord(char)}_"

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
