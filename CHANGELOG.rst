=========================
Change history for XBlock
=========================

Unreleased
----------

5.0.0 - 2024-05-30
------------------

* dropped python 3.8 support
* transitioned from deprecated pkg_resources lib to importlib.resources


4.1.0 - 2024-05-16
------------------

* optional streaming response support added to webob_to_django_response

4.0.1 - 2024-04-24
------------------

* unpin lxml constraint.

4.0.0 - 2024-04-18
------------------

* xblock.fragment has returned as a pass-though component to web_fragments.fragment


3.0.0 - 2024-03-18
------------------

Various extraneous classes have been removed from the XBlock API, simplifying its implementation
and making debugging of XBlock instances easier. We believe that most, if not all, XBlock API users
will be unaffected by this change. Some improvements have also been made to the reference documentation.

Specific changes:

* **Removed:**

  * ``xblock.XBlockMixin`` (still available as ``xblock.core.XBlockMixin``)
  * ``xblock.core.SharedBlockBase`` (replaced with ``xblock.core.Blocklike``)
  * ``xblock.internal.Nameable``
  * ``xblock.internal.NamedAttributesMetaclass``
  * ``xblock.django.request.HeadersDict``
  * ``xblock.fields.XBlockMixin`` (still available as ``xblock.core.XBlockMixin``)
  * ``xblock.mixins.RuntimeServicesMixin``
  * ``xblock.mixins.ScopedStorageMixin``
  * ``xblock.mixins.IndexInfoMixin``
  * ``xblock.mixins.XmlSerializationMixin``
  * ``xblock.mixins.HandlersMixin``
  * ``xblock.mixins.ChildrenModelMetaclass``
  * ``xblock.mixins.HierarchyMixin``
  * ``xblock.mixins.ViewsMixin``

* **Added:**

  * ``xblock.core.Blocklike``, the new common ancestor of ``XBlock`` and ``XBlockAside``, and ``XBlockMixin``,
    replacing ``xblock.core.SharedBlockBase``.

  * New attributes on ``xblock.core.XBlockAside``, each behaving the same as their ``XBlock`` counterpart:

    * ``usage_key``
    * ``context_key``
    * ``index_dictionary``

  * Various new attributes on ``xblock.core.XBlockMixin``, encompassing the functionality of these former classes:

    * ``xblock.mixins.IndexInfoMixin``
    * ``xblock.mixins.XmlSerializationMixin``
    * ``xblock.mixins.HandlersMixin``

* **Docs**

  * Various docstrings have been improved, some of which are published in the docs.
  * XBlockAside will now be represented in the API docs, right below XBlock on the "XBlock API" page.
  * XBlockMixin has been removed from the docs.
    It was only ever documented under the "Fields API" page (which didn't make any sense),
    and it was barely even documented there. We considered adding it back to the "XBlock API" page,
    but as noted in the class's new docstring, we do not want to encourage any new use of XBlockMixin.

2.0.0 - 2024-02-26
------------------

* Removed deprecations
* xblock.fragment (removed completely)
* xblock.runtime.Runtime._aside_from_xml (just the id_generator argument)
* xblock.runtime.Runtime._usage_id_from_node (just the id_generator argument)
* xblock.runtime.Runtime.add_node_as_child (just the id_generator argument)
* xblock.runtime.Runtime.parse_xml_string (just the id_generator argument)
* xblock.runtime.Runtime.parse_xml_file (just the id_generator argument)

1.10.0 - 2024-01-12
-------------------

* Add two new properties to ``XBlock`` objects: ``.usage_key`` and ``.context_key``.
  These simply expose the values of ``.scope_ids.usage_id`` and ``.scope_ids.usage_id.context_key``,
  providing a convenient replacement to the deprecated, edx-platform-specific block properties ``.location``
  and ``.course_id``, respectively.

1.9.1 - 2023-12-22
------------------

* Fix: add ``get_javascript_i18n_catalog_url`` missing ``xblock`` parameter to match the Open edX LMS
  XBlockI18nService.

1.9.0 - 2023-11-20
------------------

* Support for `OEP-58 JavaScript translations <https://docs.openedx.org/en/latest/developers/concepts/oep58.html>`_:

  * Introduced abstract JavaScript translations support by adding the ``i18n_js_namespace`` property and
    ``get_i18n_js_namespace`` method to the ``SharedBlockBase``. This allows XBlocks to define a JavaScript namespace
    so the XBlock i18n runtime service can manage and load JavaScript translations for XBlocks.

  * Added the stub ``get_javascript_i18n_catalog_url`` method to the ``NullI18nService`` class to be implemented
    by runtime services.

  * See the `edx-platform atlas translations proposal <https://github.com/openedx/edx-platform/blob/master/docs/decisions/0019-oep-58-atlas-translations-design.rst>`_

1.8.1 - 2023-10-07
------------------

* Python Requirements Update
* Update setup.py, adds required packages

1.8.0 - 2023-09-25
------------------
* Added `xblock-utils <https://github.com/openedx/xblock-utils>`_ repository code into this repository along with docs.

  * Docs moved into the docs/ directory.

  * See https://github.com/openedx/xblock-utils/issues/197 for more details.

1.7.0 - 2023-08-03
------------------

* Switch from ``edx-sphinx-theme`` to ``sphinx-book-theme`` since the former is
  deprecated.  See https://github.com/openedx/edx-sphinx-theme/issues/184 for
  more details.
* Added support for Django 4.2

1.6.1 - 2022-01-28
------------------

* Fix Release Issue with PyPi release workflow

1.6.0 - 2022-01-25
------------------

* Dropped Django22, 30 and 31 support
* Added Django40 Support in CI


1.5.1 - 2021-08-26
------------------

* Deprecated the Runtime.user_id property in favor of the user service.

1.5.0 - 2021-07-27
------------------

* Added Django 3.0, 3.1 & 3.2 support

1.4.2 - 2021-05-24
------------------

* Upgraded all Python dependencies.

1.4.1 - 2021-03-20
------------------

* Added XBlockParseException exception.

1.3.1 - 2020-05-06
------------------

* Fixed import error of mock.

1.3.0 - 2020-05-04
------------------

* Drop support to python 2.7 and add support to python 3.8.
  typing package failing on py3.8 so add constraint.

1.2.8 - 2019-10-24
------------------

* Ensure the version file is closed after reading its content.

1.2.7 - 2019-10-15
------------------

* Changed how illegal XML characters are sanitized, to speed the operation.
  The old way was removing more characters than are required by the XML
  specification.

1.2.6 - 2019-09-24
------------------

* Add support for relative dates to DateTime fields.

1.2.5 - 2019-09-19
------------------

* Changes for Python 2/3 compatibility.

1.2.4 - 2019-08-27
------------------

* Added an API for notifying the Runtime when an XBlock's ``save()`` method is
  called.

* Added a mechanism for Runtime subclasses to more easily add extra CSS classes
  to the ``<div>`` that wraps rendered XBlocks

1.2.3 - 2019-07-24
------------------

Allow Mixologist class to consume both class objects and string paths to classes as a part of initialization.

1.2.1 - 2018-09-05
------------------

Add a method to get completion mode for a block.

1.2.1 - 2018-06-25
------------------

Suppress a spurious warning when using lazily-translated text as the default
value of a String field.

1.2.0 - Aside filtering
-----------------------

* Add capability for XBlockAsides to apply only to XBlocks that match certain conditions

1.0 - Python 3
--------------

* Introduce Python 3 compatibility to the xblock code base.
  This does not enable Python 2 codebases (like edx-platform) to load xblocks
  written in Python 3, but it lays the groundwork for future migrations.

0.5 - ???
---------

No notes provided.

0.4
---

* Separate Fragment class out into new web-fragments package

* Make Scope enums (UserScope.* and BlockScope.*) into Sentinels, rather than just ints,
  so that they can have more meaningful string representations.

* Rename `export_xml` to `add_xml_to_node`, to more accurately capture the semantics.

* Allowed `Runtime` implementations to customize loading from **block_types** to
  `XBlock` classes.

0.3 - 2014-01-09
----------------

* Added services available through `Runtime.service`, once XBlocks have
  announced their desires with `@XBlock.needs` and `@XBlock.wants`.

* The "i18n" service provides a `gettext.Translations` object for retrieving
  localized strings.

* Make `context` an optional parameter for all views.

* Add shortcut method to make rendering an XBlock's view with its own
  runtime easier.

* Change the user field of scopes to be three valued, rather than two.  `False`
  becomes `UserScope.NONE`, `True` becomes `UserScope.ONE`, and `UserScope.ALL`
  is new, and represents data that is computed based on input from many users.

* Rename `ModelData` to `FieldData`.

* Rename `ModelType` to `Field`.

* Split xblock.core into a number of smaller modules:

  * xblock.core: Defines XBlock.

  * xblock.fields: Defines ModelType and subclasses, ModelData, and metaclasses
    for classes with fields.

  * xblock.namespaces: Code for XBlock Namespaces only.

  * xblock.exceptions: exceptions used by all parts of the XBlock project.

* Changed the interface for `Runtime` and `ModelData` so that they function
  as single objects that manage large numbers of `XBlocks`. Any method that
  operates on a block now takes that block as the first argument. Blocks, in
  turn, are responsible for storing the key values used by their field scopes.

* Changed the interface for `model_data` objects passed to `XBlocks` from
  dict-like to the being cache-like (as was already used by `KeyValueStore`).
  This removes the need to support methods like iteration and length, which
  makes it easier to write new `ModelDatas`. Also added an actual `ModelData`
  base class to serve as the expected interface.
