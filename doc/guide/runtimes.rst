========
Runtimes
========

In casual XBlock parliance, a ``Runtime`` is the application that hosts
the XBlocks.

Nomenclature
------------

There are several entities that go by the name ``Runtime``. This will attempt to provide
context and names to disambiguate them.

``Runtime Application``
    This is a general term used to refer to the application code hosting the ``XBlocks``

:class:`~xblock.runtime.Runtime`
    This is the interface that may be used by :class:`~xblock.core.XBlock` to access
    resources provided by the runtime application. For example, the :class:`~xblock.core.XBlock`
    can ask for the url to use in order to call into one of its handlers using
    :method:`~xblock.runtime.Runtime.handler_url` or it can render a view on one
    of its children using :method:`~xblock.runtime.Runtime.render_child`

Responsibilities
----------------

As hosts for ``XBlocks``, ``Runtime Applications`` are responsible for instantiating
``XBlocks`` with the correct data access functionality, displaying the html returned
by ``XBlock`` views, binding the frontend javascript to the correct DOM elements, and
routing handler requests back from the client-size ``XBlock`` to the server-side handlers.

Contracts
---------

``Runtime Applications`` SHOULD document which views they will call on the ``XBlock``. A runtime is
permitted to provide additional methods on it's :class:`~xblock.runtime.Runtime` instance
for use inside those views.

Extending XBlocks
-----------------

When constructing a :class:`~xblock.runtime.Runtime` instance, a ``Runtime Application``
provide a list of mixin classes. These classes will be used whenever the :class:`~xblock.runtime.Runtime`
contstructs an :class:`~xblock.core.XBlock` to generate a new subclass of that :class:`~xblock.core.XBlock`
with the mixins added as base classes. This functionality allows a ``Runtime Application`` to
add field data and methods to all `XBlocks` that it hosts, without requiring that the ``XBlocks``
themselves being aware of the runtime they are being hosted in.