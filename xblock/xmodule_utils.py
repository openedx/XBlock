"""
Minimal mixin for Split Mongo: pops ``cds_init_args`` and exposes ``get_cds_init_args``.

``XModuleMixin`` does the same; use this when ``XModuleMixin`` is omitted from the
runtime mixin list so ``construct_xblock_from_class(..., cds_init_args=...)`` still works.
"""


class PlaceholderXModuleMixin:
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

    @property
    def course_id(self):
        """
        Return the key of the block to which this Course belongs.

        New code should always used `context_key`, which is the key of the Learning Context to which
        this block belongs. "Learning Context" is a generalized notion of Courses which is inclusive
        of Content Libraries, et al.
        """
        return self.context_key

    @property
    def category(self):
        """
        Return the block type, formerly known as "category".

        Preferred forms for new code: `self.usage_key.block_type` or `self.scope_ids.blocks_type`
        """
        return self.scope_ids.block_type

    @property
    def location(self):
        """
        Return the usage key identifying this block instance, formerly called the "location".

        `self.usage_key` is always preferred in new code.
        """
        return self.usage_key

    @location.setter
    def location(self, value):
        from opaque_keys.edx.keys import UsageKey
        assert isinstance(value, UsageKey)
        self.scope_ids = self.scope_ids._replace(
            def_id=value,  # Note: assigning a UsageKey as def_id is OK in old mongo / import system but wrong in split
            usage_id=value,
        )

    @property
    def url_name(self):
        """
        Return the URL-friendly name for this block.

        Preferred forms for new code: `self.usage_key.block_id`
        """
        return self.usage_key.block_id
