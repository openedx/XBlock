"""
Tests for classes using Shared Field.
"""

from mock import Mock
import unittest


from xblock.fields import RemoteScope, Field


class TestRemoteScope(unittest.TestCase):

	 def test_named_scopes_len(self):
	 	self.assertEqual(2, len(RemoteScope.named_scopes()))

	 def test_access_field_Attributes(self):
	 	help_message = 'This is a help message'
	 	test_field = Field(help = help_message)
	 	test_query = test_field.Query(test_field)

	 	self.assertEqual(help_message, test_query.field.help)
	 	self.assertEqual(test_field.help, test_query.field.help)