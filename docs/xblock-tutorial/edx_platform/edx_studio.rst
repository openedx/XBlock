.. _EdX Studio as an XBlock Runtime:

###############################
EdX Studio as an XBlock Runtime
###############################

EdX Studio is the application in the edX Platform that instructors use to build
courseware.

Because instructors use Studio to add and configure XBlocks, Studio is
also an :ref:`XBlock runtime <XBlock Runtimes>` application.

As an XBlock developer, you must understand what XBlock properties Studio
requires.

*******************************
Studio Requirements for XBlocks
*******************************

Studio requires XBlocks to have the following properties.

* A :ref:`view method <View Methods>` named ``studio_view``. This is the view
  that renders the XBlock in the Studio editor, allowing the instructor to
  configure it. In Studio, the instructor accesses this view by selecting
  **Edit** in the component.

* A view method named ``author_view``. This view is used to display the XBlock
  in the Studio preview mode.  

  The ``author_view`` method should be as close as possible to the LMS
  ``student_view``, but may contain inline editing capabilities. 

  If you do not define an ``author_view``, the preview mode uses the
  ``student_view``. For more information, see :ref:`EdX Learning Management
  System as an XBlock Runtime`.

* A class property named ``non_editable_metadata_fields``. This variable
  contains a list of the XBlock fields that should not be displayed in the
  Studio editor.


.. include:: ../../links.rst
