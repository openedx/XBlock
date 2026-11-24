"""
``{% load xblock_i18n %}``: ``trans`` and ``blocktrans`` that translate through the XBlock i18n service.

The tags look for the service under the ``_i18n_service`` key of the template context; put it there
when rendering, for example ``render_to_string(name, {**context, "_i18n_service": service})``.
See ``xblock.utils.templatetags.i18n``, which this exposes under a name Django's engine can load.
"""

from xblock.utils.templatetags.i18n import register  # pylint: disable=unused-import
