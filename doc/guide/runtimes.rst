========
Runtimes
========

In casual XBlock terms, a **Runtime** is the application that hosts XBlocks.

Nomenclature
------------

There are several entities that go by the name **Runtime**. This will attempt
to provide context and names to disambiguate them.

**Runtime Application**

    This is a general term used to refer to the application code hosting the
    XBlocks.

:class:`~xblock.runtime.Runtime`

    This is the interface that XBlocks use to access resources from the runtime
    application. For example, the XBlock can ask for the URL to use in order to
    call into one of its handlers using :meth:`.Runtime.handler_url` or it can
    render a view on one of its children using :meth:`.Runtime.render_child`.

Responsibilities
----------------

As hosts for XBlocks, runtime applications are responsible for instantiating
XBlocks with the correct data access functionality, displaying the HTML
returned by XBlock views, binding the front-end Javascript to the correct DOM
elements, and routing handler requests back from the client-side XBlock to the
server-side handlers.

Contracts
---------

Runtime applications SHOULD document which views they will call on the XBlock.
A runtime is permitted to provide additional methods on its :class:`.Runtime`
instance for use inside those views.

Extending XBlocks
-----------------

When constructing a :class:`.Runtime` instance, a runtime application can
provide a list of mixin classes. These classes will be used whenever the
:class:`.Runtime` constructs an :class:`.XBlock` to generate a new subclass of
that XBlock with the mixins added as base classes. This allows a runtime
application to add field data and methods to all XBlocks that it hosts, without
requiring that the XBlocks themselves being aware of the runtime they are being
hosted in.


======================
Creating a new Runtime
======================

To build a new host for XBlocks, an author must provide several things:

* A :class:`.Runtime` implementation, which provides access to external
  resources and is responsible for constructing XBlocks.

* A :class:`.FieldData` implementation, which provides access the underlying
  data storage for the XBlock fields.

* [Proposed] A :class:`.UsageStore`, which provides mappings between the
  various fields of :class:`.ScopeIds`.

In each case, by overriding specific methods in those classes, the runtime
application determines the behavior of the XBlocks.

A runtime application also provides access to some set of XBlock views and
handlers.


Rendering Views
---------------

A runtime application document which views it will render on the XBlocks that
it hosts, and in what context it will render those views. XBlock developers
write views with those specific names so that they interact properly with the
application.

When a runtime application renders a view (by calling :meth:`.Runtime.render`
or :meth:`.XBlock.render`), it will receive a :class:`.Fragment` as a result.
It should embed :attr:`.Fragment.content` into the HTML it is producing, add
:meth:`.Fragment.head_html` to the head of the page, and add
:meth:`.Fragment.foot_html` to the foot of the page. This ensures that the
Javascript and CSS of all of the fragments on the page are combined properly.


Routing Handlers
----------------

The runtime application needs to route requests from the client-side XBlock to
the server-side XBlock handler functions. The runtime's implementation of
:meth:`.Runtime.handler_url` must return a relative URL that the client-side
XBlock can call to pass data back to the server.  Authentication of the handler
is managed by the runtime application, although you can also request a URL that
is unauthenticated for use from third-party applications.

:class:`.XBlock` implementations may have arbitrarily named handler functions,
so the runtime application must be able to route to any of them.
