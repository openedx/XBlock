from nose.tools import assert_equals, assert_false, assert_true, assert_raises
from mock import patch, Mock

from xblock.core import *
from xblock.runtime import *
from xblock.fragment import Fragment
from xblock.test import DictKeyValueStore


class Metaclass(NamespacesMetaclass, ChildrenModelMetaclass, ModelMetaclass):
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
            self.preferences = context[0]
            return Fragment(self.preferences)

        def fallback_view(self, view_name, context):
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

TestUsage = namedtuple('TestUsage', 'id, def_id')


def check_field(collection, field):
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

    for collection in (tester, tester.test):
        for field in collection.fields:
            yield check_field, collection, field


def test_db_model_keys():
    """
    Tests that updates to fields are properly recorded in the KeyValueStore,
    and that the keys have been constructed correctly
    """
    key_store = DictKeyValueStore()
    db_model = DbModel(key_store, TestModel, 's0', TestUsage('u0', 'd0'))
    tester = TestModel(Mock(), db_model)

    assert_false('not a field' in db_model)

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

    print key_store.db

    # Examine each value in the database and ensure that keys were constructed correctly
    assert_equals('new content', key_store.db[KeyValueStore.Key(Scope.content, None, 'd0', 'content')])
    assert_equals('new settings', key_store.db[KeyValueStore.Key(Scope.settings, None, 'u0', 'settings')])
    assert_equals('new user_state', key_store.db[KeyValueStore.Key(Scope.user_state, 's0', 'u0', 'user_state')])
    assert_equals('new preferences', key_store.db[KeyValueStore.Key(Scope.preferences, 's0', 'TestModel', 'preferences')])
    assert_equals('new user_info', key_store.db[KeyValueStore.Key(Scope.user_info, 's0', None, 'user_info')])
    assert_equals('new by_type', key_store.db[KeyValueStore.Key(Scope(False, BlockScope.TYPE), None, 'TestModel', 'by_type')])
    assert_equals('new for_all', key_store.db[KeyValueStore.Key(Scope(False, BlockScope.ALL), None, None, 'for_all')])
    assert_equals('new user_def', key_store.db[KeyValueStore.Key(Scope(True, BlockScope.DEFINITION), 's0', 'd0', 'user_def')])

    assert_equals('new n_content', key_store.db[KeyValueStore.Key(Scope.content, None, 'd0', 'n_content')])
    assert_equals('new n_settings', key_store.db[KeyValueStore.Key(Scope.settings, None, 'u0', 'n_settings')])
    assert_equals('new n_user_state', key_store.db[KeyValueStore.Key(Scope.user_state, 's0', 'u0', 'n_user_state')])
    assert_equals('new n_preferences', key_store.db[KeyValueStore.Key(Scope.preferences, 's0', 'TestModel', 'n_preferences')])
    assert_equals('new n_user_info', key_store.db[KeyValueStore.Key(Scope.user_info, 's0', None, 'n_user_info')])
    assert_equals('new n_by_type', key_store.db[KeyValueStore.Key(Scope(False, BlockScope.TYPE), None, 'TestModel', 'n_by_type')])
    assert_equals('new n_for_all', key_store.db[KeyValueStore.Key(Scope(False, BlockScope.ALL), None, None, 'n_for_all')])
    assert_equals('new n_user_def', key_store.db[KeyValueStore.Key(Scope(True, BlockScope.DEFINITION), 's0', 'd0', 'n_user_def')])


class MockRuntimeForQuerying(Runtime):
    def __init__(self):
        self.q = Mock()

    def query(self, block):
        return self.q


def test_querypath_parsing():
    mrun = MockRuntimeForQuerying()
    block = Mock()
    mrun.querypath(block, "..//@hello")
    print mrun.q.mock_calls
    expected = Mock()
    expected.parent().descendants().attr("hello")
    assert mrun.q.mock_calls == expected.mock_calls


def test_runtime_handle():
    """
    Test a simple handler and a fallback handler

    """
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
