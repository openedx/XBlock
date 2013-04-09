======
XBlock
======

.. note::

    This is extremely preliminary documentation.  Please get in touch with us
    if you have any questions or concerns. Do not make any plans based on this
    document without talking to us first.

    The ideas here are our current best guess at how XBlocks will work, but
    some parts are more settled than others.


To create rich engaging online courses, course authors must be able to combine
components from a variety of sources.  XBlock is edX's component architecture
that makes this possible.  Courses are built hierarchically of pieces called
**XBlocks**. Like an HTML ``<div>``, XBlocks can represent pieces as small as a
paragraph of text, a video, or a multiple-choice input field, or as large as a
section, a chapter, or an entire course.

XBlocks are not limited to just delivering courses.  A complete educational
ecosystem will make use of a number of web applications, all of which will need
access to course content and data.  XBlocks provide the structure and APIs
needed to build components for use in all of these applications.

Contents:

.. toctree::
    :maxdepth: 2

    concepts
    guide/xblock
    guide/fragment


API
===

.. toctree::
    :maxdepth: 1
    :glob:

    api/*

..
    Outline:

    - Concepts
        - Roles
    - XBlock structure
        - Python structure
        - State
        - Methods
    - Getting started
    - The XBlock Workbench
    - Writing an XBlock
        - Views
        - Fragments
    - Existing XBlock types


..
    Indices and tables
    ==================

    * :ref:`modindex`
