"""
XBlock Courseware Components
"""

# For backwards compatibility, provide the XBlockMixin in xblock.fields
# without causing a circular import
import codecs
import os
import warnings

import xblock.core
import xblock.fields


class XBlockMixin(xblock.core.XBlockMixin):
    """
    A wrapper around xblock.core.XBlockMixin that provides backwards compatibility for the old location.

    Deprecated.
    """
    def __init__(self, *args, **kwargs):
        warnings.warn("Please use xblock.core.XBlockMixin", DeprecationWarning, stacklevel=2)
        super(XBlockMixin, self).__init__(*args, **kwargs)


# For backwards compatibility, provide the XBlockMixin in xblock.fields
# without causing a circular import
xblock.fields.XBlockMixin = XBlockMixin

VERSION_FILE = os.path.join(os.path.dirname(__file__), 'VERSION.txt')

with codecs.open(VERSION_FILE, encoding='ascii') as f:
    __version__ = f.read().strip()
