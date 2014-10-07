"""
Tests of the utility FieldData's defined by xblock
"""
import ddt
from mock import Mock

from xblock.core import XBlock
from xblock.exceptions import InvalidScopeError
from xblock.fields import Scope, String
from xblock.field_data import SplitFieldData, ReadOnlyFieldData, OrderedLookupWithDefaultDictReadOnlyFieldData

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
    config = String(scope=Scope.configuration)
    config_not_backed_with_dict = String(scope=Scope.configuration, default="default_from_field_definition")
    plugin_name = "testing"  # supplying this, since OrderedLookupWithDefaultDictReadOnlyFieldData uses it


class OtherTestingBlock(TestingBlock):
    """
    Another XBlock class for use in the tests below
    """
    plugin_name = "other"  # supplying this, since OrderedLookupWithDefaultDictReadOnlyFieldData uses it


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


@ddt.ddt
class TestOrderedLookupWithDefaultDictReadOnlyFieldData(object):
    """
    Tests of :ref:`OrderedLookupWithDefaultDictReadOnlyFieldData`.
    """
    # First, to test inheritance.  An XBlock field looked up in OrderedLookupWithDefaultDictReadOnlyFieldData
    # can fall under 2x2 cases: the field can be defined in '_default' or not, and in its specific 'dict' or not
    # we test each case matches the expected behaviors

    def setUp(self):
        self.field_data = self.get_field_data()
        self.block = TestingBlock(
            runtime=Mock(),
            field_data=self.field_data,
            scope_ids=Mock(),
        )

    def get_field_data(self, default_exists=True, override_exists=True):
        """
        Helper method to return the appropriate testing field_data
        """
        default_dict = {'config': 'default'}
        override_dict = {'config': 'override'}
        fd_init = {}
        if default_exists:
            fd_init.update({'_default': default_dict})
        if override_exists:
            fd_init.update({'testing': override_dict})
        return OrderedLookupWithDefaultDictReadOnlyFieldData(fd_init)

    def get_testing_block_with_field_data(self, default_exists=True, override_exists=True, field_data=None):
        """
        Helper method to return a TestingBlock with the appropriate testing field_data
        """
        if not field_data:
            return TestingBlock(
                runtime=Mock(),
                field_data=self.get_field_data(default_exists, override_exists),
                scope_ids=Mock(),
            )
        else:
            return TestingBlock(
                runtime=Mock(),
                field_data=field_data,
                scope_ids=Mock(),
            )

    @ddt.unpack
    @ddt.data(
        {'default_exists': True, 'override_exists': True, 'expected': True},
        {'default_exists': True, 'override_exists': False, 'expected': True},
        {'default_exists': False, 'override_exists': True, 'expected': True},
        {'default_exists': False, 'override_exists': False, 'expected': False}
    )
    def test_has_exists(self, default_exists, override_exists, expected):
        field_data = self.get_field_data(default_exists, override_exists)
        block = self.get_testing_block_with_field_data(field_data=field_data)
        assert_equals(field_data.has(block, 'config'), expected)

    @ddt.unpack
    @ddt.data(
        {'default_exists': True, 'override_exists': True, 'expected': 'override'},
        {'default_exists': True, 'override_exists': False, 'expected': 'default'},
        {'default_exists': False, 'override_exists': True, 'expected': 'override'},
        {'default_exists': False, 'override_exists': False, 'expected': None}
    )
    def test_get_exists(self, default_exists, override_exists, expected):
        block = self.get_testing_block_with_field_data(default_exists, override_exists)
        assert_equals(block.config, expected)

    def test_default_value_from_field_definition(self):
        block = self.get_testing_block_with_field_data(default_exists=False, override_exists=False)
        assert_equals(block.config_not_backed_with_dict, "default_from_field_definition")

    def test_delete(self):
        with assert_raises(InvalidScopeError):
            self.field_data.delete(self.block, 'config')

    def test_set(self):
        with assert_raises(InvalidScopeError):
            self.field_data.set(self.block, 'config', 'foo')

    def test_set_many(self):
        with assert_raises(InvalidScopeError):
            self.field_data.set_many(self.block, {'config': 'foo', 'config_not_backed_with_dict': 'bar'})
