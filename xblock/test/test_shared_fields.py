"""
Tests for classes using Shared Field.
"""

from mock import Mock
import unittest

from xblock.test.tools import TestRuntime


from xblock.core import XBlock
from xblock.fields import RemoteScope, Field, ScopeIds, List
from xblock.query import Query, Queryable
from xblock.field_data import DictFieldData, SplitFieldData


class TestSharedFields(unittest.TestCase):

	def setUp(self):
		self.help_message = 'This is a help message'

		class TestBlock(XBlock):
			test_field = List(help = self.help_message, default = [])

		self.runtime = TestRuntime(services={'field-data': SplitFieldData({})})
		self.test_block = TestBlock(self.runtime, scope_ids=Mock(spec=ScopeIds))
		self.test_field = self.test_block.fields['test_field']

	def test_named_scopes_len(self):
	 	self.assertEqual(3, len(RemoteScope.named_scopes()))

	def test_access_field_attributes(self):
		test_query = self.test_field.Query(self.test_block)

		self.assertEqual(self.help_message, test_query.field.help)
		self.assertEqual(self.test_field.help, test_query.field.help)

	def test_access_queryable(self):
	 	test_query = self.test_field.Query(self.test_block)
	 	self.assertTrue(isinstance(test_query, Queryable))

	def test_access_queryable_xblock(self):
	 	test_query = self.test_field.Query(self.test_block)
	 	test_xblock = test_query.xblock

	 	self.assertTrue(isinstance(test_xblock, XBlock))

	def test_access_query_name(self):
		test_query = self.test_field.Query(self.test_block)

		self.assertEqual(test_query.name, self.test_field.name)




