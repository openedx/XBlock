"""
Test the case when a lazily-translated string is given as a default for
an XBlock String field.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# Set up Django settings
import os
from mock import Mock
from unittest import TestCase

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xblock.test.settings")

# pylint: disable=wrong-import-position
try:
    from django.utils.translation import ugettext_lazy as _  # pylint: disable=import-error
    HAS_DJANGO = True
except ImportError:
    HAS_DJANGO = False

# Django isn't always available, so skip tests if it isn't.
from nose.plugins.skip import SkipTest

from xblock import fields  # pylint: disable=unused-import
# pylint: enable=wrong-import-position

from xblock.core import XBlock, XBlockMixin
from xblock.fields import BlockScope, Scope, String, ScopeIds, List, UserScope, Integer
from xblock.runtime import (
    DictKeyValueStore,
    KvsFieldData,
)
from xblock.test.tools import assert_equals, TestRuntime


class TestXBlock(XBlock):
    """
    Set up a class that contains a single string field with a translated default.
    """
    STR_DEFAULT_ENG = 'ENG: String to be translated'
    str_field = String(scope=Scope.settings, default=_(STR_DEFAULT_ENG))

class TestXBlockStringFieldDefaultTranslation(TestCase):

    def setUp(self):
        from django.conf import settings
        try:
            if settings.is_defined('DEBUG'):
                pass
        except:
            raise SkipTest("Not running in Django context.")

    def test_db_model_keys(self):
        # Construct a runtime and an XBlock using it.
        key_store = DictKeyValueStore()
        field_data = KvsFieldData(key_store)
        runtime = TestRuntime(Mock(), services={'field-data': field_data})
        tester = runtime.construct_xblock_from_class(TestXBlock, ScopeIds('s0', 'TestXBlock', 'd0', 'u0'))
        # Check instantiated XBlock str_field value - ensure not translated.
        assert_equals(tester.str_field, tester.STR_DEFAULT_ENG)
        # Save XBlock - verify str_field *is* translated.
