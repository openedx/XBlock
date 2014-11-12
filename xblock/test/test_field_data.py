"""
Tests of the utility FieldData's defined by xblock
"""
import ddt
from mock import Mock

from xblock.core import XBlock
from xblock.exceptions import InvalidScopeError, BadFieldDataComponent, FieldDataError
from xblock.fields import Scope, String
from xblock.field_data import (
    SplitFieldData,
    ReadOnlyFieldData,
    OrderedFieldDataList,
    XBlockRoutedFieldData,
    get_configuration_field_data,
)

from xblock.test.tools import assert_false, assert_raises, assert_equals, TestRuntime


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
    plugin_name = "testing"  # supplying this, since XBlockRoutedFieldData uses it


class AnotherTestingXBlock(TestingBlock):
    """
    Identical to `TestingBlock`, just a different class for tests that need it
    """
    pass


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
        self.runtime = TestRuntime(services={'field-data': self.split})
        self.block = TestingBlock(
            runtime=self.runtime,
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
        self.runtime = TestRuntime(services={'field-data': self.read_only})
        self.block = TestingBlock(
            runtime=self.runtime,
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
class TestOrderedFieldDataList(object):
    """
    Tests of :ref:`OrderedFieldDataList`
    """
    def setUp(self):
        self.first = Mock()
        self.second = Mock()
        self.ofdl = OrderedFieldDataList([self.first, self.second])
        self.block = TestingBlock(
            runtime=Mock(),
            field_data=self.ofdl,
            scope_ids=Mock(),
        )

    def test_bad_init(self):
        with assert_raises(BadFieldDataComponent):
            OrderedFieldDataList([])

    def test_get_first(self):
        self.first.get.return_value = "retv"
        self.second.get.side_effect = KeyError
        assert_equals(self.ofdl.get(self.block, "getme"), "retv")
        self.first.get.called_with(self.block, "getme")
        assert_false(self.second.get.called)

    def test_get_second(self):
        self.first.get.side_effect = KeyError
        self.second.get.return_value = "retv"
        assert_equals(self.ofdl.get(self.block, "getme"), "retv")
        self.first.get.called_with(self.block, "getme")
        self.second.get.called_with(self.block, "getme")

    def test_get_fails(self):
        self.first.get.side_effect = KeyError
        self.second.get.side_effect = KeyError
        with assert_raises(KeyError):
            self.ofdl.get(self.block, "getme")
        self.first.get.called_with(self.block, "getme")
        self.second.get.called_with(self.block, "getme")

    def test_set(self):
        self.ofdl.set(self.block, "name", "val")
        self.first.set.assert_called_once_with(self.block, "name", "val")
        assert_false(self.second.set.called)

    def test_delete(self):
        self.ofdl.delete(self.block, "deleteme")
        self.first.delete.called_with(self.block, "deleteme")
        self.second.delete.called_with(self.block, "deleteme")

    def test_delete_cascade(self):
        self.first.delete.side_effect = FieldDataError
        self.ofdl.delete(self.block, "deleteme")
        self.first.delete.called_with(self.block, "deleteme")
        self.second.delete.called_with(self.block, "deleteme")

    @ddt.unpack
    @ddt.data(
        {'retv_1': False, 'retv_2': False, 'retv_expected': False, 'called_1': True, 'called_2': True},
        {'retv_1': False, 'retv_2': True, 'retv_expected': True, 'called_1': True, 'called_2': True},
        {'retv_1': True, 'retv_2': False, 'retv_expected': True, 'called_1': True, 'called_2': False},
        {'retv_1': True, 'retv_2': True, 'retv_expected': True, 'called_1': True, 'called_2': False},
    )
    def test_has(self, retv_1, retv_2, retv_expected, called_1, called_2):
        """
        Tests for has.  Also tests short-cutting
        """
        self.first.has.return_value = retv_1
        self.second.has.return_value = retv_2
        assert_equals(self.ofdl.has(self.block, "hasme"), retv_expected)
        assert_equals(called_1, self.first.has.called)
        assert_equals(called_2, self.second.has.called)

    def test_set_many(self):
        update_dict = {"name": "value"}
        self.ofdl.set_many(self.block, update_dict)
        self.first.set_many.assert_called_once_with(self.block, update_dict)
        assert_false(self.second.set_many.called)

    def test_default_first(self):
        self.first.default.return_value = "default"
        self.second.default.side_effect = KeyError
        assert_equals(self.ofdl.default(self.block, "defaultme"), "default")
        self.first.default.called_with(self.block, "defaultme")
        assert_false(self.second.default.called)

    def test_default_second(self):
        self.first.default.side_effect = KeyError
        self.second.default.return_value = "default"
        assert_equals(self.ofdl.default(self.block, "defaultme"), "default")
        self.first.default.called_with(self.block, "defaultme")
        self.second.default.called_with(self.block, "defaultme")

    def test_default_fails(self):
        self.first.default.side_effect = KeyError
        self.second.default.side_effect = KeyError
        with assert_raises(KeyError):
            self.ofdl.default(self.block, "defaultme")
        self.first.default.called_with(self.block, "defaultme")
        self.second.default.called_with(self.block, "defaultme")


@ddt.ddt
class TestXBlockRoutedFieldData(object):
    """
    Test for :ref:`XBlockRoutedFieldData`
    """
    def setUp(self):
        self.mapped_fd = Mock()
        self.field_data = XBlockRoutedFieldData(
            {
                AnotherTestingXBlock: self.mapped_fd,
            },
            get_xblock_class
        )
        self.mapped_block = AnotherTestingXBlock(
            runtime=Mock(),
            field_data=self.field_data,
            scope_ids=Mock(),
        )
        self.unmapped_block = TestingBlock(
            runtime=Mock(),
            field_data=self.field_data,
            scope_ids=Mock(),
        )

    def test_unmapped_exception(self):
        with assert_raises(XBlockRoutedFieldData.KeyNotInMappingsExceptionClass):
            self.field_data._field_data(self.unmapped_block)  # pylint: disable=protected-access

    def test_get(self):
        self.mapped_fd.get.return_value = "retv"
        assert_equals(self.field_data.get(self.mapped_block, "getme"), "retv")
        self.mapped_fd.get.assert_called_once_with(self.mapped_block, "getme")

    def test_get_exception(self):
        with assert_raises(KeyError):
            self.field_data.get(self.unmapped_block, "getme")
        assert_false(self.mapped_fd.get.called)

    def test_set(self):
        self.field_data.set(self.mapped_block, "setme", "setv")
        self.mapped_fd.set.assert_called_once_with(self.mapped_block, "setme", "setv")

    def test_set_many(self):
        update_dict = {"setme": "setv"}
        self.field_data.set_many(self.mapped_block, update_dict)
        self.mapped_fd.set_many.assert_called_once_with(self.mapped_block, update_dict)

    def test_delete(self):
        self.field_data.delete(self.mapped_block, "deleteme")
        self.mapped_fd.delete.assert_called_once_with(self.mapped_block, "deleteme")

    @ddt.unpack
    @ddt.data(
        {'has': True, 'expected': True},
        {'has': False, 'expected': False},
    )
    def test_has_mapped(self, has, expected):
        self.mapped_fd.has.return_value = has
        assert_equals(self.field_data.has(self.mapped_block, "hasme"), expected)
        self.mapped_fd.has.assert_called_once_with(self.mapped_block, "hasme")

    def test_has_unmapped(self):
        self.mapped_fd.has.return_value = True
        assert_false(self.field_data.has(self.unmapped_block, "hasme"))
        assert_false(self.mapped_fd.has.called)

    def test_default(self):
        self.mapped_fd.default.return_value = "default"
        assert_equals(self.field_data.default(self.mapped_block, "defaultme"), "default")
        self.mapped_fd.default.assert_called_once_with(self.mapped_block, "defaultme")

    def test_default_unmapped(self):
        self.mapped_fd.has.return_value = True
        with assert_raises(KeyError):
            self.field_data.default(self.unmapped_block, "defaultme")
        assert_false(self.mapped_fd.default.called)


@ddt.ddt
class TestConfigurationFieldData(object):
    """
    Tests of the FieldData output of `get_configuration_field_data`, tailored towards Scope.configuration.
    """

    # First, to test inheritance.  An XBlock field looked up in configuration FieldData
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
        return get_configuration_field_data(fd_init)

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


def get_xblock_class(xblock):
    """
    returns the class of xblock.  Used as the xblock's routing key for XBlockRoutedFieldData
    """
    return xblock.__class__
