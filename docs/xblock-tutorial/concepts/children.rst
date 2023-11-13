.. _XBlock Children:

####################
XBlock Children
####################

An XBlock can have child XBlocks. 

.. contents::
 :local:
 :depth: 1

**********************
XBlock Tree Structure
**********************

An XBlock does not refer directly to its children. Instead, the structure of a
tree of XBlocks is maintained by the runtime application, and is made available
to the XBlock through a runtime service. For more information, see :ref:`XBlock
Runtimes`.

This allows the runtime to store, access, and modify the structure of a course
without incurring the overhead of the XBlock code itself.

XBlock children are not implicitly available to their parents. The runtime
provides the parent XBlock with a list of child XBlock IDs. The child XBlock
can then be loaded with the ``get_child()`` function. Therefore the runtime can
defer loading child XBlocks until they are actually required.

.. example?

********************************
Accessing Children (Server-Side)
********************************

To access XBlock children through the server, use the following methods.

* To iterate over the XBlock’s children, use ``self.get_children`` which
  returns the IDs for each child XBlock.

* Then, to access a child XBlock, use ``self.get_child(usage_id)`` for
  your desired ID. You can then modify the child XBlock using its ``.save()``
  method.

* To render a given child XBlock, use ``self.runtime.render_child(usage_id)``.

* To render all children for a given XBlock, use
  ``self.runtime.render_children()``.

* To ensure the XBlock children are rendered correctly, add the
  ``fragment.content`` into the parent XBlock's HTML file, then use
  ``fragment.add_frag_resources()`` (or ``.add_frags_resources()``, to render
  all children). This ensures that the JavaScript and CSS of child elements are
  included.

.. examples?

********************************
Accessing Children (Client-Side)
********************************

To access XBlock children through the client, with JavaScript, use the
following methods.

* Use ``runtime.children(element)``, where ``element`` is the DOM node that
  contains the HTML representation of your XBlock’s server-side view.
  (``runtime`` is automatically provided by the XBlock runtime.)
  
* Similarly, you can use ``runtime.childMap(element, name)`` to get a child
  element that has a specific name. 

.. examples?

.. include:: ../../links.rst
