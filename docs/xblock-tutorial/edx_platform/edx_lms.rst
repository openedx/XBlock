.. _EdX Learning Management System as an XBlock Runtime:

####################################################
EdX Learning Management System as an XBlock Runtime
####################################################

The edX Learning Management System (LMS) is the application in the edX Platform
that learners use to view and interact with courseware.

Because it presents XBlocks to learners and records their interactions, the LMS
is also an :ref:`XBlock runtime <XBlock Runtimes>` application.

As an XBlock developer, you must understand what XBlock properties the LMS
requires.

.. contents::
   :depth: 1
   :local:

*****************************
LMS Requirements for XBlocks
*****************************

The LMS requires XBlocks to have the following properties.

* A :ref:`view method <View Methods>` named ``student_view``. This is the view that renders
  the XBlock in the LMS for learners to see and interact with.

  In addition, the ``student_view`` method is used to render the XBlock in the
  Studio preview mode, unless the XBlock also has an ``author_view`` method.
  For more information, see :ref:`EdX Studio as an XBlock Runtime`.

* A class property named ``has_score`` with a value of ``True`` if the XBlock
  is to be graded.

.. * A method named ``get_progress`` that . . . TBD (  x_module.py:XModuleMixin.get_progress)

* A class property named ``icon_class``, which controls the icon that displays
  to learners in the unit navigation bar on the **Course** page when the XBlock
  is in that unit. The variable must have one of the following values.

  .. list-table::
     :header-rows: 1

     * - Value
       - Icon
     * - ``problem``
       - .. image:: ../Images/icon_class_problem.png
            :alt: The icon for an assessment of any type.
     * - ``video``
       - .. image:: ../Images/icon_class_video.png
            :alt: The icon for a video.
     * - ``other``
       - .. image:: ../Images/icon_class_other.png
            :alt: The icon for any other type of course content.

****************************
Internationalization Support
****************************

The LMS is currently capable of supporting internationalization (i18n) and localization (l10n) of static UI text
included in your XBlock -- also known as "chrome" or "labels".  Translation of user-generated content stored as XBlock
state is not currently supported.

To present XBlock language translations in the LMS you must include the translated strings for your chosen "locale"
in the GNU Gettext Portable Object file format.  Translated strings must be stored in a "domain" file named "text.po".

* locale:  A set of parameters that defines the user's language, region and any special variant preferences that the
  user wants to see in their user interface
* domain:  A Gettext application representing the set of translated strings corresponding to a particular locale.

Each "text.po" domain file consists of one or more string/translation pairs for the language/locale.  Further, each
translation pair consists of two fields: "msgid" for the base string, and "msgstr" for its corresponding translation.

There is no limit on the number of locales/domains that can be included with your XBlock.  However, your specific Open
edX installation may not be configured to support every locale that you provide.

You can learn more about the GNU Gettext Portable Object file format and download the GNU Gettext software using the
following resources:

* https://www.gnu.org/software/gettext/
* https://en.wikipedia.org/wiki/Gettext
* https://www.drupal.org/node/1814954

In addition to GNU Gettext, it is also possible to utilize the Open edX "i18n-tools" GNU Gettext wrapper to work with
your XBlock locales and domains.  You will need to modify the i18n-tools YAML configuration file to work with your
XBlock project.  More information about the i18n-tools project and its configuration file can be found at:

* https://github.com/openedx/i18n-tools
* https://github.com/openedx/i18n-tools/blob/master/conf/locale/config.yaml

Adding Translated Strings to your XBlock
****************************************

#. Create a directory within your XBlock code project named "translations".  This directory should be located at the
   same level in your code project as your XBlock implementation file.  For example:

   * ``http://github.com/my_org/my_xblock/my_xblock/my_xblock.py``
   * ``http://github.com/my_org/my_xblock/my_xblock/translations/``

#. Create a set of language directories for each of your locales within this new "translations" directory.  You may
   specify either a general language code or a specific language locale code for the name of each directory.  Include
   an "LC_MESSAGES" directory with each language directory.

   * ``../my_xblock/translations/ar/LC_MESSAGES/``
   * ``../my_xblock/translations/es-es/LC_MESSAGES/``

#. Create a domain file named "text.po".  You can use the Gettext ``xgettext`` command directly, or another tool
   of your choosing, such as Django's ``makemessages`` utility, or i18n-tools.  For more information on how to use
   these tools, see the following resources.

   * Gettext: https://www.gnu.org/software/gettext/manual/gettext.html
   * Gettext: http://phptal.org/manual/en/split/gettext.html
   * Django: https://docs.djangoproject.com/en/dev/topics/i18n/translation/#localization-how-to-create-language-files
   * i18n-tools: https://github.com/openedx/i18n-tools

#. Repeat the domain file creation process for each language/locale you support.

   In the following example, we will use the i18n-tools utilites to generate a "text.po" file.

   #. Create an alternative configuration file containing the details for your particular XBlock project
   #. Run ``i18n_tool extract`` to automatically find strings and populate the PO file.
   #. Run ``i18n_tool generate`` to compile your human-readable PO file to a machine-readable "MO" binary file
   #. Repeat the extraction/generation process for as many languages/locales as you require for your XBlock
   #. Add all of your translation directories and PO/MO files to your XBlock code project for distribution

#. Open each "text.po" domain file and, for each "msgid" string, add a corresponding "msgstr" translation.  PO files
   can be edited by hand, with a tool such as Pedit or Emacs, or through a third party service such as Transifex.

#. Place each locale's "text.po" domain file within the corresponding "LC_MESSAGES" directory.

   * ``../my_xblock/translations/ar/LC_MESSAGES/text.po``
   * ``../my_xblock/translations/es-es/LC_MESSAGES/text.po``

#. Compile your "text.po" files into binary "text.mo" files using the Gettext ``msgfmt`` command (or via the tool of
   your choice), and include these "text.mo" files alongside your "text.po" files in your code project.

   * ``../my_xblock/translations/ar/LC_MESSAGES/text.mo``
   * ``../my_xblock/translations/ar/LC_MESSAGES/text.po``

The resulting directory/file structure should look like this.

.. code-block:: text

    /my_xblock
    ├── my_xblock.py
    └── translations
        ├── ar
        |   └── LC_MESSAGES
        |       ├── text.mo
        |       └── text.po
        ├── es-es
        |   └── LC_MESSAGES
        |       ├── text.mo
        |       └── text.po
        ├── ru
        |   └── LC_MESSAGES
        |       ├── text.mo
        |       └── text.po
        └── zh-cn
            └── LC_MESSAGES
                ├── text.mo
                └── text.po

You can now run the LMS and update your preferred language via Account Settings
in order to observe the translated strings for your chosen locale.

.. note:: In the absence of an available language locale and domain file, the
    LMS XBlock runtime will attempt to match strings marked for translation
    within your XBlock using its own set of language locales and domains.
    However, it is not recommended that you rely on the LMS mechanism for
    internationalization support.  There is no guarantee your strings will be
    matched by the LMS, and even if matches are found, the translations may be
    incorrect in the context of your specific XBlock.

.. include:: ../../links.rst
