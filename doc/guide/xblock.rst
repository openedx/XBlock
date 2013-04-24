=======
XBlocks
=======

XBlocks are Python classes that implement a small web application. Like full
applications, they have state and methods, and operate on both the server and
the client.


Python Structure
----------------

XBlocks are implemented as Python code, and packaged using standard Python
techniques.  They have Python code, and other file resources, including CSS and
Javascript needed to fully render themselves in a browser.


State
-----

XBlock state (or data) is arbitrary JSON-able data.  XBlock state can be scoped
on several axes:

* By User: State scoped by user is different for every user in the system.

* By XBlock: State scoped by XBlock can be scoped by various aspects of the
  XBlock:

  * block usage - the instance of the XBlock in a particular course

  * block definition - the definition of an XBlock created by a content
    creator (potentially shared across runs of a course)

  * block type - the Python type of the XBlock (shared across all instances
    of the XBlock in all courses)

  * all - all XBlocks share the same data

For example:

* A user's progress through a particular set of problems would be stored in a
  User=True, XBlock=Usage scope.

* The content to display in an XBlock would be stored in a User=False,
  XBlock=Definition scope.

* A user's preferences for a type of XBlock, such as the preferences for a
  circuit editor, would be stored in a User=True, XBlock=Type scope.

* Information about the user, such as language or timezone, would be stored in
  a User=True, XBlock=All scope.

XBlocks declare their data with a schema in the XBlock class definition.  The
schema defines a series of properties, each of which has at least a name, a
type, and a scope::

    upvotes = Integer(help="Number of up votes", display_name="Up Votes", default=0, scope=Scope(user=False, module=DEFINITION))
    downvotes = Integer(help="Number of down votes", display_name="Down Votes", default=0, scope=Scope(user=False, module=DEFINITION))
    voted = Boolean(help="Whether a student has already voted", default=False, scope=Scope(user=True, module=USAGE))

For convenience, we also provide five predefined scopes: ``Scope.content``,
``Scope.settings``, ``Scope.user_state``, ``Scope.preferences``, and
``Scope.user_info``.

In XBlock code, state is accessed as attributes on self. In our example above,
the data is available as ``self.upvotes``, ``self.downvotes``, and
``self.voted``.  The data is automatically scoped for the current user and
block.  Modifications to the attributes are persisted implicitly, there is no
save() method.  The runtime is free to provide these attributes however it
likes.  For example, it could pre-load the data from a database, or proxy the
attributes to load them lazily.  It could provide explicitly stored data, or it
could provide calculated values as it sees fit.


Children
--------

In contrast to the conceptual view of XBlocks, an XBlock does not refer
directly to its children. Instead, the structure of a tree of XBlocks is
maintained by the runtime, and is made available to the XBlock through a
runtime service.

This allows the runtime to store, access, and modify the structure of a course
without incurring the overhead of the XBlock code itself.  The children will
not be implicitly available.  The runtime will provide a list of child ids, and
a child can be loaded with a get_child() function call.  This means the runtime
can defer loading children until they are actually required (if ever).

.. todo::

    When editing an XBlock, it might want to modify its children. How can it do
    that?


Methods
-------

The behavior of an XBlock is determined by its methods, which come in a few
categories:

* Views: These are invoked by the runtime to render the XBlock. There can be
  any number of these, written as ordinary Python methods.  Each view has a
  specific name, such as "edit" or "read", specified by the runtime that will
  invoke it.

  A typical use of a view is to produce a :ref:`fragment <fragment>` for
  rendering the block as part of a web page.  The user state, settings, and
  preferences may be used to affect the output in any way the XBlock likes.
  Views can indicate what data they rely on, to aid in caching their output.

  Although views typically produce HTML-based renderings, they can be used for
  anything the runtime wants.  The runtime description of each view should be
  clear about what return type is expected and how it will be used.

* Handlers: Handlers provide server-side logic invoked by AJAX calls from the
  browser. There can be any number of these, written as ordinary Python
  methods.  Each handler has a specific name of your choice, such as "submit"
  or "preview." The runtime provides a mapping from handler names to actual
  URLs so that XBlock Javascript code can make requests to its handlers.
  Handlers can be used with GET requests as well as POST requests.

* Recalculators: (not a great word!) There can be any number of these, written
  as ordinary Python methods. Each has a specific name, and is invoked by the
  runtime when a particular kind of recalculation needs to be done.  An example
  is "regrade", run when a TA needs to adjust a problem, and all the students'
  inputs should be checked again, and their grades republished.

* Methods: XBlocks have access to their children and parent, and can invoke
  methods on them simply by invoking Python methods.

Views and Handlers are both inspired by web applications, but have different
uses, and therefore different designs.  Views are invoked by the runtime to
produce a rendering of some course content.  Their results are aggregated
together hierarchically, and so are not expressed as an HTTP response, but as a
structured Fragment.  Handlers are invoked by XBlock code in the browser, so they
are defined more like traditional web applications: they accept an HTTP
request, and produce an HTTP response.


Views
-----

Views are how XBlocks render themselves.  The runtime will invoke a view as
part of creating a webpage for part of a course.  The XBlock view should return
data in the form needed by the runtime.  Often, the result will be a
:ref:`fragment <fragment>` that the runtime can compose together into a
complete page.

Views can specify caching information to let runtimes avoid invoking the view
more frequently than needed.  TODO: Describe this.


Handlers
--------

TODO: Describe handlers.


Querying
--------

Blocks often need access to information from other blocks in a course.  An exam
page may want to collect information from each problem on the page, for
example.

TODO: Describe how that works.


Tags
----

TODO: Blocks can have tags and you can use them in querying.
