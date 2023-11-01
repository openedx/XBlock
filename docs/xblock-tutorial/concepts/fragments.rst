.. _XBlock Fragments:

################
XBlock Fragments
################

A fragment is a part of a web page returned by an XBlock view method. 

.. contents::
 :local:
 :depth: 1

.. link to fragments api doc

*****************
Fragment Contents
*****************

A fragment typically contains all the resources needed to display the XBlock in
a web page, including HTML content, JavaScript, and CSS resources.

=============
HTML Content
=============

Content in a fragment is typically HTML, though some runtimes might require
views that return other mime-types. Each fragment has only a single content
value.

==========
JavaScript
==========

A fragment contains the JavaScript resources necessary to run the XBlock.
JavaScript resources can include both external files to link to, and inline
source code.

When fragments are composed, external JavaScript links are made unique, so
that files are not loaded multiple times.

JavaScript Initializer
***********************

The JavaScript specified for a fragment can also specify a function to be
called when that fragment is rendered on the page.

The DOM element containing all of the content in the fragment is passed to this
function, which then executes any code needed to make that fragment
operational.

The JavaScript view is also passed a JavaScript runtime object that contains
a set of functions to generate links back to the XBlock's handlers and views
on the runtime server.

For example, see the code in the Thumbs XBlock, in the file
``xblock_development/xblock-
sdk/sample_xblocks/thumbs/static/js/source/thumbs.js``.

.. include:: ../reusable/code_thumbs_javascript.rst

=====
CSS
=====

A fragment contains CSS resources to control how the XBlock is displayed. CSS
resources can include both external files to link to and inline source code.

When fragments are composed, external JavaScript links will are made unique, so
that files are not loaded multiple times.

*****************************
Fragments and XBlock Children
*****************************

Because XBlocks are nested hierarchically, a single XBlock view might require
collecting renderings from each of its children, then composing them together.
The parent XBlock view must handle composing its children's content together
to create the parent content.

The fragment system has utilities for composing children’s resources together
into the parent.

.. details on utilities?

********************
Fragments and Views
********************

You configure fragments in XBlock view methods.

In the following example, the Thumbs sample XBlock in the XBlock SDK defines a
student view that composes and returns a fragment with HTML, JavaScript, and
CSS strings generated from the XBlock's static files.

.. include:: ../reusable/code_thumbs_student_view.rst

..
  ********************
  Caching Fragments
  ********************

  TBP

.. include:: ../../links.rst
