******************
Create an XBlock
******************

You use the XBlock SDK to create skeleton files for an XBlock. To do this,
follow these steps at a command prompt.

#. Change to the ``xblock_development`` directory, which contains the ``venv`` and ``xblock-sdk`` subdirectories.

#. Run the following command to create the skeleton
   files for the XBlock.

   .. code-block:: none

      (venv) $ xblock-sdk/bin/workbench-make-xblock

   Instructions in the command window instruct you to determine a short name
   and a class name. Follow the guidelines in the command window to determine
   the names that you want to use.

   .. code-block:: none

      You will be prompted for two pieces of information:

      * Short name: a single word, all lower-case, for directory and file
        names. For a hologram 3-D XBlock, you might choose "holo3d".

      * Class name: a valid Python class name.  It's best if this ends with
        "XBlock", so for our hologram XBlock, you might choose
        "Hologram3dXBlock".

      Once you specify those two names, a directory is created in the
      ``xblock_development`` directory containing the new project.

      If you don't want to create the project here, or you enter a name
      incorrectly, type Ctrl-C to stop the creation script.  If you don't want
      the resulting project, delete the directory it created.

#. At the command prompt, enter the Short Name you selected for your XBlock.

   .. code-block:: none

      $ Short name: myxblock

#. At the command prompt, enter the Class name you selected for your XBlock.

   .. code-block:: none

      $ Class name: MyXBlock

The skeleton files for the XBlock are created in the ``myxblock`` directory.
For more information about the XBlock files, see
:ref:`Anatomy of an XBlock`.
