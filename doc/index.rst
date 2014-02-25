======================================
XBlock: Open edX courseware components
======================================

.. note::

    This is still preliminary documentation.  Please get in touch with us
    if you have any questions or concerns. Do not make any plans based on this
    document without talking to us first.

    edX is in the process of implementing XBlock support, and that effort
    could produce changes to these documents.

To create rich, engaging online courses, course authors must be able to combine
components from a variety of sources.  XBlock is edX's component architecture
that makes this possible.  Courses are built hierarchically of pieces called
**XBlocks**. Like an HTML ``<div>``, XBlocks can represent pieces as small as a
paragraph of text, a video, or a multiple-choice input field, or as large as a
section, a chapter, or an entire course.

XBlocks are not limited to just delivering courses.  A complete educational
ecosystem will make use of a number of web applications, all of which will need
access to course content and data.  XBlocks provide the structure and APIs
needed to build components for use in all of these applications.

Getting Started
---------------

How to begin writing an XBlock.

.. toctree::
    :maxdepth: 2

    getting_started

User's Guide
------------

The concepts of XBlock, in depth.

.. toctree::
    :maxdepth: 2

    concepts
    guide/xblock
    guide/runtimes
    guide/fragment

API
---

Details of the XBlock APIs.

.. toctree::
    :maxdepth: 2

    api/xblock
    api/fields
    api/runtime
    api/fragment
    api/exceptions


Project Info
------------

Other information about the project.

.. toctree::
    :maxdepth: 1

    changelog

..
    Indices and tables
    ==================

    * :ref:`modindex`
