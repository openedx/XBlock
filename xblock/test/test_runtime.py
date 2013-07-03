"""Tests the features of xblock/runtime"""
# Nose redefines assert_equal and assert_not_equal
# pylint: disable=E0611
from nose.tools import assert_equals, assert_false, assert_true, assert_raises
# pylint: enable=E0611
from collections import namedtuple
from mock import patch, Mock

from xblock.core import BlockScope, ChildrenModelMetaclass, ModelMetaclass, \
    Namespace, NamespacesMetaclass, Scope, String, XBlock
from xblock.runtime import NoSuchViewError, KeyValueStore, DbModel, Runtime
from xblock.fragment import Fragment
from xblock.test import DictKeyValueStore


class Metaclass(NamespacesMetaclass, ChildrenModelMetaclass, ModelMetaclass):
    """Test Metaclass that is comprised of three of the four XBlock metaclasses
    (does not include TagCombiningMetaclass)"""
    pass


class TestNamespace(Namespace):
    """
    Set up namespaces for each scope to use.
    """
    n_content = String(scope=Scope.content, default='nc')
    n_settings = String(scope=Scope.settings, default='ns')
    n_user_state = String(scope=Scope.user_state, default='nss')
    n_preferences = String(scope=Scope.preferences, default='nsp')
    n_user_info = String(scope=Scope.user_info, default='nsi')
    n_by_type = String(scope=Scope(False, BlockScope.TYPE), default='nbt')
    n_for_all = String(scope=Scope(False, BlockScope.ALL), default='nfa')
    n_user_def = String(scope=Scope(True, BlockScope.DEFINITION), default='nsd')


with patch('xblock.core.Namespace.load_classes', return_value=[('test', TestNamespace)]):
    class TestModel(XBlock):
        """
        Set up a class that contains ModelTypes as fields.
        """
        content = String(scope=Scope.content, default='c')
        settings = String(scope=Scope.settings, default='s')
        user_state = String(scope=Scope.user_state, default='ss')
        preferences = String(scope=Scope.preferences, default='sp')
        user_info = String(scope=Scope.user_info, default='si')
        by_type = String(scope=Scope(False, BlockScope.TYPE), default='bt')
        for_all = String(scope=Scope(False, BlockScope.ALL), default='fa')
        user_def = String(scope=Scope(True, BlockScope.DEFINITION), default='sd')

with patch('xblock.core.Namespace.load_classes', return_value=[('test', TestNamespace)]):
    class TestXBlock(XBlock):
        """
        Set up a class that contains ModelTypes as fields.
        """
        content = String(scope=Scope.content, default='c')
        settings = String(scope=Scope.settings, default='s')
        user_state = String(scope=Scope.user_state, default='ss')
        preferences = String(scope=Scope.preferences, default='sp')
        user_info = String(scope=Scope.user_info, default='si')
        by_type = String(scope=Scope(False, BlockScope.TYPE), default='bt')
        for_all = String(scope=Scope(False, BlockScope.ALL), default='fa')
        user_def = String(scope=Scope(True, BlockScope.DEFINITION), default='sd')

        def existing_handler(self, data):
            """ an existing handler to be used """
            self.user_state = data
            return "I am the existing test handler"

        def fallback_handler(self, handler_name, data):
            """ test fallback handler """
            self.user_state = data
            if handler_name == 'test_fallback_handler':
                return "I have been handled"

        def student_view(self, context):
            """ an existing view to be used """
            self.preferences = context[0]
            return Fragment(self.preferences)

        def fallback_view(self, view_name, context):
            """ test fallback view """
            self.preferences = context[0]
            if view_name == 'test_fallback_view':
                return Fragment(self.preferences)

with patch('xblock.core.Namespace.load_classes', return_value=[('test', TestNamespace)]):
    class TestXBlockNoFallback(XBlock):
        """
        Set up a class that contains ModelTypes as fields.
        """
        content = String(scope=Scope.content, default='c')
        settings = String(scope=Scope.settings, default='s')
        user_state = String(scope=Scope.user_state, default='ss')
        preferences = String(scope=Scope.preferences, default='sp')
        user_info = String(scope=Scope.user_info, default='si')
        by_type = String(scope=Scope(False, BlockScope.TYPE), default='bt')
        for_all = String(scope=Scope(False, BlockScope.ALL), default='fa')
        user_def = String(scope=Scope(True, BlockScope.DEFINITION), default='sd')

# Allow this tuple to be named as if it were a class
# pylint: disable=C0103
TestUsage = namedtuple('TestUsage', 'id, def_id')
# pylint: enable=C0103


def check_field(collection, field):
    """
    Test method.

    Asserts that the given `field` is present in `collection`.
    Sets the field to a new value and asserts that the update properly occurs.
    Deletes the new value, and asserts that the default value is properly restored.
    """
    print "Getting %s from %r" % (field.name, collection)
    assert_equals(field.default, getattr(collection, field.name))
    new_value = 'new ' + field.name
    print "Setting %s to %s on %r" % (field.name, new_value, collection)
    setattr(collection, field.name, new_value)
    print "Checking %s on %r" % (field.name, collection)
    assert_equals(new_value, getattr(collection, field.name))
    print "Deleting %s from %r" % (field.name, collection)
    delattr(collection, field.name)
    print "Back to defaults for %s in %r" % (field.name, collection)
    assert_equals(field.default, getattr(collection, field.name))


def test_namespace_actions():
    tester = TestModel(Mock(), DbModel(DictKeyValueStore(), TestModel, 's0', TestUsage('u0', 'd0')))
    # `test` is a namespace provided by the patch when TestModel is defined, which ultimately
    # comes from the NamespacesMetaclass. Since this is not understood by static
    # analysis, silence this error for the duration of this test.
    # pylint: disable=E1101, E1103
    for collection in (tester, tester.test):
        for field in collection.fields:
            yield check_field, collection, field


def test_db_model_keys():
    # Tests that updates to fields are properly recorded in the KeyValueStore,
    # and that the keys have been constructed correctly
    key_store = DictKeyValueStore()
    db_model = DbModel(key_store, TestModel, 's0', TestUsage('u0', 'd0'))
    tester = TestModel(Mock(), db_model)

    assert_false('not a field' in db_model)

    # `test` is a namespace provided by the patch when TestModel is defined, which ultimately
    # comes from the NamespacesMetaclass. Since this is not understood by static
    # analysis, silence this error for the duration of this test.
    # pylint: disable=E1101, E1103
    for collection in (tester, tester.test):
        for field in collection.fields:
            new_value = 'new ' + field.name
            assert_false(field.name in db_model)
            setattr(collection, field.name, new_value)

    # Write out the values
    tester.save()

    # Make sure everything saved correctly
    for collection in (tester, tester.test):
        for field in collection.fields:
            assert_true(field.name in db_model)

    print key_store.db_dict

    # Examine each value in the database and ensure that keys were constructed correctly
    assert_equals(
        'new content',
        key_store.db_dict[KeyValueStore.Key(Scope.content, None, 'd0', 'content')]
    )
    assert_equals(
        'new settings',
        key_store.db_dict[KeyValueStore.Key(Scope.settings, None, 'u0', 'settings')]
    )
    assert_equals(
        'new user_state',
        key_store.db_dict[KeyValueStore.Key(Scope.user_state, 's0', 'u0', 'user_state')]
    )
    assert_equals(
        'new preferences',
        key_store.db_dict[KeyValueStore.Key(Scope.preferences, 's0', 'TestModel', 'preferences')]
    )
    assert_equals(
        'new user_info',
        key_store.db_dict[KeyValueStore.Key(Scope.user_info, 's0', None, 'user_info')]
    )
    assert_equals(
        'new by_type',
        key_store.db_dict[KeyValueStore.Key(Scope(False, BlockScope.TYPE), None, 'TestModel', 'by_type')]
    )
    assert_equals(
        'new for_all',
        key_store.db_dict[KeyValueStore.Key(Scope(False, BlockScope.ALL), None, None, 'for_all')]
    )
    assert_equals(
        'new user_def',
        key_store.db_dict[KeyValueStore.Key(Scope(True, BlockScope.DEFINITION), 's0', 'd0', 'user_def')]
    )

    assert_equals(
        'new n_content',
        key_store.db_dict[KeyValueStore.Key(Scope.content, None, 'd0', 'n_content')]
    )
    assert_equals(
        'new n_settings',
        key_store.db_dict[KeyValueStore.Key(Scope.settings, None, 'u0', 'n_settings')]
    )
    assert_equals(
        'new n_user_state',
        key_store.db_dict[KeyValueStore.Key(Scope.user_state, 's0', 'u0', 'n_user_state')]
    )
    assert_equals(
        'new n_preferences',
        key_store.db_dict[KeyValueStore.Key(Scope.preferences, 's0', 'TestModel', 'n_preferences')]
    )
    assert_equals(
        'new n_user_info',
        key_store.db_dict[KeyValueStore.Key(Scope.user_info, 's0', None, 'n_user_info')]
    )
    assert_equals(
        'new n_by_type',
        key_store.db_dict[KeyValueStore.Key(Scope(False, BlockScope.TYPE), None, 'TestModel', 'n_by_type')]
    )
    assert_equals(
        'new n_for_all',
        key_store.db_dict[KeyValueStore.Key(Scope(False, BlockScope.ALL), None, None, 'n_for_all')]
    )
    assert_equals(
        'new n_user_def',
        key_store.db_dict[KeyValueStore.Key(Scope(True, BlockScope.DEFINITION), 's0', 'd0', 'n_user_def')]
    )


class MockRuntimeForQuerying(Runtime):
    """Mock out a runtime for querypath_parsing test"""
    # OK for this mock class to not override abstract methods or call base __init__
    # pylint: disable=W0223, W0231
    def __init__(self):
        self.mock_query = Mock()

    def query(self, block):
        return self.mock_query


def test_querypath_parsing():
    mrun = MockRuntimeForQuerying()
    block = Mock()
    mrun.querypath(block, "..//@hello")
    print mrun.mock_query.mock_calls
    expected = Mock()
    expected.parent().descendants().attr("hello")
    assert mrun.mock_query.mock_calls == expected.mock_calls


def test_runtime_handle():
    # Test a simple handler and a fallback handler

    key_store = DictKeyValueStore()
    db_model = DbModel(key_store, TestXBlock, 's0', TestUsage('u0', 'd0'))
    tester = TestXBlock(Mock(), db_model)
    runtime = MockRuntimeForQuerying()
    # string we want to update using the handler
    update_string = "user state update"
    assert_equals(runtime.handle(tester, 'existing_handler', update_string),
                  'I am the existing test handler')
    assert_equals(tester.user_state, update_string)

    # when the handler needs to use the fallback as given name can't be found
    new_update_string = "new update"
    assert_equals(runtime.handle(tester, 'test_fallback_handler', new_update_string),
                  'I have been handled')
    assert_equals(tester.user_state, new_update_string)

    # handler can't be found & no fallback handler supplied, should throw an exception
    tester = TestXBlockNoFallback(Mock(), db_model)
    ultimate_string = "ultimate update"
    with assert_raises(Exception):
        runtime.handle(tester, 'test_nonexistant_fallback_handler', ultimate_string)


def test_runtime_render():
    key_store = DictKeyValueStore()
    db_model = DbModel(key_store, TestXBlock, 's0', TestUsage('u0', 'd0'))
    tester = TestXBlock(Mock(), db_model)
    runtime = MockRuntimeForQuerying()
    # string we want to update using the handler
    update_string = u"user state update"

    # test against the student view
    frag = runtime.render(tester, [update_string], 'student_view')
    assert_equals(frag.body_html(), update_string)
    assert_equals(tester.preferences, update_string)

    # test against the fallback view
    update_string = u"new update"
    frag = runtime.render(tester, [update_string], 'test_fallback_view')
    assert_equals(frag.body_html(), update_string)
    assert_equals(tester.preferences, update_string)

    # test against the no-fallback XBlock
    update_string = u"ultimate update"
    tester = TestXBlockNoFallback(Mock(), db_model)
    with assert_raises(NoSuchViewError):
        runtime.render(tester, [update_string], 'test_nonexistant_view')
