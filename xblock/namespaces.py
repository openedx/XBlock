"""
Namespaces allow Runtime Applications to inject fields into all of
the XBlocks that they instantiate
"""

from xblock.plugin import Plugin
from xblock.fields import ModelMetaclass, Field


class NamespacesMetaclass(type):
    """
    A metaclass to be used for classes that want to include namespaced fields in their
    instances.

    Any namespaces registered in the `xblock.namespace` will be added to
    the instance
    """
    def __new__(mcs, name, bases, attrs):
        namespaces = []
        for ns_name, namespace in Namespace.load_classes():
            if issubclass(namespace, Namespace):
                attrs[ns_name] = NamespaceDescriptor(namespace)
                namespaces.append(ns_name)
        attrs['namespaces'] = namespaces

        return super(NamespacesMetaclass, mcs).__new__(mcs, name, bases, attrs)


class NamespaceDescriptor(object):
    """
    Holds the descriptor for namespaces. Used by `NamespacesMetaclass` to
    define new namespaces.
    """
    def __init__(self, namespace):
        self._namespace = namespace

    def __get__(self, instance, owner):
        return self._namespace(instance)


class Namespace(Plugin):
    """
    A baseclass that sets up machinery for Field fields that makes those fields be called
    with the container as the field instance
    """
    __metaclass__ = ModelMetaclass

    entry_point = 'xblock.namespace'

    def __init__(self, container):
        self._container = container

    def __getattribute__(self, name):
        container = super(Namespace, self).__getattribute__('_container')
        namespace_attr = getattr(type(self), name, None)

        if namespace_attr is None or not isinstance(namespace_attr, Field):
            return super(Namespace, self).__getattribute__(name)

        return namespace_attr.__get__(container, type(container))

    def __setattr__(self, name, value):
        try:
            container = super(Namespace, self).__getattribute__('_container')
        except AttributeError:
            super(Namespace, self).__setattr__(name, value)
            return

        namespace_attr = getattr(type(self), name, None)

        if namespace_attr is None or not isinstance(namespace_attr, Field):
            return super(Namespace, self).__setattr__(name, value)

        return namespace_attr.__set__(container, value)

    def __delattr__(self, name):
        container = super(Namespace, self).__getattribute__('_container')
        namespace_attr = getattr(type(self), name, None)

        if namespace_attr is None or not isinstance(namespace_attr, Field):
            return super(Namespace, self).__detattr__(name)

        return namespace_attr.__delete__(container)
