"""
Generic plugin support so we can find XBlocks.

This code is in the Runtime layer.
"""
import functools
import importlib.metadata
import itertools
import logging

from xblock.internal import class_lazy

log = logging.getLogger(__name__)

PLUGIN_CACHE = {}


class PluginMissingError(Exception):
    """Raised when trying to load a plugin from an entry_point that cannot be found."""


class AmbiguousPluginError(Exception):
    """Raised when a class name produces more than one entry_point."""
    def __init__(self, all_entry_points):
        classes = (entpt.load() for entpt in all_entry_points)
        desc = ", ".join("{0.__module__}.{0.__name__}".format(cls) for cls in classes)
        msg = f"Ambiguous entry points for {all_entry_points[0].name}: {desc}"
        super().__init__(msg)


class AmbiguousPluginOverrideError(AmbiguousPluginError):
    """Raised when a class name produces more than one override for an entry_point."""


def _default_select_no_override(identifier, all_entry_points):  # pylint: disable=inconsistent-return-statements
    """
    Selects plugin for the given identifier, raising on error:

    Raises:
    - PluginMissingError when we don't have an entry point.
    - AmbiguousPluginError when we have ambiguous entry points.
    """

    if len(all_entry_points) == 0:
        raise PluginMissingError(identifier)
    if len(all_entry_points) == 1:
        return all_entry_points[0]
    elif len(all_entry_points) > 1:
        raise AmbiguousPluginError(all_entry_points)


def default_select(identifier, all_entry_points):
    """
    Selects plugin for the given identifier with the ability for a Plugin to override
    the default entry point.

    Raises:
    - PluginMissingError when we don't have an entry point or entry point to override.
    - AmbiguousPluginError when we have ambiguous entry points.
    """

    # Split entry points into overrides and non-overrides
    overrides = []
    block_entry_points = []

    for block_entry_point in all_entry_points:
        if block_entry_point.group.endswith('.overrides'):
            overrides.append(block_entry_point)
        else:
            block_entry_points.append(block_entry_point)

    # Get the default entry point
    default_plugin = _default_select_no_override(identifier, block_entry_points)

    # If we have an unambiguous override, that gets priority. Otherwise, return default.
    if len(overrides) == 1:
        return overrides[0]
    elif len(overrides) > 1:
        raise AmbiguousPluginOverrideError(overrides)
    return default_plugin


class Plugin:
    """Base class for a system that uses entry_points to load plugins.

    Implementing classes are expected to have the following attributes:

        `entry_point`: The name of the entry point to load plugins from.

    """
    entry_point = None  # Should be overwritten by children classes

    @class_lazy
    def extra_entry_points(cls):  # pylint: disable=no-self-argument
        """
        Temporary entry points, for register_temp_plugin.  A list of pairs,
        (identifier, entry_point):

        [('test1', test1_entrypoint), ('test2', test2_entrypoint), ...]
        """
        return []

    @classmethod
    def _load_class_entry_point(cls, entry_point):
        """
        Load `entry_point`, and set the `entry_point.name` as the
        attribute `plugin_name` on the loaded object
        """
        class_ = entry_point.load()
        class_.plugin_name = entry_point.name
        return class_

    @classmethod
    def load_class(cls, identifier, default=None, select=None):
        """Load a single class specified by identifier.

        By default, this returns the class mapped to `identifier` from entry_points
        matching `{cls.entry_points}.overrides` or `{cls.entry_points}`, in that order.

        If multiple classes are found for either `{cls.entry_points}.overrides` or
        `{cls.entry_points}`, it will raise an `AmbiguousPluginError`.

        If no classes are found for `{cls.entry_points}`, it will raise a `PluginMissingError`.

        Args:
        - identifier: The class to match on.

        Kwargs:
        - default: A class to return if no entry_point matching `identifier` is found.
        - select: A function to override our default_select functionality.

        If `select` is provided, it should be a callable of the form::

            def select(identifier, all_entry_points):
                # ...
                return an_entry_point

        The `all_entry_points` argument will be a list of all entry_points matching `identifier`
        that were found, and `select` should return one of those entry_points to be
        loaded. `select` should raise `PluginMissingError` if no plugin is found, or `AmbiguousPluginError`
        if too many plugins are found
        """
        identifier = identifier.lower()
        key = (cls.entry_point, identifier)

        if key in PLUGIN_CACHE:
            xblock_cls = PLUGIN_CACHE[key] or default
            if xblock_cls:
                return xblock_cls

            # If the key was in PLUGIN_CACHE, but the value stored was None, and
            # there was no default class to fall back to, we give up and raise
            # PluginMissingError. This is for performance reasons. We've cached
            # the fact that there is no XBlock class that maps to this
            # identifier, and it is very expensive to check through the entry
            # points each time. This assumes that XBlock class mappings do not
            # change during the life of the process.
            raise PluginMissingError(identifier)

        if select is None:
            select = default_select

        all_entry_points = [
            *importlib.metadata.entry_points(group=f'{cls.entry_point}.overrides', name=identifier),
            *importlib.metadata.entry_points(group=cls.entry_point, name=identifier)
        ]

        for extra_identifier, extra_entry_point in iter(cls.extra_entry_points):
            if identifier == extra_identifier:
                all_entry_points.append(extra_entry_point)

        try:
            selected_entry_point = select(identifier, all_entry_points)
        except PluginMissingError:
            PLUGIN_CACHE[key] = None
            if default is not None:
                return default
            raise

        PLUGIN_CACHE[key] = cls._load_class_entry_point(selected_entry_point)

        return PLUGIN_CACHE[key]

    @classmethod
    def load_classes(cls, fail_silently=True):
        """Load all the classes for a plugin.

        Produces a sequence containing the identifiers and their corresponding
        classes for all of the available instances of this plugin.

        fail_silently causes the code to simply log warnings if a
        plugin cannot import. The goal is to be able to use part of
        libraries from an XBlock (and thus have it installed), even if
        the overall XBlock cannot be used (e.g. depends on Django in a
        non-Django application). There is disagreement about whether
        this is a good idea, or whether we should see failures early
        (e.g. on startup or first page load), and in what
        contexts. Hence, the flag.
        """
        all_classes = itertools.chain(
            importlib.metadata.entry_points(group=cls.entry_point),
            (entry_point for identifier, entry_point in iter(cls.extra_entry_points)),
        )
        for class_ in all_classes:
            try:
                yield (class_.name, cls._load_class_entry_point(class_))
            except Exception:  # pylint: disable=broad-except
                if fail_silently:
                    log.warning('Unable to load %s %r', cls.__name__, class_.name, exc_info=True)
                else:
                    raise

    @classmethod
    def register_temp_plugin(cls, class_, identifier=None, dist='xblock', group='xblock.v1'):
        """Decorate a function to run with a temporary plugin available.

        Use it like this in tests::

            @register_temp_plugin(MyXBlockClass):
            def test_the_thing():
                # Here I can load MyXBlockClass by name.

        """
        from unittest.mock import Mock  # pylint: disable=import-outside-toplevel

        if identifier is None:
            identifier = class_.__name__.lower()

        entry_point = Mock(
            dist=Mock(key=dist),
            load=Mock(return_value=class_),
            group=group
        )
        entry_point.name = identifier

        def _decorator(func):
            @functools.wraps(func)
            def _inner(*args, **kwargs):
                global PLUGIN_CACHE  # pylint: disable=global-statement

                old = list(cls.extra_entry_points)
                old_cache = PLUGIN_CACHE

                cls.extra_entry_points.append((identifier, entry_point))  # pylint: disable=no-member
                PLUGIN_CACHE = {}

                try:
                    return func(*args, **kwargs)
                finally:
                    cls.extra_entry_points = old
                    PLUGIN_CACHE = old_cache
            return _inner
        return _decorator
