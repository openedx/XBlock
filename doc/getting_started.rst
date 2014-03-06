===============
Getting Started
===============

Creating a new XBlock means creating an installable Python kit with a class
derived from :class:`.XBlock`.  That sounds complicated, but it isn't.


Prerequisites
-------------

You'll need some software installed in order to work with XBlock:

Python 2.7

    Chances are good that you already have Python 2.7 installed.  If you need
    to install it, you can get a kit from `python.org`__.   Do not install the
    highest version you find.  Python 3.x will not work.  You want Python 2.7.

.. __: http://python.org/download/

Pip

    Python's package manager is called pip, with its own `installation
    instructions`__.

.. __: http://www.pip-installer.org/en/latest/installing.html

Git

    Git manages code repositories.  Github has a good `introduction to setting
    up git`__ if you need one.

.. __: https://help.github.com/articles/set-up-git



Get the XBlock repository
-------------------------

.. highlight: console

The XBlock code is on Github.  Get the code by cloning the XBlock repo::

    $ git clone https://github.com/edx/XBlock.git

This will create the XBlock directory in your current directory.

In the XBlock directory, install its prerequisite Python packages::

    $ pip install -r requirements.txt


Create a new XBlock
-------------------

.. highlight: console

The simplest way to get started on a new XBlock is to use the
script/startnew.py script in the XBlock SDK repo: 

    https://github.com/edx/xblock-sdk

Make a directory for your
development work, outside the XBlock directory, let's call it ``~/edxwork``,
and run the startnew.py script from there::

    $ cd ~
    $ mkdir edxwork
    $ cd edxwork
    $ /path/to/xblock-sdk/script/startnew.py

The script will need two pieces of information, both related to the name of
your XBlock:  a short name that can be used for directory names, and a Python
class name.  You might choose "myxblock" for the short name and "MyXBlock" for
the class name.  We'll use those names in the rest of these instructions.  Your
files will be named using the actual name you gave.

When the script is done, you'll have a myxblock directory with a complete
working XBlock.  Of course, it's just the boilerplate for your XBlock, now you
have to start writing your code.

.. highlight: python

Most of your work will be in the myxblock/myxblock/myxblock.py file, which
contains the MyXBlock class.  There are "TO-DO" comments in the file indicating
where you should make changes::

    # TO-DO: change this view to display your data your own way.
    def student_view(self, context=None):
        etc...


Write your XBlock
-----------------

Now comes the hard part!  You'll modify myxblock.py and the other files in the
generated XBlock to make it do whatever it is you want your XBlock to do.

Define your fields
..................

The first step is to define your fields.  These are declarations of the data
your XBlock will store.  XBlock fields have a rich scoping mechanism that lets
you associate data with particular blocks and users.  See :ref:`guide_fields`
for more details.


Define your view
................

The view is a function that creates the HTML to display your block in a course.
It may be a simple rendering of your data, or you may have complex logic to
determine what to show.

Many XBlocks will need only a single view, called "student_view".

Your view includes not only HTML, but also whatever Javascript and CSS are
needed to support the HTML.


Define your handlers
....................

If your XBlock is interactive, you will likely need to receive events from the
Javascript.  A handler is a function bound to a URL.  You can use the URL in
your Javascript to communicate back to the server.

You can define as many handlers as you need, and name them whatever you like.


Write tests
...........

TBD


Test your XBlock
----------------

.. highlight: console

It's important to thoroughly test your XBlock to be sure that it does what you
want and that it works properly in the environments you need.

To run your XBlock another application, you'll install it.  Using pip, you can
install your XBlock so that your working tree (the code you are editing) is the
installed version.  The makes it easy to change the code and see the changes
running without a cumbersome edit-install-run cycle.

Use pip to install your block::

    $ cd ~/edxwork
    $ pip install -e myxblock

Testing with the workbench
..........................

The simplest test environment is the XBlock workbench. It can be found in the XBlock SDK:

    https://github.com/edx/xblock-sdk


Testing with the edX LMS
........................

See https://github.com/edx/edx-platform/blob/master/docs/en_us/developers/source/xblocks.rst#testing

Deploying your XBlock
---------------------

See https://github.com/edx/edx-platform/blob/master/docs/en_us/developers/source/xblocks.rst#deploying-your-xblock

Submitting your XBlock to edX
-----------------------------

If you would like your XBlock to be available on edx.org, please do the following:

- Upload your XBlock to a public Git repository on a reliable host.  We
  recommend Github_.
- Create a pull request against `edx-platform`_.  However, *do not include your
  XBlock code in this request*.  Instead, add a line to the 
  `requirements file`_, indicating which version of your XBlock you would like
  to use.  That line should be the only change in your pull request.
  Additionally, in your pull request description, please include a link to where
  the XBlock code is hosted.
- A developer at edX will see the pull request and review your XBlock to ensure
  that it can integrate safely with the rest of edx-platform.
- To expedite the review process, please include, in the pull request, a
  thorough description of what your XBlock does, so that we can find the best
  person to review your code.

.. _Github: http://www.github.com/
.. _`edx-platform`: https://github.com/edx/edx-platform
.. _requirements file: https://github.com/edx/edx-platform/blob/master/requirements/edx/github.txt
