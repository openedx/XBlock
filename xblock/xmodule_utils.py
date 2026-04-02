"""
Minimal mixin for Split Mongo: pops ``cds_init_args`` and exposes ``get_cds_init_args``.

``XModuleMixin`` does the same; use this when ``XModuleMixin`` is omitted from the
runtime mixin list so ``construct_xblock_from_class(..., cds_init_args=...)`` still works.
"""


from xblock.fields import Scope, UserScope


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

    # has_score = False

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

    def get_icon_class(self):
        """
        Return a css class identifying this module in the context of an icon
        """
        return 'other'
        # return self.icon_class

    @property
    def display_name_with_default(self):
        """
        Return a display name for the module: use display_name if defined in
        metadata, otherwise convert the url name.
        """
        return (
            self.display_name if self.display_name is not None
            else self.usage_key.block_id.replace('_', ' ')
        )

    def bind_for_student(self, user_id, wrappers=None):
        """
        Set up this XBlock to act as an XModule instead of an XModuleDescriptor.

        Arguments:
            user_id: The user_id to set in scope_ids
            wrappers: These are a list functions that put a wrapper, such as
                      LmsFieldData or OverrideFieldData, around the field_data.
                      Note that the functions will be applied in the order in
                      which they're listed. So [f1, f2] -> f2(f1(field_data))
        """

        # Skip rebinding if we're already bound a user, and it's this user.
        if self.scope_ids.user_id is not None and user_id == self.scope_ids.user_id:
            if getattr(self.runtime, "position", None):
                self.position = self.runtime.position  # update the position of the tab
            return

        # If we are switching users mid-request, save the data from the old user.
        self.save()

        # Update scope_ids to point to the new user.
        self.scope_ids = self.scope_ids._replace(user_id=user_id)

        # Clear out any cached instantiated children.
        self.clear_child_cache()

        # Clear out any cached field data scoped to the old user.
        for field in self.fields.values():
            if field.scope in (Scope.parent, Scope.children):
                continue

            if field.scope.user == UserScope.ONE:
                field._del_cached_value(self)  # pylint: disable=protected-access
                # not the most elegant way of doing this, but if we're removing
                # a field from the module's field_data_cache, we should also
                # remove it from its _dirty_fields
                if field in self._dirty_fields:
                    del self._dirty_fields[field]

        if wrappers:
            # Put user-specific wrappers around the field-data service for this block.
            # Note that these are different from modulestore.xblock_field_data_wrappers, which are not user-specific.
            wrapped_field_data = self.runtime.service(self, "field-data-unbound")
            for wrapper in wrappers:
                wrapped_field_data = wrapper(wrapped_field_data)
            self._bound_field_data = wrapped_field_data
            if getattr(self.runtime, "uses_deprecated_field_data", False):
                # This approach is deprecated but OldModuleStoreRuntime still requires it.
                # For SplitModuleStoreRuntime, don't set ._field_data this way.
                self._field_data = wrapped_field_data

    def get_required_block_descriptors(self):
        """
        Return a list of XBlock instances upon which this block depends but are
        not children of this block.

        TODO: Move this method directly to the ConditionalBlock.
        """
        return []
