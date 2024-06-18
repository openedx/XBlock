"""
Internal machinery used to make building XBlock family base classes easier.
"""
from __future__ import annotations

import functools
import typing as t


# The class upon which the property is declared; i.e., the supertype of all classes
# upon which the property will be defined.
BaseT = t.TypeVar('BaseT')

# The return value of the property.
ReturnT = t.TypeVar('ReturnT')


class LazyClassProperty(t.Generic[BaseT, ReturnT]):
    """
    A descriptor that acts as a class-level @lazy.

    That is, it behaves as a lazily loading class property by
    executing the decorated method once, and then storing the result
    in the class __dict__.
    """
    def __init__(self, wrapped: t.Callable[[BaseT], ReturnT]):

        # _wrapped is the original method on BaseT which we are converting to a classproperty.
        # Crazy typechecking note: From the perspective of the type checker, the wrapped
        # method's argument is an *instance* of BaseT (a "self" arg). In reality, we know that
        # the wrapped method's first arg is used as a *subclass* of BaseT (a "cls" arg).  So, we
        # must subvert the typechecker here by statically casting from [BaseT] to [type[BaseT]].
        self._wrapped: t.Callable[[type[BaseT]], ReturnT] = wrapped  # type: ignore[assignment]

        # The caches maps classes (BaseT or subclasses thereof) to return values.
        self._cache: dict[type[BaseT], ReturnT] = {}

        # This line transfers the "metadata" (function name, docstring, arg names) from _wrapped
        # to self (the descriptor, which becomes the class property). I couldn't get mypy to be
        # happy about this, since it doesn't understand that self is callable.
        functools.wraps(self._wrapped)(self)  # type: ignore

    def __get__(self, _instance: BaseT | None, owner: type[BaseT]) -> ReturnT:
        if owner not in self._cache:
            # If _wrapped iterates over members, then we don't want to call it
            # again in an infinite loop. So, preseed the __cache with None.
            self._cache[owner] = None  # type: ignore
            self._cache[owner] = self._wrapped(owner)
        return self._cache[owner]


class_lazy = LazyClassProperty  # pylint: disable=invalid-name
