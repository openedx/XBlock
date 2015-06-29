"""
Tests for classes using Shared Field.
"""

from mock import Mock
import unittest

from xblock.test.tools import TestRuntime


from xblock.core import XBlock
from xblock.fields import RemoteScope, Field, ScopeIds, List
from xblock.query import Query, Queryable
from xblock.field_data import DictFieldData


class TestRemoteScope(unittest.TestCase):

	def setUp(self):
		self.help_message = 'This is a help message'

		class TestBlock(XBlock):
			test_field = List(help = self.help_message, default = [])

		self.runtime = TestRuntime(services={'field-data': DictFieldData({})})
		self.test_block = TestBlock(self.runtime, scope_ids=Mock(spec=ScopeIds))
		self.test_field = TestBlock.fields['test_field']


	def test_named_scopes_len(self):
	 	self.assertEqual(3, len(RemoteScope.named_scopes()))

	def test_access_field_attributes(self):
		test_query = self.test_field.Query()

		self.assertEqual(self.help_message, test_query.field.help)
		self.assertEqual(self.test_field.help, test_query.field.help)

	def test_access_queryable(self):
	 	test_query = self.test_field.Query()
	 	test_queryable = test_query

	 	print type(test_queryable)

	 	self.assertTrue(isinstance(test_queryable, Queryable))
