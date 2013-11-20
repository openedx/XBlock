========
Runtimes
========

In casual XBlock parliance, a ``Runtime`` is the application that hosts
the ``XBlocks``.

Nomenclature
------------

There are several entities that go by the name ``Runtime``. This will attempt to provide
context and names to disambiguate them.

``Runtime Application``
    This is a general term used to refer to the application code hosting the ``XBlocks``

:class:`~xblock.runtime.Runtime`
    This is the interface that may be used by :class:`.XBlock` to access
    resources provided by the runtime application. For example, the :class:`.XBlock`
    can ask for the url to use in order to call into one of its handlers using
    :meth:`.Runtime.handler_url` or it can render a view on one
    of its children using :meth:`.Runtime.render_child`

Responsibilities
----------------

As hosts for ``XBlocks``, ``Runtime Applications`` are responsible for instantiating
``XBlocks`` with the correct data access functionality, displaying the html returned
by ``XBlock`` views, binding the frontend javascript to the correct DOM elements, and
routing handler requests back from the client-size ``XBlock`` to the server-side handlers.

Contracts
---------

``Runtime Applications`` SHOULD document which views they will call on the ``XBlock``.
A runtime is permitted to provide additional methods on it's :class:`.Runtime` instance
for use inside those views.

Extending XBlocks
-----------------

When constructing a :class:`.Runtime` instance, a ``Runtime Application``
provide a list of mixin classes. These classes will be used whenever the :class:`.Runtime`
contstructs an :class:`.XBlock` to generate a new subclass of that :class:`.XBlock`
with the mixins added as base classes. This functionality allows a ``Runtime Application`` to
add field data and methods to all `XBlocks` that it hosts, without requiring that the ``XBlocks``
themselves being aware of the runtime they are being hosted in.


======================
Creating a new Runtime
======================

To build a new host for ``XBlocks``, an author must provide several things:

* A :class:`.Runtime` implementation, which provides access to external resources and is responsible
  for constructing :class:`.XBlock` s
* A :class:`.FieldData` implementation, which provides access the underlying data storage for the
  :class:`.XBlock` s fields.
* [Proposed] A :class:`.UsageStore`, which provides mappings between the various fields of
  :class:`.ScopeIds`

In each case, by overriding specific methods in those classes, the ``Runtime Application`` determines
the behavior of the ``XBlocks``.

The other thing that a ``Runtime Application`` must do is to provide access to some set of
:class:`.XBlock` views and handlers.


Rendering Views
---------------

A ``Runtime Application`` should publish documentation about which views it will render on
the ``XBlocks`` that it hosts, and in what context it will render those views. That way, ``XBlocks``
can be written to provide the views needed for the ``Runtime``.

When a ``Runtime Application`` renders a view (by calling :meth:`.Runtime.render` or :meth:`.XBlock.render`),
it will recieve a :class:`.Fragment` as a result. It should embed :attr:`.Fragment.content` into the html
page to render, add :meth:`.Fragment.head_html` to the head of the page, and add :meth:`.Fragment.foot_html` to the foot of the page. This will enable the javascript and css of all of the fragments that were combined to render the particular :class:`.XBlock`.

Routing Handlers
----------------

The ``Runtime Application`` needs to route requests from the client-side ``XBlock`` to the
server-side ``XBlock.handler`` functions. The implementation of :meth:`.Runtime.handler_url` must
return a relative url that the client-side ``XBlock`` can call to pass data back to the server.
Authentication of the handler should be managed by the ``Runtime Application``.

:class:`.XBlock` implementations may have arbitrarily named handler functions, so the ``Runtime Application``
must be able to route to any of them.