Part of `edX code`__.

__ http://code.edx.org/

XBlock Courseware Components |build-status| |coverage-status|
=============================================================

XBlock is a component architecture by edX.org for building courseware.

This is a pre-alpha release of the XBlock API, to gather input from potential
users of the API.  We like what is here, but are open to suggestions for
changes. We will be implementing this shortly in the edX LMS.

This repo contains the core code for implementing XBlocks.


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

This code runs on Python 2.7. If you prefer to use Python 3, there is `a fork
of XBlock that provides Python 3 support`_, but this fork is not yet supported
by edX.

1.  Get a local copy of this repo.

2.  (Optional)  Create and activate a virtualenv to work in.

3.  Install the requirements and register the XBlock entry points with (you may
    need to sudo this if you don't use virtualenv):

        $ pip install -r requirements.txt

.. _a fork of XBlock that provides Python 3 support: https://github.com/singingwolfboy/XBlock/tree/py3


Testing
--------

To run the test suite:

    $ nosetests

This will run:

    * Unit tests of the XBlock core and runtime.

To run the test suite under coverage:

    $ coverage run -m nose

to execute the tests. Then to view the coverage report:

    $ coverage report

See the `coverage.py`_ docs for more info and options.

.. _coverage.py: http://nedbatchelder.com/code/coverage/


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
we ignore by viewing the contents of `pylintrc`_ and `setup.cfg`_. Before making a pull
request, you should ensure that your branch does not add any new quality violations
by checking your code with these tools.

.. _pylintrc: https://github.com/edx/XBlock/blob/master/pylintrc
.. _setup.cfg: https://github.com/edx/XBlock/blob/master/setup.cfg

You can run these tests automatically before pushing code to github (and running
the validation in Travis) by activating the `pre-push` script

    cd .git/hooks
    ln -s ../../script/pre-push
    cd -


Using the XBlock-SDK
-------------------

The XBlock-SDK exists in a separate repository. The SDK contains useful tools for
developing your own XBlocks, such as a template XBlock generator, sample XBlocks
that demonstrate XBlock functionality.

You can find it in its own repository: https://github.com/edx/xblock-sdk


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


Making your own XBlock
----------------------

Making an XBlock can be as simple as creating a Python class with a few
specific methods.

Instructions for constructing a new XBlock along with examples can be found in
the XBlock SDK: https://github.com/edx/xblock-sdk


License
-------

The code in this repository is licensed the Apache 2.0 license unless otherwise
noted.

Please see ``LICENSE.txt`` for details.


How to Contribute
-----------------

Contributions are very welcome. The easiest way is to fork this repo, and then
make a pull request from your fork. The first time you make a pull request, you
may be asked to sign a Contributor Agreement.

Please refer to our `contributor guidelines <https://github.com/edx/edx-platform/
blob/master/CONTRIBUTING.rst>`_ in the main edx-platform repo for
important additional information.


Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@edx.org

Packaging
---------

To package a new release:

#. Update the version number in setup.py and xblock/__init__.py.

#. Tag the commit to be released::

    $VERSION=0.5
    git tag -a -m "XBlock version $VERSION" xblock-$VERSION

#. Upload to PyPI::

    make package


Mailing List and IRC Channel
----------------------------

You can discuss this code on the `edx-code Google Group`__ or in the
``#edx-code`` IRC channel on Freenode.

__ https://groups.google.com/group/edx-code

.. |build-status| image:: https://travis-ci.org/edx/XBlock.svg?branch=master
   :target: https://travis-ci.org/edx/XBlock
.. |coverage-status| image:: https://coveralls.io/repos/edx/XBlock/badge.svg
   :target: https://coveralls.io/r/edx/XBlock
