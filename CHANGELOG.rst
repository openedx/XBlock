----------
Change history for XBlock
----------

These are notable changes in XBlock.  This is a rolling list of changes,
in roughly chronological order, most recent first.  Add your entries at
or near the top.  Include a label indicating the component affected.

0.3
----------

* Changed the interface for `model_data` objects passed to `XBlocks` from
  dict-like to the being cache-like (as was already used by `KeyValueStore`).
  This removes the need to support methods like iteration and length, which
  makes it easier to write new `ModelDatas`. Also added an actual `ModelData`
  base class to serve as the expected interface.