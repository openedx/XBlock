"""
Tests for classes using Shared Field.
"""

from mock import Mock
import unittest

from xblock.test.tools import TestRuntime


from xblock.core import XBlock
from xblock.fields import RemoteScope, Field, ScopeIds, List, Scope
from xblock.query import Query, Queryable
from xblock.field_data import DictFieldData, SplitFieldData
from xblock.runtime import MemoryIdManager


class TestSharedFields(unittest.TestCase):

	def setUp(self):
		self.help_message = 'This is a help message'

		class TestBlock(XBlock):
			test_field = List(
				scope=Scope.user_state, 
				help=self.help_message, 
				default=[],
				RemoteScope=RemoteScope.my_course
				)

			test_query = List.Query('test_field')

		field_data = DictFieldData({})
		sids = ScopeIds(
			user_id="bob",
			block_type="bobs-type",
	    	def_id="definition-id",
	    	usage_id="usage-id"
	    	)


		self.runtime = TestRuntime(services={'field-data': field_data})
		self.test_block = TestBlock(self.runtime, scope_ids=sids)

		self.test_field = self.test_block.fields['test_field']
		self.test_query = self.test_block.test_query

		self.test_field_name = self.test_field.name

	def test_named_scopes_len(self):
	 	self.assertEqual(4, len(RemoteScope.named_scopes()))

	def test_access_query_field_attribute(self):
		self.assertEqual(self.test_field_name, self.test_query.field_name)

	def test_access_query_type(self):
	 	self.assertTrue(isinstance(self.test_query, Queryable))

	def test_access_query_xblock(self):
	 	test_xblock = self.test_query.current_block

	 	self.assertTrue(isinstance(test_xblock, XBlock))

	def test_access_query_name(self):
		self.assertEqual(self.test_query.field_name, self.test_field.name)





