.. _XBlock Methods:

##############
XBlock Methods
##############

You use XBlock methods in the XBlock Python file to define the behavior of your
XBlock.

.. contents::
 :local:
 :depth: 1

.. _View Methods:

************
View Methods
************

XBlock view methods are Python methods invoked by the XBlock runtime to render
the XBlock.

An XBlock can have multiple view methods. For example, an XBlock might have a
student view for rendering the XBlock for learners, and an editing view for
rendering the XBlock to course staff.

.. note::
  The XBlock view names are specified by runtime applications; you cannot use
  arbitrary view names.

For information about the view requirements in the edX Platform, see :ref:`Open edX
LMS <Open edX Learning Management System as an XBlock Runtime>` and
:ref:`Open edX Studio <Open edX Studio as an XBlock Runtime>`.

Typically, you define a view to produce a fragment that is used to render the
XBlock as part of a web page. Fragments are aggregated hierarchically. You can
use any field to affect the rendering of the XBlock as needed.

In the following example, the Thumbs sample XBlock in the XBlock SDK defines a
student view.

.. include:: ../reusable/code_thumbs_student_view.rst

Although view methods typically produce HTML-based renderings, they can be used
for other purposes. See the documentation for your runtime application to
verify the type of data the view must return and how it will be used.

.. _Handler Methods:

***************
Handler Methods
***************

You write handlers to implement the server side of your XBlock's interactive
features.

XBlock handlers are Python methods invoked by AJAX calls from the user's
browser. Handlers accept an HTTP request and return an HTTP response.

An XBlock can have any number of handlers. For example, a problem XBlock
might contain ``submit`` and ``show_answer`` handlers.

Each handler has a specific name of your choosing that is mapped to from
specific URLs by the runtime. The runtime provides a mapping from handler names
to specific URLs so that the XBlock JavaScript code can make requests to its
handlers. Handlers can be used with ``GET`` and ``POST`` requests.

Handler methods also emit events for learner interactions and grades. For more
information, see :ref:`Publish Events in Handler Methods`.

In the following example, the Thumbs sample XBlock in the XBlock SDK defines a
handler for voting.

.. code-block:: python

    def vote(self, data, suffix=''):  # pylint: disable=unused-argument
        """
        Update the vote count in response to a user action.
        """
        # Here is where we would prevent a student from voting twice, but then
        # we couldn't click more than once in the demo!
        #
        #     if self.voted:
        #         log.error("cheater!")
        #         return

        if data['voteType'] not in ('up', 'down'):
            log.error('error!')
            return

        if data['voteType'] == 'up':
            self.upvotes += 1
        else:
            self.downvotes += 1

        self.voted = True

        return {'up': self.upvotes, 'down': self.downvotes}

*******************************
Default Methods in a New XBlock
*******************************

When you create a new XBlock, two methods are added automatically.

* The view method ``student_view``.

  You can modify the contents of this view, but to use your XBlock with the edX
  Platform, you must keep the method name ``student_view``.

* The handler method ``increment_count``.

  This method is for demonstration purposes and you can remove it.


.. include:: ../../links.rst
