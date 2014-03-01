"""
Basic admin screens for displaying XBlock state and filtering/searching on the
fields.
"""
from django.contrib import admin
from .models import XBlockState


class XBlockStateAdmin(admin.ModelAdmin):
    """Basic admin operations for XBlockState model.

    This is primarily meant for viewing/filtering/searching, not for editing.
    You're only allowed to edit the state fields themselves, not the IDs or
    categories. Since things like `tag` and `scenario` are set on write, weird
    things could happen if you muck with them later on.
    """
    list_display = ['scope_id', 'scope', 'user_id', 'state']
    list_filter = ['scope', 'user_id', 'scenario', 'tag']
    search_fields = ['user_id', 'scope_id', 'state']
    readonly_fields = [
        'scope', 'scope_id', 'scenario', 'tag', 'user_id', 'created'
    ]

admin.site.register(XBlockState, XBlockStateAdmin)
