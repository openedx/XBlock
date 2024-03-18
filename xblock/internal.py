"""
Internal machinery used to make building XBlock family base classes easier.
"""
import functools


class LazyClassProperty:
    """
    A descriptor that acts as a class-level @lazy.

    That is, it behaves as a lazily loading class property by
    executing the decorated method once, and then storing the result
    in the class __dict__.
    """
    def __init__(self, constructor):
        self.__constructor = constructor
        self.__cache = {}
        functools.wraps(self.__constructor)(self)

    def __get__(self, instance, owner):
        if owner not in self.__cache:
            # If __constructor iterates over members, then we don't want to call it
            # again in an infinite loop. So, preseed the __cache with None.
            self.__cache[owner] = None
            self.__cache[owner] = self.__constructor(owner)
        return self.__cache[owner]


class_lazy = LazyClassProperty  # pylint: disable=invalid-name
