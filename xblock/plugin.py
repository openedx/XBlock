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


def select_first_and_warn(entry_points):
    """
    Select the first entry_point, and log a warning that we're doing so
    with no additional knowledge
    """
    assert len(entry_points) > 1

    log.warning(
        "Found multiple entry_points with identifier %s: %s. Returning the first one.",
        entry_points[0].name,
        ", ".join(class_.module_name for class_ in entry_points)
    )
    return entry_points[0]


class Plugin(object):
    """Base class for a system that uses entry_points to load plugins.

    Implementing classes are expected to have the following attributes:

        `entry_point`: The name of the entry point to load plugins from.

    """

    _plugin_cache = None
    entry_point = None  # Should be overwritten by children classes

    # Temporary entry points, for register_temp_plugin.  This dict maps
    # identifiers to classes:
    #   {'test1': Test1XBlock, 'test2': Test2XBlock}
    extra_entry_points = {}

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

            def select(entry_points):
                # ...
                return an_entry_point

        The `entry_points` argument will be a list of all entry_points matching `identifier`
        that were found, and `select` should return one of those entry_points to be
        loaded.
        """
        if select is None:
            select = select_first_and_warn

        if cls._plugin_cache is None:
            cls._plugin_cache = {}

        if identifier not in cls._plugin_cache:
            identifier = identifier.lower()
            entry_points = list(pkg_resources.iter_entry_points(cls.entry_point, name=identifier))
            if identifier in cls.extra_entry_points:
                entry_points.append(cls.extra_entry_points[identifier])

            if len(entry_points) > 1:
                entry_point = select(entry_points)

            elif len(entry_points) == 0:
                if default is not None:
                    return default
                raise PluginMissingError(identifier)

            else:
                entry_point = entry_points[0]

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
            cls.extra_entry_points.values(),
        )
        for class_ in all_classes:
            yield (class_.name, cls._load_class_entry_point(class_))

    @classmethod
    def register_temp_plugin(cls, class_, identifier=None):
        """Decorate a function to run with a temporary plugin available.

        Use it like this in tests::

            @register_temp_plugin(MyXBlockClass):
            def test_the_thing():
                # Here I can load MyXBlockClass by name.

        """
        if identifier is None:
            identifier = class_.__name__.lower()
        entry_point = _EntryPointStub(class_, identifier)

        def _decorator(func):
            @functools.wraps(func)
            def _inner(*args, **kwargs):
                old = cls.extra_entry_points.copy()
                cls.extra_entry_points[identifier] = entry_point
                try:
                    return func(*args, **kwargs)
                finally:
                    cls.extra_entry_points = old
            return _inner
        return _decorator


class _EntryPointStub(object):
    """A simple stub for entry points for use by register_temp_plugin."""
    def __init__(self, class_, name):
        self.class_ = class_
        self.name = name

    def load(self):
        return self.class_
