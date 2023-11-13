.. _Set Up the XBlock Software Development Kit:

###########################################
Set Up the XBlock Software Development Kit
###########################################

Before you continue, make sure that you are familiar with the subjects in the
:ref:`Install XBlock Prerequisites` section.

When you have installed all prerequisites, you are ready to set up the `XBlock
SDK`_ in a virtual environment. To do this, complete the following steps.

.. contents::
 :local:
 :depth: 1

********************************************
Create a Directory for XBlock Work
********************************************

It is recommended that you create a directory in which to store all your XBlock
work, including a virtual environment, the XBlock SDK, and the XBlocks you
develop.

#. At the command prompt, run the following command to create the directory.

   .. code-block:: bash

      $ mkdir xblock_development

#. Change directories to the ``xblock_development`` directory.

   .. code-block:: bash

      $ cd xblock_development

   The rest of your work will be from this directory.

.. _Create and Activate the Virtual Environment:

********************************************
Create and Activate the Virtual Environment
********************************************

You must have a virtual environment tool installed on your computer. For more information, see :ref:`Install XBlock Prerequisites`.

Then create the virtual environment in your ``xblock_development`` directory.

#. At the command prompt in ``xblock_development``, run the following
   command to create the virtual environment.

   .. code-block:: bash

      $ virtualenv venv

#. Run the following command to activate the virtual environment.

   .. code-block:: bash

      $ source venv/bin/activate

   When the virtual environment is activated, the command prompt shows the name
   of the virtual directory in parentheses.

   .. code-block:: none

      (venv) $

.. include:: ../reusable/clone_sdk.rst

When the requirements are installed, you are in the ``xblock_development`` directory, which contains the ``venv`` and ``xblock-sdk`` subdirectories. You can now :ref:`create your first XBlock <Create Your First XBlock>`.

.. include:: ../../links.rst
