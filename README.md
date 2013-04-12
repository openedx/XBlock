XBlock Courseware Components
============================

XBlock is a component architecture by edX.org for building courseware.

This is a pre-alpha release of the XBlock API, to gather input from potential
users of the API.  We like what is here, but are open to suggestions for
changes. We will be implementing this shortly in the edX LMS.

This repo contains the core code for implementing XBlocks as well as a simple
workbench application for running XBlocks in a small simple environment.


Background
----------

EdX courseware is built out of components that are combined hierarchically.
These include components like the video player,
[LON-CAPA](http://www.lon-capa.org/) problems, as well as compound components
like learning sequences. We are developing a second-generation API for these
components called XBlocks. Although they're in a prototype stage, we like the
API, and want to collaborate with others to develop them into an industry
standard. This is our proposed API and specification for XBlocks.

How does this differ from existing industry standards like [Learning Tools
Interoperability](http://www.imsglobal.org/toolsinteroperability2.cfm) (LTI)
and [SCORM](http://scorm.com/scorm-explained/)? On a high level, XBlocks is a
Python language-level API, and it provides sensible defaults for things like
storing data. XBlocks could be wrapped up in LTI, and one could make an LTI
XBlock. The core reason to write an XBlock is that it is deployable. You can
give us the code to an XBlock, and we can embed it in our courseware. LTI would
require you to give us a virtual machine image which ran it.


Installation
------------

This code runs on Python 2.7.

1.  Get a local copy of this repo.

2.  (Optional)  Create and activate a virtualenv to work in.

3.  Install the requirements and register the XBlock entry points with (you may
    need to sudo this if you don't use virtualenv):

        $ pip install -r requirements.txt

4.  Run the Django development server:

        $ python manage.py runserver

5.  Open a web browser to: http://127.0.0.1:8000


Using the workbench
-------------------

When you open the workbench, you'll see a list of sample XBlock configurations
(scenarios).  Each will display a page showing the XBlocks composited together,
along with internal information like the "database" contents.

The workbench doesn't use a real database, it simply stores all data in an
in-memory dictionary.  The data is all lost and reset when you restart the
server.

If you want to experiment with different students, you can use a URL parameter
to set the numeric student ID, which defaults to 1:

    http://127.0.0.1:8000/?student_id=17

Different students will see different student state, for example, while seeing
the same content.


Documentation
-------------

The docs for the XBlock API is on Read The Docs:  https://xblock.readthedocs.org .


Reading the code
----------------

There are distinct layers to this code.  In the docstrings, we've tried to make
clear which layer the code lives in, though sometimes the lines are blurred:

1.  **XBlock** The sample XBlock code.  This is the most important, it is the
    code that most third parties will be writing, and demonstrates the XBlock
    interfaces.

2.  **Runtime** The runtime code that we think will be common to all runtimes.
    This is the behind-the-scenes code edX will write to make XBlocks work.
    This layer may not be real code here, but we'll need to write real code to
    perform these functions.

3.  **Workbench** The workbench-specific code we wrote to make everything work.
    This code is the least real, in that it might be just stubs, and will be
    done very differently in real code.

4.  **Thumbs** This is a sample XBlock written as a separate installable kit as
    an example of how third-party XBlocks can be structured.

5. *Chat* This is another sample XBlock written to demonstrate the use
   of Django templates and third-party libraries in XBlocks. Note that
   to run this XBlock, you'll need to run `python manage.py
   collectstatic` _before_ running the workbench server.


Making your own XBlock
----------------------

Making an XBlock can be as simple as creating a Python class with a few
specific methods.  The ``thumbs`` module demonstrates an XBlock with state,
views, and input handling.

You can provide scenarios for the workbench to display, see the thumbs.py
sample for an example, or the xblock/problem.py file.  The scenarios are
written in a simple XML language.  Note this is not an XML format we are
proposing as a standard.

Once you install your XBlock into your virtualenv, the workbench will
automatically display its scenarios for you to experiment with.


Contacts
--------

The XBlock mailing list is [edx-xblock on Google Groups](https://groups.google.com/forum/#!forum/edx-xblock). 
You can also write to edX directly at info@edx.org.
