XBlock
######


|pypi-badge| |ci-badge| |codecov-badge| |doc-badge| |pyversions-badge|
|license-badge| |status-badge|

Purpose
*******

XBlock is the Open edX component architecture for building courseware.

This repo contains the core code for implementing XBlocks. Open edX courseware
is built out of components that are combined hierarchically. These include
components like the video player, `LON-CAPA`_ problems, as well as compound
components like learning sequences. The API for these components is called
XBlocks.

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

Getting Started
***************

Developing
==========

One Time Setup
--------------

First, clone the repository:

.. code-block:: bash

   git clone git@github.com:openedx/XBlock.git

Go to the XBlock directory, set up a virtual environment using ``virtualenvwrapper`` with
the same name as the repo and activate it:

.. code-block:: bash

   cd XBlock
   mkvirtualenv -p python3.11 XBlock

Every time you develop something in this repo
---------------------------------------------

.. code-block:: bash

  # Activate the virtualenv
  workon XBlock

  # Grab the latest code
  git checkout master
  git pull

  # Install/update the dev requirements
  make requirements

  # Run the tests and quality checks (to verify the status before you make any changes)
  make validate

  # Make a new branch for your changes
  git checkout -b <your_github_username>/<short_description>

  # Using your favorite editor, edit the code to make your change.
  vim ...

  # Run your new tests
  pytest ./path/to/new/tests

  # Run all the tests and quality checks
  make validate

  # Commit all your changes
  git commit ...
  git push

  # Open a PR and ask for review.

Deploying
---------

To package a new release:

#. Describe the release in `CHANGELOG.rst`_

#. Update the ``__version__`` number in `xblock/__init__.py`_

#. Use the github release mechanism to release a new version. This will tag and publish the package.

.. _CHANGELOG.rst: https://github.com/openedx/XBlock/blob/master/CHANGELOG.rst
.. _xblock/__init__.py: https://github.com/openedx/XBlock/blob/master/xblock/__init__.py

Using the XBlock-SDK
********************

The XBlock-SDK exists in a separate repository. The SDK contains useful tools for
developing your own XBlocks, such as a template XBlock generator, sample XBlocks
that demonstrate XBlock functionality.

You can find it in its own repository: https://github.com/openedx/xblock-sdk

Getting Help
************

Documentation
=============

The docs for the XBlock API is on Read The Docs: https://docs.openedx.org/projects/xblock/en/latest/xblock-tutorial/index.html .

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
the `XBlock SDK`_.

.. _XBlock SDK: https://github.com/openedx/xblock-sdk

More Help
=========

If you're having trouble, we have discussion forums at
https://discuss.openedx.org where you can connect with others in the
community.

Our real-time conversations are on Slack. You can request a `Slack
invitation`_, then join our `community Slack workspace`_.

For anything non-trivial, the best path is to open an issue in this
repository with as many details about the issue you are facing as you
can provide.

https://github.com/openedx/XBlock/issues

For more information about these options, see the `Getting Help`_ page.

.. _Slack invitation: https://openedx.org/slack
.. _community Slack workspace: https://openedx.slack.com/
.. _Getting Help: https://openedx.org/getting-help

License
*******

The code in this repository is licensed the Apache 2.0 license unless otherwise
noted.

Please see `LICENSE.txt`_ for details.

.. _LICENSE.txt: https://github.com/openedx/XBlock/blob/master/LICENSE.txt

Contributing
************

Contributions are very welcome!

Please read `How To Contribute <https://openedx.org/r/how-to-contribute>`_ for details.

This project is currently accepting all types of contributions, bug fixes,
security fixes, maintenance work, or new features.  However, please make sure
to have a discussion about your new feature idea with the maintainers prior to
beginning development to maximize the chances of your change being accepted.
You can start a conversation by creating a new issue on this repo summarizing
your idea.

The Open edX Code of Conduct
****************************

All community members are expected to follow the `Open edX Code of Conduct`_.

.. _Open edX Code of Conduct: https://openedx.org/code-of-conduct/

People
******

The assigned maintainers for this component and other project details may be
found in `Backstage`_. Backstage pulls this data from the ``catalog-info.yaml``
file in this repo.

.. _Backstage: https://backstage.openedx.org/catalog/default/component/xblock

Reporting Security Issues
*************************

Please do not report security issues in public. Please email security@openedx.org

.. |pypi-badge| image:: https://img.shields.io/pypi/v/XBlock.svg
    :target: https://pypi.python.org/pypi/XBlock/
    :alt: PyPI

.. |ci-badge| image:: https://github.com/openedx/XBlock/workflows/Python%20CI/badge.svg?branch=master
    :target: https://github.com/openedx/XBlock/actions
    :alt: CI

.. |codecov-badge| image:: https://codecov.io/github/openedx/XBlock/coverage.svg?branch=master
    :target: https://codecov.io/github/openedx/XBlock?branch=master
    :alt: Codecov

.. |doc-badge| image:: https://readthedocs.org/projects/XBlock/badge/?version=latest
    :target: https://docs.openedx.org/projects/xblock/en/latest/
    :alt: Documentation

.. |pyversions-badge| image:: https://img.shields.io/pypi/pyversions/XBlock.svg
    :target: https://docs.openedx.org/projects/xblock/en/latest/
    :alt: Supported Python versions

.. |license-badge| image:: https://img.shields.io/github/license/openedx/XBlock.svg
    :target: https://github.com/openedx/XBlock/blob/master/LICENSE.txt
    :alt: License

.. |status-badge| image:: https://img.shields.io/badge/Status-Maintained-brightgreen
    :alt: Repo is maintained.
