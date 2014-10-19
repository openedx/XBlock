"""
Tests of the utility FieldData's defined by xblock
"""

from mock import Mock

from xblock.core import XBlock
from xblock.exceptions import InvalidScopeError
from xblock.fields import Scope, String
from xblock.field_data import SplitFieldData, ReadOnlyFieldData

from xblock.test.tools import assert_false, assert_raises, assert_equals


class TestingBlock(XBlock):
    """
    An XBlock for use in the tests below.

    It has fields in a handful of scopes to test that the different scopes
    do the right thing with a split fielddata.

    """
    content = String(scope=Scope.content)
    settings = String(scope=Scope.settings)
    user_state = String(scope=Scope.user_state)


class TestSplitFieldData(object):
    """
    Tests of :ref:`SplitFieldData`.
    """
    def setUp(self):
        self.content = Mock()
        self.settings = Mock()
        self.split = SplitFieldData({
            Scope.content: self.content,
            Scope.settings: self.settings
        })
        self.block = TestingBlock(
            runtime=Mock(),
            field_data=self.split,
            scope_ids=Mock(),
        )

    def test_get(self):
        self.split.get(self.block, 'content')
        self.content.get.assert_called_once_with(self.block, 'content')
        assert_false(self.settings.get.called)

    def test_set(self):
        self.split.set(self.block, 'content', 'foo')
        self.content.set.assert_called_once_with(self.block, 'content', 'foo')
        assert_false(self.settings.set.called)

    def test_delete(self):
        self.split.delete(self.block, 'content')
        self.content.delete.assert_called_once_with(self.block, 'content')
        assert_false(self.settings.delete.called)

    def test_has(self):
        self.split.has(self.block, 'content')
        self.content.has.assert_called_once_with(self.block, 'content')
        assert_false(self.settings.has.called)

    def test_is_writable(self):
        self.split.is_writable(self.block, 'content')
        self.content.is_writable.assert_called_once_with(self.block, 'content')
        assert_false(self.settings.is_writable.called)

    def test_set_many(self):
        self.split.set_many(self.block, {'content': 'new content', 'settings': 'new settings'})
        self.content.set_many.assert_called_once_with(self.block, {'content': 'new content'})
        self.settings.set_many.assert_called_once_with(self.block, {'settings': 'new settings'})

    def test_invalid_scope(self):
        with assert_raises(InvalidScopeError):
            self.split.get(self.block, 'user_state')

    def test_default(self):
        self.split.default(self.block, 'content')
        self.content.default.assert_called_once_with(self.block, 'content')
        assert_false(self.settings.default.called)


class TestReadOnlyFieldData(object):
    """
    Tests of :ref:`ReadOnlyFieldData`.
    """
    def setUp(self):
        self.source = Mock()
        self.read_only = ReadOnlyFieldData(self.source)
        self.block = TestingBlock(
            runtime=Mock(),
            field_data=self.read_only,
            scope_ids=Mock(),
        )

    def test_get(self):
        assert_equals(self.source.get.return_value, self.read_only.get(self.block, 'content'))
        self.source.get.assert_called_once_with(self.block, 'content')

    def test_set(self):
        with assert_raises(InvalidScopeError):
            self.read_only.set(self.block, 'content', 'foo')

    def test_delete(self):
        with assert_raises(InvalidScopeError):
            self.read_only.delete(self.block, 'content')

    def test_set_many(self):
        with assert_raises(InvalidScopeError):
            self.read_only.set_many(self.block, {'content': 'foo', 'settings': 'bar'})

    def test_default(self):
        assert_equals(self.source.default.return_value, self.read_only.default(self.block, 'content'))
        self.source.default.assert_called_once_with(self.block, 'content')

    def test_has(self):
        assert_equals(self.source.has.return_value, self.read_only.has(self.block, 'content'))
        self.source.has.assert_called_once_with(self.block, 'content')

    def test_is_writable(self):
        assert_false(self.read_only.is_writable(self.block, 'content'))
