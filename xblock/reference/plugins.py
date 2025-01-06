"""
This is a set of reference implementations for XBlock plugins
(XBlocks, Fields, and Services).

The README file in this directory contains much more information.

Much of this still needs to be organized.
"""
from djpyfs import djpyfs  # type: ignore[import-untyped]
from fs.base import FS

from xblock.core import Blocklike
from xblock.runtime import Runtime
from xblock.fields import Field, NO_CACHE_VALUE, scope_key

#  Finished services


def public(type=None, **kwargs):  # pylint: disable=unused-argument, redefined-builtin
    """
    Mark a function as public. In the future, this will inform the
    XBlocks services framework to make the function remotable. For
    now, this is a placeholder.

    The kwargs will contain:

      type : A specification for what the function does. Multiple
      functions of the same type will have identical input/output
      semantics, but may have different implementations. For example,

        type = student_distance

      Takes two students and returns a number. Specific instances may
      look at e.g. difference in some measure of aptitude, geographic
      distance, culture, or language. See stevedor, as well as queries
      in https://github.com/edx-unsupported/insights to understand how
      this will be used.
    """

    def wrapper(function):
        """
        Just return the function (for now)
        """
        return function

    return wrapper


class Service:
    """
    Top-level definition for an XBlocks service.

    This is intended as a starting point for discussion, not
    necessarily a finished interface.

    Possible goals:
    * Right now, they derive from object. We'd like there to be a
      common superclass.
    * We'd like to be able to provide both language-level and
      service-level bindings.
    * We'd like them to have a basic knowledge of context (what block
      they're being called from, access to the runtime, dependencies,
      etc.
    * That said, we'd like to not over-initialize. Services may have
      expensive initializations, and a per-block initialization may be
      prohibitive.
    * We'd like them to be able to load through Stevedor, and have a
      plug-in mechanism similar to XBlock.
    """
    def __init__(
        self,
        *,
        runtime: Runtime | None = None,
        xblock: Blocklike | None = None,
        user: object | None = None,
        **kwargs
    ):
        # TODO: We need plumbing to set these
        self._runtime = runtime
        self._xblock = xblock
        self._user = user

    def xblock(self) -> Blocklike | None:
        """
        Accessor for the xblock calling the service. Returns None if unknown
        """
        return self._xblock

    def runtime(self) -> Runtime | None:
        """
        Accessor for the runtime object. Returns None if unknown
        """
        return self._runtime


class Filesystem(Field):
    """An enhanced pyfilesystem.

    This returns a file system provided by the runtime. The file
    system has two additional methods over a normal pyfilesytem:

    * `get_url` allows it to return a URL for a file
    * `expire` allows it to create files which may be garbage
      collected after a preset period. `edx-platform` and
      `xblock-sdk` do not currently garbage collect them,
      however.

    More information can be found at: https://github.com/openedx/django-pyfs

    The major use cases for this are storage of large binary objects,
    pregenerating per-student data (e.g. `pylab` plots), and storing
    data which should be downloadable (for example, serving <img
    src=...> will typically be faster through this than serving that
    up through XBlocks views.
    """
    MUTABLE = False

    def __get__(self, xblock: Blocklike | None, xblock_class: type[Blocklike]):
        """
        Returns a `pyfilesystem` object which may be interacted with.
        """
        # Prioritizes the cached value over obtaining the value from
        # the field-data service. Thus if a cached value exists, that
        # is the value that will be returned. Otherwise, it will get
        # it from the fs service.

        if xblock is None:
            return self

        value = self._get_cached_value(xblock)
        if value is NO_CACHE_VALUE:
            value = xblock.runtime.service(xblock, 'fs').load(self, xblock)
            self._set_cached_value(xblock, value)

        return value

    def __delete__(self, xblock: Blocklike):
        """
        We don't support this until we figure out what this means. Files
        should be deleted through normal pyfilesystem operations.
        """
        raise NotImplementedError

    def __set__(self, xblock: Blocklike, value: object):
        """
        We interact with a file system by `open`/`close`/`read`/`write`,
        not `set` and `get`.

        We don't support this until we figure out what this means. In
        the future, this might be used to e.g. store some kind of
        metadata about the file system in the KVS (perhaps prefix and
        location or similar?)
        """
        raise NotImplementedError

#  edX-internal prototype services


class FSService(Service):
    """
    This is a PROTOTYPE service for storing files in XBlock fields.

    It returns a file system as per:
    https://github.com/openedx/django-pyfs

    1) We want to change how load() works, and specifically how
    prefixes are calculated.
    2) There is discussion as to whether we want this service at
    all. Specifically:
    - It is unclear if XBlocks ought to have filesystem-as-a-service,
      or just as a field, as per below. Below requires an FS service,
      but it is not clear XBlocks should know about it.
    """
    @public()
    def load(self, instance: Field, xblock: Blocklike) -> FS:
        """
        Get the filesystem for the field specified in 'instance' and the
        xblock in 'xblock' It is locally scoped.
        """
        return djpyfs.get_filesystem(scope_key(instance, xblock))

    def __repr__(self):
        return "File system object"
