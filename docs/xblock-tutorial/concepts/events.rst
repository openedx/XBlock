.. _XBlocks, Events, and Grading:

#############################
XBlocks, Events, and Grading
#############################

Events are emitted by the server or the browser to capture information about
interactions with the courseware.

In most cases, your XBlock must emit events. 

For example, :ref:`assigning a grade <Publish Grade Events>` is a common event.

.. contents::
 :local:
 :depth: 1
   
.. _Publish Events in Handler Methods:

**********************************
When an XBlock Should Emit Events
**********************************

Analysis of events can provide insight about how learners use the XBlock. Using
event data, analysts should be able to reconstruct the state of the XBlock at
any point in time.

Your XBlock should emit an event whenever a significant state change occurs,
and when a grade for the learner's interaction is assigned. For example, when a
learner submits an answer or otherwise interacts with your XBlock, an event
should record that action.

To assign grades from your XBlock, it must emit a :ref:`grade event <Publish
Grade Events>`.

**********************************
Publish Events in Handler Methods
**********************************

You define :ref:`handler methods <Handler Methods>` to emit events.

In the handler, you use the XBlock runtime interface ``publish`` method
to emit the event. The ``runtime.publish`` method causes the runtime
application to save the event data in the application event stream.

The following code shows the ``runtime.publish`` method syntax in an XBlock
handler.

.. code-block:: python

  self.runtime.publish(self, "event_type",
                       { event_dictionary })

Note the following information about the ``runtime.publish`` method.

* The ``event_type`` uniquely identifies the event in log files. 

* The event dictionary contains key-value pairs that define the event. 

.. _Publish Grade Events:

********************
Publish Grade Events
********************

To assign a grade for a learner's interaction with the XBlock, the XBlock
handler method must publish a grade event.

A grade event uses the ``runtime.publish`` method with specific arguments.

* The event type is ``grade``.

* The event dictionary must contain two entries.

  * ``value``: The learner's score
  * ``max_value``: The maximum possible score
  
The current user's ``user_id`` is implicit in the event dictionary.

..The event dictionary can also contain the ``user_id`` entry. If ``user_id`` is not specified, the current user's ID is used.

For example, the following handler code emits a grade for the learner that is
stored in the ``submission_result`` variable in an XBlock with the maximum
grade of ``1.0``.

.. code-block:: python

   self.runtime.publish(self, "grade",
                       { value: submission_result
                         max_value: 1.0 })

Typically, the handler method also returns the calculated grade, so that it can
be displayed to the learner.

====================
has_score Variable
====================

To be graded, in addition to publishing the grade event, the XBlock must also
have a ``has_score`` variable set to ``True``.

.. code-block:: python

    has_score = True

.. include:: ../../links.rst
