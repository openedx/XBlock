.. _settings-and-theme-support:


Settings and theme support
##########################

.. _accessing-xblock-specific-settings:

Accessing XBlock specific settings
**********************************

XBlock utils provide a mixin to simplify accessing instance-wide
XBlock-specific configuration settings: ``XBlockWithSettingsMixin``.
This mixin aims to provide a common interface for pulling XBlock
settings from the LMS
`SettingsService <https://github.com/edx/edx-platform/blob/master/common/lib/xmodule/xmodule/services.py>`__.

``SettingsService`` allows individual XBlocks to access environment and
django settings in an isolated manner:

-  XBlock settings are represented as dictionary stored in `django
   settings <https://github.com/edx/edx-platform/blob/master/cms/envs/aws.py#L341-342>`__
   and populated from environment \*.json files (cms.env.json and
   lms.env.json)
-  Each XBlock is associated with a particular key in that dictionary:
   by default an XBlock's class name is used, but XBlocks can override
   it using the ``block_settings_key`` attribute/property.

Please note that at the time of writing the implementation of
``SettingsService`` assumed "good citizenship" behavior on the part of
XBlocks, i.e. it does not check for key collisions and allows modifying
mutable settings. Both ``SettingsService`` and
``XBlockWithSettingsMixin`` are not concerned with contents of settings
bucket and return them as is. Refer to the ``SettingsService`` docstring
and implementation for more details.

Using XBlockWithSettingsMixin
=============================

In order to use ``SettingsService`` and ``XBlockWithSettingsMixin``, a
client XBlock *must* require it via standard
``XBlock.wants('settings')`` or ``XBlock.needs('settings')`` decorators.
The mixins themselves are not decorated as this would not result in all
descendant XBlocks to also be decorated.

With ``XBlockWithSettingsMixin`` and ``wants`` decorator applied,
obtaining XBlock settings is as simple as

.. code:: python

   self.get_xblock_settings()  # returns settings bucket or None
   self.get_xblock_settings(default=something)  # returns settings bucket or "something"

In case of missing or inaccessible XBlock settings (i.e. no settings
service in runtime, no ``XBLOCK_SETTINGS`` in settings, or XBlock
settings key is not found) ``default`` value is used.

.. _theming-support:

Theming support
***************

XBlock theming support is built on top of XBlock-specific settings.
XBlock utils provide ``ThemableXBlockMixin`` to streamline using XBlock
themes.

XBlock theme support is designed with two major design goals:

-  Allow for a different look and feel of an XBlock in different
   environments.
-  Use a pluggable approach to hosting themes, so that adding a new
   theme will not require forking an XBlock.

The first goal made using ``SettingsService`` and
``XBlockWithSettingsMixin`` an obvious choice to store and obtain theme
configuration. The second goal dictated the configuration format - it is
a dictionary (or dictionary-like object) with the following keys:

-  ``package`` - "top-level" selector specifying package which hosts
   theme files
-  ``locations`` - a list of locations within that package

Examples:

.. code:: python

   # will search for files red.css and small.css in my_xblock package
   {
       'package': 'my_xblock',
       'locations': ['red.css', 'small.css']
   }

   # will search for files public/themes/red.css in my_other_xblock.assets package
   default_theme_config = {
       'package': 'my_other_xblock.assets',
       'locations': ['public/themes/red.css']
   }

Theme files must be included into package (see `python
docs <https://docs.python.org/2/distutils/setupscript.html#installing-package-data>`__
for details). At the time of writing it is not possible to fetch theme
files from multiple packages.

**Note:** XBlock themes are *not* LMS themes - they are just additional
CSS files included into an XBlock fragment when the corresponding XBlock
is rendered. However, it is possible to misuse this feature to change
look and feel of the entire LMS, as contents of CSS files are not
checked and might contain selectors that apply to elements outside of
the XBlock in question. Hence, it is advised to scope all CSS rules
belonging to a theme with a global CSS selector
``.themed-xblock.<root xblock element class>``, e.g.
``.themed-xblock.poll-block``. Note that the ``themed-xblock`` class is
not automatically added by ``ThemableXBlockMixin``, so one needs to add
it manually.

Using ThemableXBlockMixin
=========================

In order to use ``ThemableXBlockMixin``, a descendant XBlock must also
be a descendant of ``XBlockWithSettingsMixin`` (``XBlock.wants``
decorator requirement applies) or provide a similar interface for
obtaining the XBlock settings bucket.

There are three configuration parameters that govern
``ThemableXBlockMixin`` behavior:

-  ``default_theme_config`` - default theme configuration in case no
   theme configuration can be obtained
-  ``theme_key`` - a key in XBlock settings bucket that stores theme
   configuration
-  ``block_settings_key`` - inherited from ``XBlockWithSettingsMixin``
   if used in conjunction with it

It is safe to omit ``default_theme_config`` or set it to ``None`` in
case no default theme is available. In this case,
``ThemableXBlockMixin`` will skip including theme files if no theme is
specified via settings.

``ThemableXBlockMixin`` exposes two methods:

-  ``get_theme()`` - this is used to get theme configuration. Default
   implementation uses ``get_xblock_settings`` and ``theme_key``,
   descendants are free to override it. Normally, it should not be
   called directly.
-  ``include_theme_files(fragment)`` - this method is an entry point to
   ``ThemableXBlockMixin`` functionality. It calls ``get_theme`` to
   obtain theme configuration, fetches theme files and includes them
   into fragment. ``fragment`` must be a
   `web_fragments.fragment <https://github.com/openedx/web-fragments/blob/master/web_fragments/fragment.py>`__
   instance.

So, having met usage requirements and set up theme configuration
parameters, including theme into XBlock fragment is a one liner:

.. code:: python

   self.include_theme_files(fragment)
