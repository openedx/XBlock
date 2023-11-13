.. _Tutorial Introduction to XBlocks:

.. include:: ../../introduction.rst

***********************
XBlock API and Runtimes
***********************

Any web application can be an :ref:`XBlock runtime<XBlock Runtimes>` by
implementing the XBlock API. Note that the XBlock API is not a RESTful API.
XBlock runtimes can compose web pages out of XBlocks that were developed by
programmers who do not need to know anything about the other components that a
web page might be using or displaying.

*********************************
XBlocks and the Open edX Platform
*********************************

The Open edX Platform is an XBlock runtime and the Open edX community
currently provides most of the support for the development of the XBlock library and specification.
Programmers who use Tutor or the edx-platform devstack instead of the xblock-sdk to
develop an XBlock should make sure that their XBlock is fully compliant with
the XBlock specification before deploying to other XBlock runtimes. More
specifically, XBlocks should package any services provided by edx-platform that
a different XBlock compliant runtime might not provide.

The Open edX Platform currently has a large suite of XBlocks built into its primary
repository that are available to course developers. Those XBlocks include HTML
content, videos, and interactive problems. The Open edX Platform also includes many
specialized XBlocks such as the `Google Drive file tool`_
and `Open Response Assessments`_. For more information,
see :ref:`XBlocks and the edX Platform`.

**********************
XBlocks for Developers
**********************

Developers can select from functionality developed by the Open edX community by
installing an XBlock on their instance of Open edX. Developers can integrate
new or propriety functionality for use in XBlock runtimes by developing a new
XBlock using the supported XBlock API.


XBlocks are like miniature web applications: they maintain state in a storage
layer, render themselves through views, and process user actions through
handlers. XBlocks differ from web applications in that they render only a small
piece of a complete web page. Like HTML ``<div>`` tags, XBlocks can represent
components as small as a paragraph of text, a video, or a multiple choice input
field, or as large as a section, a chapter, or an entire course.

=============
Prerequisites
=============

This tutorial is for developers who are new to XBlock. To use this tutorial,
you should have basic knowledge of the following technologies.

* Python
* JavaScript
* HTML and CSS
* Python `VirtualEnv`_
* `Git`_

================
XBlock Resources
================

This tutorial is meant to guide developers through the process of creating an
XBlock, and to explain the :ref:`concepts<XBlock Concepts>` and
:ref:`anatomy<Anatomy of an XBlock>` of XBlocks.

The `XBlock SDK`_  supports the creation of new XBlocks.
Developers should also see the :ref:`Open edX XBlock API Guide`.

========================================
XBlock Independence and Interoperability
========================================

You must design your XBlock to meet two criteria.

* The XBlock must be independent of other XBlocks. Course teams must be able to
  use the XBlock without using other XBlocks.

* The XBlock must work together with other XBlocks. Course teams must be able
  to combine different XBlocks in flexible ways.


.. include:: ../../links.rst
