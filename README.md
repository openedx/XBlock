xmodule-debugger
================

This is a "code sketch" we wrote while designing the new XBlock architecture.
It illustrates working XBlocks.  The goal was not to implement entire courses,
but to get enough interesting test cases together in one place to try the
design and see how it felt to make it actually work.


Installation
------------

1. Get a local copy of this repo.

2. (Optional)  Create and activate a virtualenv to work in.

3. Install the requirements and register the XBlock entry points with (you may
   need to sudo this if you don't use virtualenv)::

    $ pip install -r requirements.txt

4. Run the Django development server:

    $ python manage.py runserver

5. Open a web browser to: http://127.0.0.1:8000


Reading the code
----------------

There are three distinct layers to this code:

1. The sample XBlock code.  This is the most important, it is the code that our
   customers will be writing, and demonstrates the XBlock interfaces.

2. The runtime code that we think will be common to all runtimes.  This is the
   behind-the-scenes code edX will write to make XBlocks work.  This layer may
   not be real code here, but we'll need to write real code to perform these
   functions.

3. The debugger-specific code we wrote to make everything work.  This code is
   the least real, in that it might be just stubs, and will be done very
   differently in real code.
