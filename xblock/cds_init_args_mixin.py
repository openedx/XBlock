"""
Minimal mixin for Split Mongo: pops ``cds_init_args`` and exposes ``get_cds_init_args``.

``XModuleMixin`` does the same; use this when ``XModuleMixin`` is omitted from the
runtime mixin list so ``construct_xblock_from_class(..., cds_init_args=...)`` still works.
"""


class CdsInitArgsMixin:
    """
    Initialization data used by SplitModuleStoreRuntime to defer FieldData initialization.

    Mirrors the ``cds_init_args`` handling in ``xmodule.x_module.XModuleMixin`` without
    pulling in the rest of XModule behavior.
    """

    def __init__(self, *args, **kwargs):
        self._cds_init_args = kwargs.pop("cds_init_args", None)
        super().__init__(*args, **kwargs)

    def get_cds_init_args(self):
        """Get initialization data used by SplitModuleStoreRuntime to defer FieldData initialization."""
        if self._cds_init_args is None:
            raise KeyError("cds_init_args was not provided for this XBlock")
        if self._cds_init_args is False:
            raise RuntimeError("Tried to get SplitModuleStoreRuntime cds_init_args twice for the same XBlock.")
        args = self._cds_init_args
        self._cds_init_args = False
        return args
