XBlock Courseware Components
============================

XBlock is a component architecture by edX.org for building courseware.

This repo contains the core code for implementing XBlocks as well as a simple
workbench application for running XBlocks in a small simple environment.


Installation
------------

1.  Get a local copy of this repo.

2.  (Optional)  Create and activate a virtualenv to work in.

3.  Install the requirements and register the XBlock entry points with (you may
    need to sudo this if you don't use virtualenv):

        $ pip install -r requirements.txt

4.  Run the Django development server:

        $ python manage.py runserver

5.  Open a web browser to: http://127.0.0.1:8000

You'll see a list of sample XBlock configurations (scenarios).  Each will
display a page showing the XBlocks composited together, along with internal
information like the "database" contents.


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


Making your own XBlock
----------------------

Making an XBlock can be as simple as creating a Python class with a few
specific methods.  The ``thumbs`` module demonstrates an XBlock with state,
views, and input handling.
