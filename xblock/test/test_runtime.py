from nose.tools import assert_equals
from mock import patch, Mock, call

from xblock.core import *
from xblock.runtime import *


class Metaclass(NamespacesMetaclass, ChildrenModelMetaclass, ModelMetaclass):
    pass


class TestNamespace(Namespace):
    n_content = String(scope=Scope.content, default='nc')
    n_settings = String(scope=Scope.settings, default='ns')
    n_student_state = String(scope=Scope.student_state, default='nss')
    n_student_preferences = String(scope=Scope.student_preferences, default='nsp')
    n_student_info = String(scope=Scope.student_info, default='nsi')
    n_by_type = String(scope=Scope(False, BlockScope.TYPE), default='nbt')
    n_for_all = String(scope=Scope(False, BlockScope.ALL), default='nfa')
    n_student_def = String(scope=Scope(True, BlockScope.DEFINITION), default='nsd')


with patch('xblock.core.Namespace.load_classes', return_value=[('test', TestNamespace)]):
    class TestModel(object):
        __metaclass__ = Metaclass

        content = String(scope=Scope.content, default='c')
        settings = String(scope=Scope.settings, default='s')
        student_state = String(scope=Scope.student_state, default='ss')
        student_preferences = String(scope=Scope.student_preferences, default='sp')
        student_info = String(scope=Scope.student_info, default='si')
        by_type = String(scope=Scope(False, BlockScope.TYPE), default='bt')
        for_all = String(scope=Scope(False, BlockScope.ALL), default='fa')
        student_def = String(scope=Scope(True, BlockScope.DEFINITION), default='sd')

        def __init__(self, model_data):
            self._model_data = model_data


class DictKeyValueStore(KeyValueStore):
    def __init__(self):
        self.db = {}

    def get(self, key):
        return self.db[key]

    def set(self, key, value):
        self.db[key] = value

    def delete(self, key):
        del self.db[key]


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
    tester = TestModel(DbModel(DictKeyValueStore(), TestModel, 's0', TestUsage('u0', 'd0')))

    for collection in (tester, tester.test):
        for field in collection.fields:
            yield check_field, collection, field


def test_db_model_keys():
    key_store = DictKeyValueStore()
    tester = TestModel(DbModel(key_store, TestModel, 's0', TestUsage('u0', 'd0')))

    for collection in (tester, tester.test):
        for field in collection.fields:
            new_value = 'new ' + field.name
            setattr(collection, field.name, new_value)

    print key_store.db
    assert_equals('new content', key_store.db[KeyValueStore.Key(Scope.content, None, 'd0', 'content')])
    assert_equals('new settings', key_store.db[KeyValueStore.Key(Scope.settings, None, 'u0', 'settings')])
    assert_equals('new student_state', key_store.db[KeyValueStore.Key(Scope.student_state, 's0', 'u0', 'student_state')])
    assert_equals('new student_preferences', key_store.db[KeyValueStore.Key(Scope.student_preferences, 's0', 'TestModel', 'student_preferences')])
    assert_equals('new student_info', key_store.db[KeyValueStore.Key(Scope.student_info, 's0', None, 'student_info')])
    assert_equals('new by_type', key_store.db[KeyValueStore.Key(Scope(False, BlockScope.TYPE), None, 'TestModel', 'by_type')])
    assert_equals('new for_all', key_store.db[KeyValueStore.Key(Scope(False, BlockScope.ALL), None, None, 'for_all')])
    assert_equals('new student_def', key_store.db[KeyValueStore.Key(Scope(True, BlockScope.DEFINITION), 's0', 'd0', 'student_def')])

    assert_equals('new n_content', key_store.db[KeyValueStore.Key(Scope.content, None, 'd0', 'n_content')])
    assert_equals('new n_settings', key_store.db[KeyValueStore.Key(Scope.settings, None, 'u0', 'n_settings')])
    assert_equals('new n_student_state', key_store.db[KeyValueStore.Key(Scope.student_state, 's0', 'u0', 'n_student_state')])
    assert_equals('new n_student_preferences', key_store.db[KeyValueStore.Key(Scope.student_preferences, 's0', 'TestModel', 'n_student_preferences')])
    assert_equals('new n_student_info', key_store.db[KeyValueStore.Key(Scope.student_info, 's0', None, 'n_student_info')])
    assert_equals('new n_by_type', key_store.db[KeyValueStore.Key(Scope(False, BlockScope.TYPE), None, 'TestModel', 'n_by_type')])
    assert_equals('new n_for_all', key_store.db[KeyValueStore.Key(Scope(False, BlockScope.ALL), None, None, 'n_for_all')])
    assert_equals('new n_student_def', key_store.db[KeyValueStore.Key(Scope(True, BlockScope.DEFINITION), 's0', 'd0', 'n_student_def')])


class MockRuntimeForQuerying(RuntimeBase):
    def __init__(self):
        self.q = Mock()

    def query(self, block):
        return self.q


def test_querypath_parsing():
    mrun = MockRuntimeForQuerying()
    block = Mock()
    q = mrun.querypath(block, "..//@hello")
    print mrun.q.mock_calls
    expected = Mock()
    expected.parent().descendants().attr("hello")
    assert mrun.q.mock_calls == expected.mock_calls
