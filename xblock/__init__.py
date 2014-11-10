"""
XBlock Courseware Components
"""

# For backwards compatability, provide the XBlockMixin in xblock.fields
# without causing a circular import
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


xblock.fields.XBlockMixin = XBlockMixin

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
