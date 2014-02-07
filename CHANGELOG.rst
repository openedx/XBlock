=========================
Change history for XBlock
=========================

These are notable changes in XBlock.

0.4 - In Progress
-----------------

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
