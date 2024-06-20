.. _Install XBlock Prerequisites:

############################
Install XBlock Prerequisites
############################

To build an XBlock, you must have the following tools on your computer.

.. contents::
 :local:
 :depth: 1


***********
Python 3.11
***********

To run the a virtual environment and the XBlock SDK, and to build an XBlock,
you must have Python 3.11 installed on your computer.

`Download Python`_ for your operating system and follow the installation
instructions.

***
Git
***

Open edX repositories, including XBlock and the XBlock SDK, are stored on GitHub.

To build your own XBlock, and to deploy it later, you must use Git for source
control.

If you do not have Git installed, or you are are unfamiliar with the tool, see
the `GitHub Help`_.

*********************
A Virtual Environment
*********************

It is recommended that you develop your XBlock using a Python virtual
environment. A virtual environment is a tool to keep the dependencies required
by different projects in separate places.

With a virtual environment you can manage the requirements of your XBlock in a
separate location so they do not conflict with requirements of other Python
applications you might need.

The instructions and examples in this tutorial use `VirtualEnv`_ and
`VirtualEnvWrapper`_ to build XBlocks. You can also use `PyEnv`_.

After you have installed Python 3.11, follow the `VirtualEnv Installation`_
instructions.

For information on creating the virtual environment for your XBlock, see
:ref:`Create and Activate the Virtual Environment`.

.. include:: ../../links.rst
