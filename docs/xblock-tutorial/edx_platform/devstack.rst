.. _Deploy Your XBlock in Devstack:

###############################
Deploy Your XBlock in Devstack
###############################

This section provides instructions for deploying your XBlock in devstack.

.. contents::
 :local:
 :depth: 1

For more information about devstack, see the `Installing,
Configuring, and Running the Open edX Platform`_.

*******************
Prerequisites
*******************

Before proceeding with the steps to deploy your XBlock, ensure the following
requirements are met.

* Devstack is running. For instructions, see the `devstack`_ repository.

* Ensure you have the XBlock directory in a location you can access from the
  devstack containers (e.g. `edx-platform/src/``).

*********************
Installing the XBlock
*********************

The following instructions will help you install a XBlock on your OpenEdX
devstack. Since LMS and Studio run on separate Docker containers, you will need
to install the XBlock to the virtual environments of both containers.

.. note::
  These steps consider you're running the Docker based Devstack provisioned at
  ``~/devstack_workspace/``.


#. From your devstack folder (``~/devstack_workspace/devstack``), enter the LMS container shell:

   .. code-block:: bash

      $ make lms-shell

#. Install the XBlock on ``edx-platform`` virtual enviroment:

   .. code-block:: bash

      root@7beb9df53150:/edx/app/edxapp/edx-platform# pip install path/to/xblock

#. Use ``C-d`` to exit the LMS shell and enter Studio shell with:

   .. code-block:: bash

      $ make studio-shell

#. Install the XBlock in the same way you've installed it on LMS:

   .. code-block:: bash

      root@7beb9df53150:/edx/app/edxapp/edx-platform# pip install path/to/xblock

#. To make sure the XBlock is available, you will need to restart both LMS and Studio:

   .. code-block:: bash

      $ make lms-restart && make studio-restart


After this, you'll be able to enable and add the XBlock to your course.

********************************
Enable the XBlock in Your Course
********************************

To use a XBlock, you must enable it in each course in which you intend to use it.

#.  Log in to Studio.

#.  Open the course.

#. From the **Settings** menu, select **Advanced Settings**.

#. In the **Advanced Module List** field, place your cursor between the braces,
   and then type the exact name of the XBlock.

   .. note::
     The name you enter must match exactly the name specified in your XBlock's
     ``setup.py`` file.

   If you see other values in the **Advanced Module List** field, add a comma
   after the closing quotation mark for the last value, and then type the name
   of your XBlock.

#. At the bottom of the page, select **Save Changes**.

****************************************
Add an Instance of the XBlock to a Unit
****************************************

You can add instances of the XBlock in any unit in the course.

On the unit page, under **Add New Component**, select **Advanced**.

Your XBlock is listed as one of the types you can add.

.. add image

Select the name of your XBlock to add an instance to the unit.

.. add image

You can then edit the properties of the instance as needed by selecting the
**Edit** button.

.. add image

For more information about working with components in Studio, see
`Developing Course Components`_ in the *Building and
Running an Open edX* guide.

.. include:: ../../links.rst
