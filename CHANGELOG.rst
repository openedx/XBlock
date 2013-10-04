----------
Change history for XBlock
----------

These are notable changes in XBlock.  This is a rolling list of changes,
in roughly chronological order, most recent first.  Add your entries at
or near the top.  Include a label indicating the component affected.

0.3
----------
* Make context an optional parameter for all views.

* Add shortcut method to make rendering an xblock's view with it's own
  runtime easier.

* Change the user field of Scopes to be three valued, rather than two.
  False is now UserScope.NONE, True is UserScope.ONE, and UserScope.ALL is new,
  and represents data that is computed based on input from many users.

* Rename ModelData to FieldData

* Rename ModelType to Field

* Split xblock.core into a number of smaller modules:
  xblock.core: Defines XBlock
  xblock.fields: Defines ModelType and subclasses, ModelData, and metaclasses
                 for classes with fields
  xblock.namespaces: Code for XBlock Namespaces only
  xblock.exceptions: Exceptions used by all parts of the xblock project

* Changed the interface for `Runtime` and `ModelData` so that they function
  as single objects that manage large numbers of `XBlocks`. Any method that
  operates on a block now takes that block as the first argument. Blocks, in
  turn, are responsible for storing the key values used by their field scopes.

* Changed the interface for `model_data` objects passed to `XBlocks` from
  dict-like to the being cache-like (as was already used by `KeyValueStore`).
  This removes the need to support methods like iteration and length, which
  makes it easier to write new `ModelDatas`. Also added an actual `ModelData`
  base class to serve as the expected interface.