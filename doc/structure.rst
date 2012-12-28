================
XBlock Structure
================

XBlocks are Python classes that implement a small web application. Like full
applications, they have state and methods, and operate on both the server and
the client.


Python Structure
----------------

XBlocks are implemented as Python applications, and packaged using standard
Python packaging techniques.  They have Python code, and other file resources,
including CSS, Javascript needed to fully render themselves in a browser.


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

    upvotes = Int(help="Number of up votes", default=0, scope=Scope(user=False, module=DEFINITION))
    downvotes = Int(help="Number of down votes", default=0, scope=Scope(user=False, module=DEFINITION))
    voted = Boolean(help="Whether a student has already voted", default=False, scope=Scope(user=True, module=USAGE))

For convenience, we also provide predefined scopes: ``Scope.content``,
``Scope.user_state``, ``Scope.preferences``, and ``Scope.user_info``.

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
