#######################
Introduction to XBlocks
#######################

This section introduces XBlocks.

.. contents::
 :local:
 :depth: 1

********
Overview
********

As a developer, you build XBlocks that course teams use to create independent
course components that work seamlessly with other components in an online
course.

For example, you can build XBlocks to represent individual problems or pieces
of text or HTML content. Furthermore, like Legos, XBlocks are composable; you
can build XBlocks to represent larger structures such as lessons, sections, and
entire courses.

A primary advantage to XBlocks is that they are sharable. The code you write
can be deployed in any instance of the Open edX Platform or other XBlock runtime
application, then used by any course team using that system.

In educational applications, XBlocks can be used to represent individual
problems, web-formatted text and videos, interactive simulations and labs, or
collaborative learning experiences. Furthermore, XBlocks are composable,
allowing an XBlock developer to control the display of other XBlocks to compose
lessons, sections, and entire courses.

****************************************
XBlock Independence and Interoperability
****************************************

You must design your XBlock to meet two goals.

* The XBlock must be independent of other XBlocks. Course teams must be able to
  use the XBlock without depending on other XBlocks.

* The XBlock must work together with other XBlocks. Course teams must be
  able to combine different XBlocks in flexible ways.

************************************
XBlocks Compared to Web Applications
************************************

XBlocks are like miniature web applications: they maintain state in a storage
layer, render themselves through views, and process user actions through
handlers.

XBlocks differ from web applications in that they render only a small piece of
a complete web page.
	
Like HTML ``<div>`` tags, XBlocks can represent components as small as a
paragraph of text, a video, or a multiple choice input field, or as large as a
section, a chapter, or an entire course.
