Part of `edX code`__.

__ http://code.edx.org/

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
These include components like the video player, `LON-CAPA`_ problems, as well
as compound components like learning sequences. We are developing a
second-generation API for these components called XBlocks. Although they're in
a prototype stage, we like the API, and want to collaborate with others to
develop them into an industry standard. This is our proposed API and
specification for XBlocks.

.. _LON-CAPA: http://www.lon-capa.org/

How does this differ from existing industry standards like `Learning Tools
Interoperability`_ (LTI) and `SCORM`_? On a high level, XBlocks is a Python
language-level API, and it provides sensible defaults for things like storing
data. XBlocks could be wrapped up in LTI, and one could make an LTI XBlock. The
core reason to write an XBlock is that it is deployable. You can give us the
code to an XBlock, and we can embed it in our courseware. LTI would require you
to give us a virtual machine image which ran it.

.. _Learning Tools Interoperability: http://www.imsglobal.org/toolsinteroperability2.cfm
.. _SCORM: http://scorm.com/scorm-explained/


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


Testing
--------

To run the test suite:

    $ python manage.py test

This will run:

    * Unit tests of the XBlock core and runtime.

    * Integration tests of XBlocks running within the workbench.

You can test XBlocks through a browser using `Selenium`_. We have included an
example Selenium test for ``thumbs`` that uses Django's `LiveServerTestCase`_.
It runs as part of the test suite as executed by the above command. You need to
have Firefox installed for this test case to run successfully.

.. _Selenium: http://docs.seleniumhq.org/
.. _LiveServerTestCase: https://docs.djangoproject.com/en/1.4/topics/testing/#django.test.LiveServerTestCase

To run the test suite under coverage:

    $ coverage run manage.py test

to execute the tests. Then to view the coverage report:

    $ coverage report

See the `coverage.py`_ docs for more info and options.

.. _coverage.py: http://nedbatchelder.com/code/coverage/

You can also run unit tests of the JavaScript used by the `thumbs` example.
See `thumbs/static/js/README.md` for details.

Style Testing
-------------

We use two tools - ``pylint`` and ``pep8`` - to manage the code quality and style
of all Python files in this repo. Our goal is to maintain zero reported pylint
and pep8 violations at all times.

To run these tools on a single file:

    $ pylint path/to/file.py

    $ pep8 path/to/file.py

To run these tools on the whole project:

    $ pylint .

    $ pep8 .

We do not abide by all pylint and pep8 violations. You can check out which violations
we ignore by viewing the contents of `pylintrc`_ and `.pep8`_. Before making a pull
request, you should ensure that your branch does not add any new quality violations
by checking your code with these tools.

Using the workbench
-------------------

When you open the workbench, you'll see a list of sample XBlock configurations
(scenarios).  Each will display a page showing the XBlocks composited together,
along with internal information like the "database" contents.

The workbench doesn't use a real database, it simply stores all data in an
in-memory dictionary.  The data is all lost and reset when you restart the
server.

If you want to experiment with different students, you can use a URL parameter
to set the student ID, which defaults to 1:

    http://127.0.0.1:8000/?student_id=17

Different students will see different student state, for example, while seeing
the same content.  Student ids are strings, even if they contain only digits
as the default does.


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

License
-------

The code in this repository is licensed under version 3 of the AGPL unless
otherwise noted.

Please see ``LICENSE.txt`` for details.

How to Contribute
-----------------

Contributions are very welcome. The easiest way is to fork this repo, and then
make a pull request from your fork. The first time you make a pull request, you
may be asked to sign a Contributor Agreement.

Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@edx.org

Mailing List and IRC Channel
----------------------------

You can discuss this code on the `edx-xblock Google Group`__ or in the
``edx-code`` IRC channel on Freenode.

__ https://groups.google.com/forum/#!forum/edx-xblock
