"""
XBlock Courseware Components
"""

# For backwards compatability, provide the XBlockMixin in xblock.fields
# without causing a circular import
import warnings
import xblock.core
import xblock.fields


class XBlockMixin(xblock.core.XBlockMixin):
    def __init__(self, *args, **kwargs):
        warnings.warn("Please use xblock.core.XBlockMixin", DeprecationWarning, stacklevel=2)
        super(XBlockMixin, self).__init__(*args, **kwargs)


xblock.fields.XBlockMixin = XBlockMixin
