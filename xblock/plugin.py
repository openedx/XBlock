"""Generic plugin support so we can find XBlocks.

This code is in the Runtime layer.

"""

import functools
import itertools
import logging
import pkg_resources

log = logging.getLogger(__name__)


class PluginMissingError(Exception):
    """Raised when trying to load a plugin from an entry_point that cannot be found."""
    pass


class AmbiguousPluginError(Exception):
    """Raised when a class name produces more than one entry_point."""
    def __init__(self, entry_points):
        classes = (entpt.load() for entpt in entry_points)
        desc = ", ".join("{0.__module__}.{0.__name__}".format(cls) for cls in classes)
        msg = "Ambiguous entry points for {}: {}".format(entry_points[0].name, desc)
        super(AmbiguousPluginError, self).__init__(msg)


def default_select(identifier, entry_points):
    """
    Raise an exception when we have ambiguous entry points.
    """

    if len(entry_points) == 0:
        raise PluginMissingError(identifier)

    elif len(entry_points) == 1:
        return entry_points[0]

    elif len(entry_points) > 1:
        raise AmbiguousPluginError(entry_points)


class Plugin(object):
    """Base class for a system that uses entry_points to load plugins.

    Implementing classes are expected to have the following attributes:

        `entry_point`: The name of the entry point to load plugins from.

    """

    _plugin_cache = None
    entry_point = None  # Should be overwritten by children classes

    # Temporary entry points, for register_temp_plugin.  A list of pairs,
    # (identifier, entry_point):
    #   [('test1', test1_entrypoint), ('test2', test2_entrypoint), ...]
    extra_entry_points = []

    @classmethod
    def _load_class_entry_point(cls, entry_point):
        """
        Load `entry_point`, and set the `entry_point.name` as the
        attribute `plugin_name` on the loaded object
        """
        class_ = entry_point.load()
        setattr(class_, 'plugin_name', entry_point.name)
        return class_

    @classmethod
    def load_class(cls, identifier, default=None, select=None):
        """Load a single class specified by identifier.

        If `identifier` specifies more than a single class, and `select` is not None,
        then call `select` on the list of entry_points. Otherwise, choose
        the first one and log a warning.

        If `default` is provided, return it if no entry_point matching
        `identifier` is found. Otherwise, will raise a PluginMissingError

        If `select` is provided, it should be a callable of the form::

            def select(identifier, entry_points):
                # ...
                return an_entry_point

        The `entry_points` argument will be a list of all entry_points matching `identifier`
        that were found, and `select` should return one of those entry_points to be
        loaded. `select` should raise `PluginMissingError` if no plugin is found, or `AmbiguousPluginError`
        if too many plugins are found
        """
        if select is None:
            select = default_select

        if cls._plugin_cache is None:
            cls._plugin_cache = {}

        if identifier not in cls._plugin_cache:
            identifier = identifier.lower()
            entry_points = list(pkg_resources.iter_entry_points(cls.entry_point, name=identifier))
            for extra_identifier, extra_entry_point in cls.extra_entry_points:
                if identifier == extra_identifier:
                    entry_points.append(extra_entry_point)

            try:
                entry_point = select(identifier, entry_points)
            except PluginMissingError:
                if default is not None:
                    return default
                raise

            cls._plugin_cache[identifier] = cls._load_class_entry_point(entry_point)
        return cls._plugin_cache[identifier]

    @classmethod
    def load_classes(cls):
        """Load all the classes for a plugin.

        Produces a sequence containing the identifiers and their corresponding
        classes for all of the available instances of this plugin.

        """
        all_classes = itertools.chain(
            pkg_resources.iter_entry_points(cls.entry_point),
            (entry_point for identifier, entry_point in cls.extra_entry_points),
        )
        for class_ in all_classes:
            yield (class_.name, cls._load_class_entry_point(class_))

    @classmethod
    def register_temp_plugin(cls, class_, identifier=None, dist='xblock'):
        """Decorate a function to run with a temporary plugin available.

        Use it like this in tests::

            @register_temp_plugin(MyXBlockClass):
            def test_the_thing():
                # Here I can load MyXBlockClass by name.

        """
        from mock import Mock

        if identifier is None:
            identifier = class_.__name__.lower()

        entry_point = Mock(
            dist=Mock(key=dist),
            load=Mock(return_value=class_),
        )
        entry_point.name = identifier

        def _decorator(func):                           # pylint: disable=C0111
            @functools.wraps(func)
            def _inner(*args, **kwargs):                # pylint: disable=C0111
                old = list(cls.extra_entry_points)
                cls.extra_entry_points.append((identifier, entry_point))
                try:
                    return func(*args, **kwargs)
                finally:
                    cls.extra_entry_points = old
            return _inner
        return _decorator
