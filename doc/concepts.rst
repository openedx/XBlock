========
Concepts
========

XBlock is a component architecture for building courseware.  They are similar
in structure to web applications.


Roles
-----

The XBlock design recognizes a few different roles people can play:

Block Developer

    An XBlock Developer is the author of an XBlock type. This is a Python
    developer writing Python classes to implement a new kind of XBlock.

Content Author

    Original course material is written by a Content Author.  This material
    may be made available to others to use in their own courses.

Course Assembler

    A Course Assembler creates or modifies courses by using content created
    by someone else. Note that the same person can act as a content author
    and as a course assembler, often within the same authoring session.

Student

    The Student (or User) is whoever uses the web applications composed
    of XBlocks.


XBlocks
-------

XBlocks are components that combine together to create interactive course
content.  They need to satisfy two conflicting goals: work together with other
blocks to build a complete course; and be independent of other blocks, so they
can be combined flexibly.

XBlocks are built similarly to web applications.  They maintain state in a
storage layer, render themselves through views, and process user actions
through handlers.

They differ from web applications, though, because each XBlock renders only a
small piece of a complete web page.


Runtime
-------

XBlocks do not run by themselves, they run within web applications such as
edX Studio, or edX LMS, known as runtimes. Each runtime provides services to the
XBlock, such as storage, URL mapping, and analytics.  Runtimes should perform
functions common to all blocks, leaving the XBlock developer to write code
particular to their block.

Runtimes will differ in the context they provide to XBlocks. For example, while
editing content, Studio won't provide user state, because there is no
interesting user state. Another runtime might provide user state, but as
read-only data.

Runtimes also differ in what views they make use of. Studio might use
"author_view" to edit the XBlock content, and "student_view" to preview that
content, while the LMS might only use the "student_view" view to render the
XBlock for students. Each runtime is free to define view names it will use for
its purposes. XBlock Developers need to understand the runtimes they will be
running in to write the proper views.

Runtimes are responsible for performing any authentication needed before
executing a view or handler in an XBlock.

Examples of runtimes:

* edX Studio 
* edX LMS
* XBlock workbench
* Peer grading workflow app
* `XBlock Runtime for Google App Engine`__

__ https://github.com/google/appengine_xblock_runtime

.. todo::

    What other information does the runtime provide? Things people have asked
    about: the name of the course, the identity of the student, the URL to the
    course.

