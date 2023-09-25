"""
Test cases for xblock/utils/settings.py
"""
import itertools
import unittest
from unittest.mock import Mock, MagicMock, patch

import ddt

from xblock.core import XBlock
from xblock.utils.settings import XBlockWithSettingsMixin, ThemableXBlockMixin


@XBlock.wants('settings')
class DummyXBlockWithSettings(XBlock, XBlockWithSettingsMixin, ThemableXBlockMixin):
    """
    A dummy XBlock test class provides configurable theme support via Settings Service
    """
    block_settings_key = 'dummy_settings_bucket'
    default_theme_config = {
        'package': 'xblock_utils',
        'locations': ['qwe.css']
    }


@XBlock.wants('settings')
class OtherXBlockWithSettings(XBlock, XBlockWithSettingsMixin, ThemableXBlockMixin):
    """
    Another XBlock test class provides configurable theme support via Settings Service
    """
    block_settings_key = 'other_settings_bucket'
    theme_key = 'other_xblock_theme'
    default_theme_config = {
        'package': 'xblock_utils',
        'locations': ['qwe.css']
    }


@ddt.ddt
class TestXBlockWithSettingsMixin(unittest.TestCase):
    """
    Test cases for XBlockWithSettingsMixin
    """
    def setUp(self):
        self.settings_service = Mock()
        self.runtime = Mock()
        self.runtime.service = Mock(return_value=self.settings_service)

    @ddt.data(None, 1, "2", [3, 4], {5: '6'})
    def test_no_settings_service_return_default(self, default_value):
        xblock = DummyXBlockWithSettings(self.runtime, scope_ids=Mock())
        self.runtime.service.return_value = None
        self.assertEqual(xblock.get_xblock_settings(default=default_value), default_value)

    @ddt.data(*itertools.product(
        (DummyXBlockWithSettings, OtherXBlockWithSettings),
        (None, 1, "2", [3, 4], {5: '6'}),
        (None, 'default1')
    ))
    @ddt.unpack
    def test_invokes_get_settings_bucket_and_returns_result(self, block, settings_service_return_value, default):
        xblock = block(self.runtime, scope_ids=Mock())

        self.settings_service.get_settings_bucket = Mock(return_value=settings_service_return_value)
        self.assertEqual(xblock.get_xblock_settings(default=default), settings_service_return_value)
        self.settings_service.get_settings_bucket.assert_called_with(xblock, default=default)


@ddt.ddt
class TestThemableXBlockMixin(unittest.TestCase):
    """
    Test cases for ThemableXBlockMixin
    """
    def setUp(self):
        self.service_mock = Mock()
        self.runtime_mock = Mock()
        self.runtime_mock.service = Mock(return_value=self.service_mock)

    @ddt.data(DummyXBlockWithSettings, OtherXBlockWithSettings)
    def test_theme_uses_default_theme_if_settings_service_is_not_available(self, xblock_class):
        xblock = xblock_class(self.runtime_mock, scope_ids=Mock())
        self.runtime_mock.service = Mock(return_value=None)
        self.assertEqual(xblock.get_theme(), xblock_class.default_theme_config)

    @ddt.data(DummyXBlockWithSettings, OtherXBlockWithSettings)
    def test_theme_uses_default_theme_if_no_theme_is_set(self, xblock_class):
        xblock = xblock_class(self.runtime_mock, scope_ids=Mock())
        self.service_mock.get_settings_bucket = Mock(return_value=None)
        self.assertEqual(xblock.get_theme(), xblock_class.default_theme_config)
        self.service_mock.get_settings_bucket.assert_called_once_with(xblock, default={})

    @ddt.data(*itertools.product(
        (DummyXBlockWithSettings, OtherXBlockWithSettings),
        (123, object())
    ))
    @ddt.unpack
    def test_theme_raises_if_theme_object_is_not_iterable(self, xblock_class, theme_config):
        xblock = xblock_class(self.runtime_mock, scope_ids=Mock())
        self.service_mock.get_settings_bucket = Mock(return_value=theme_config)
        with self.assertRaises(TypeError):
            xblock.get_theme()
        self.service_mock.get_settings_bucket.assert_called_once_with(xblock, default={})

    @ddt.data(*itertools.product(
        (DummyXBlockWithSettings, OtherXBlockWithSettings),
        ({}, {'mass': 123}, {'spin': {}}, {'parity': "1"})
    ))
    @ddt.unpack
    def test_theme_uses_default_theme_if_no_mentoring_theme_is_set_up(self, xblock_class, theme_config):
        xblock = xblock_class(self.runtime_mock, scope_ids=Mock())
        self.service_mock.get_settings_bucket = Mock(return_value=theme_config)
        self.assertEqual(xblock.get_theme(), xblock_class.default_theme_config)
        self.service_mock.get_settings_bucket.assert_called_once_with(xblock, default={})

    @ddt.data(*itertools.product(
        (DummyXBlockWithSettings, OtherXBlockWithSettings),
        (123, [1, 2, 3], {'package': 'qwerty', 'locations': ['something_else.css']}),
    ))
    @ddt.unpack
    def test_theme_correctly_returns_configured_theme(self, xblock_class, theme_config):
        xblock = xblock_class(self.runtime_mock, scope_ids=Mock())
        self.service_mock.get_settings_bucket = Mock(return_value={xblock_class.theme_key: theme_config})
        self.assertEqual(xblock.get_theme(), theme_config)

    @ddt.data(DummyXBlockWithSettings, OtherXBlockWithSettings)
    def test_theme_files_are_loaded_from_correct_package(self, xblock_class):
        xblock = xblock_class(self.runtime_mock, scope_ids=Mock())
        fragment = MagicMock()
        package_name = 'some_package'
        theme_config = {xblock_class.theme_key: {'package': package_name, 'locations': ['lms.css']}}
        self.service_mock.get_settings_bucket = Mock(return_value=theme_config)
        with patch("xblock.utils.settings.ResourceLoader") as patched_resource_loader:
            xblock.include_theme_files(fragment)
            patched_resource_loader.assert_called_with(package_name)

    @ddt.data(
        ('dummy_block', ['']),
        ('dummy_block', ['public/themes/lms.css']),
        ('other_block', ['public/themes/lms.css', 'public/themes/lms.part2.css']),
        ('dummy_app.dummy_block', ['typography.css', 'icons.css']),
    )
    @ddt.unpack
    def test_theme_files_are_added_to_fragment(self, package_name, locations):
        xblock = DummyXBlockWithSettings(self.runtime_mock, scope_ids=Mock())
        fragment = MagicMock()
        theme_config = {DummyXBlockWithSettings.theme_key: {'package': package_name, 'locations': locations}}
        self.service_mock.get_settings_bucket = Mock(return_value=theme_config)
        with patch("xblock.utils.settings.ResourceLoader.load_unicode") as patched_load_unicode:
            xblock.include_theme_files(fragment)
            for location in locations:
                patched_load_unicode.assert_any_call(location)

            self.assertEqual(patched_load_unicode.call_count, len(locations))

    @ddt.data(None, {}, {'locations': ['red.css']})
    def test_invalid_default_theme_config(self, theme_config):
        xblock = DummyXBlockWithSettings(self.runtime_mock, scope_ids=Mock())
        xblock.default_theme_config = theme_config
        self.service_mock.get_settings_bucket = Mock(return_value={})
        fragment = MagicMock()
        with patch("xblock.utils.settings.ResourceLoader.load_unicode") as patched_load_unicode:
            xblock.include_theme_files(fragment)
            patched_load_unicode.assert_not_called()
