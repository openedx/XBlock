.. _XBlock Fields:

#############
XBlock Fields
#############

You use XBlock fields to store state data for your XBlock.

.. contents::
 :local:
 :depth: 1

.. link to fields api doc

************************
XBlock Fields and State
************************

XBlock fields are Python attributes that store user and XBlock state as JSON
data.

You define the fields in the XBlock Python file. For example, the ``thumbs.py``
file in the XBlock SDK includes three fields.

.. include:: ../reusable/code_thumbs_fields.rst

=================
Field Names
=================

The field names you define in the Python file are also used in the XBlock
:ref:`JavaScript<The XBlock JavaScript File>` and :ref:`HTML<The XBlock HTML
File>` code.

..
  =================
  Field Types
  =================

  TBP

=================
Field Parameters
=================

When you initialize an XBlock field, you define three parameters.

* ``help``: A help string for the field that can be used in an application such
  as edX Studio.

* ``default``: The default value for the field.

* ``scope``:  The scope of the field.  For more information, see the next
  section.

.. _Field Scope:

***********
Field Scope
***********

Field scope is the relationship of the field to users and the XBlock.

You define the field scope when initializing the field in the XBlock Python
file. For example, in ``thumbs.py``, the ``voted`` field is initialized to have
the scope ``user_state``.

.. code-block:: python

    voted = Boolean(help="Has this student voted?", default=False,
        scope=Scope.user_state)

===========
User Scope
===========

Fields can relate to users in the following ways.

* **No user**: the field data is not related to any users. No learner activity
  created modified the field value, and all learners see the same value.For
  example, a field that contains course content is independent of users.

  .. note:: The XBlock cannot modify the value of a field that is not related
    to any users.

* **One user**: the field data is specific to a single user. For example, the
  answer to a problem is specific to the user who submitted it.

* **All users**: the field data is common for all users. Learner activity can
  change the field value, and all learners see the same value. For example, the
  total number of learners who answer a question is the same for all users.

  .. note:: Field data related to all users is not the same as aggregate or
    query data. The same value is shared for all users, and you cannot
    associate specific actions to specific users.

============
XBlock Scope
============

Fields can relate to XBlocks in the following ways.

* **Block usage**: the field data is related to an instance, or usage, of the
  XBlock in a particular course. In most cases, you use the **Block usage**
  scope. For example, for an XBlock that polls learners and shows totals for
  each response, you would need the question and available answers to be
  specific to that instance of the XBlock in your course.

* **Block definition**: the field data is related to the definition of the
  XBlock. The definition is specified by the content creator. A definition can
  be shared across one or more uses. For example, you could create a single
  XBlock definition with many uses, and those uses can appear across
  courses or within the same course.

* **Block type**: The field data is related to the Python type of the XBlock,
  and is shared across all instances of the XBlock in all courses.

* **All**: The field data is related to all XBlocks, of all types. Any
  XBlock can access the field data.

  .. note::
    When you use the **All** scope, there is potential for name conflicts. If
    you have two fields of the same name with the scope **All** in different
    XBlock types, both fields point to the same data. Therefore you should use
    caution when using **All**.

=================================
User and Block Scope Independence
=================================

The user and block scope of a field are independent of each other.  The field
scope you define specifies both. The following examples show different ways you
can combine user and block scope.

* A user's progress through a particular set of problems is stored in a field
  with the scope **One user** and **XBlock usage**.

* The content to display in an XBlock is stored in a field with the scope **No
  user** and **Block definition**.

* A user's preferences for a type of XBlock are stored in a field with the
  scope with **One user** and **XBlock type**.

* Information about the user, such as language or timezone, is stored in a
  field with the scope with **One user** and **All**.

Scope combinations that are used together frequently are available is a set of
predefined scopes, as described below.

=================================
Predefined Scopes
=================================

XBlock includes the following predefined scopes that you can use when
configuring fields. Each of these scopes includes the indicated user and block
scope settings.

* ``Scope.content``

  * Block definition
  * No user

* ``Scope.settings``

  * Block usage
  * No user

* ``Scope.user_state``

  * Block usage
  * One user

* ``Scope.preferences``

  * Block type
  * One user

* ``Scope.user_info``

  * All blocks
  * One user

* ``Scope.user_state_summary``

  * Block usage
  * All users

************************
Fields and Data Storage
************************

.. What is large?

Because XBlock fields are written and retrieved as single entities, you cannot
store a large amount of data in a single field.

To store very large amounts of data, you should split the data across many
smaller fields.

********************
Initializing Fields
********************

You do not use the ``__init__`` method with XBlocks.

XBlocks can be used in many contexts, and the ``__init__`` method might not
work in those contexts.

To initialize field values, use one of the following alternatives.

* Use ``xblock.fields.UNIQUE_ID`` to set a default string value for the field.

* Use a lazy property decorator, so that when a field is first accessed, a
  function is called to set the value.

* Run the logic to set the default field value in the view instead of the
  ``__init__`` method.

***************
Fields and OLX
***************

XBlock fields map to attributes in the OLX (open learning XML) definition.

For example, you might include the fields ``href``, ``maxwidth``, and
``maxheight`` in a ``SimpleVideoBlock`` XBlock.  You configure the fields as in
the following example.

.. code-block:: python

  class SimpleVideoBlock(XBlock):
      """
      An XBlock providing Embed capabilities for video
      """

      href = String(help="URL of the video page at the provider",
          default=None, scope=Scope.content)
      maxwidth = Integer(help="Maximum width of the video", default=800,
          scope=Scope.content)
      maxheight = Integer(help="Maximum height of the video", default=450,
          scope=Scope.content)

By default, the ``SimpleVideoBlock`` XBlock is represented in OLX as in the
following example:

.. code-block:: xml

    <simplevideo
        href="https://vimeo.com/46100581"
        maxwidth="800"
        maxheight="450"
    />

You can customize the OLX representation of the XBlock by using the
``xblock.parse_xml()`` and ``xblock.add_xml_to_node()`` methods.

.. add links to api doc

**************************************
Field Requirements in the edX Platform
**************************************

For information about field requirements in the edX Platform, see :ref:`Open edX LMS
<Open edX Learning Management System as an XBlock Runtime>` and
:ref:`Open edX Studio <Open edX Studio as an XBlock Runtime>`.

******************************
Default Fields in a New XBlock
******************************

When you create a new XBlock, the ``count`` field is added to the Python file
by default. This field is for demonstration purposes and you should replace it
with your own field definitions.

.. include:: ../../links.rst
