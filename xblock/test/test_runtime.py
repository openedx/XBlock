"""Tests the features of xblock/runtime"""
# Allow tests to access private members of classes
# pylint: disable=W0212

# Nose redefines assert_equal and assert_not_equal
# pylint: disable=E0611
from nose.tools import (
    assert_equals, assert_false, assert_true, assert_raises,
    assert_is, assert_is_not
)
# pylint: enable=E0611
from collections import namedtuple
from mock import Mock

from xblock.core import XBlock
from xblock.fields import BlockScope, Scope, String, ScopeIds, Integer, List, UserScope
from xblock.exceptions import NoSuchViewError, NoSuchHandlerError
from xblock.runtime import KeyValueStore, DbModel, Runtime
from xblock.fragment import Fragment
from xblock.test import DictKeyValueStore
from xblock.test.tools import DictModel


class TestMixin(object):
    """
    Set up namespaces for each scope to use.
    """
    mixin_content = String(scope=Scope.content, default='mixin_c')
    mixin_settings = String(scope=Scope.settings, default='mixin_s')
    mixin_user_state = String(scope=Scope.user_state, default='mixin_ss')
    mixin_preferences = String(scope=Scope.preferences, default='mixin_sp')
    mixin_user_info = String(scope=Scope.user_info, default='mixin_si')
    mixin_by_type = String(scope=Scope(UserScope.NONE, BlockScope.TYPE), default='mixin_bt')
    mixin_for_all = String(scope=Scope(UserScope.NONE, BlockScope.ALL), default='mixin_fa')
    mixin_user_def = String(scope=Scope(UserScope.ONE, BlockScope.DEFINITION), default='mixin_sd')
    mixin_agg_global = String(scope=Scope(UserScope.ALL, BlockScope.ALL), default='mixin_ag')
    mixin_agg_type = String(scope=Scope(UserScope.ALL, BlockScope.TYPE), default='mixin_at')
    mixin_agg_def = String(scope=Scope(UserScope.ALL, BlockScope.DEFINITION), default='mixin_ad')
    mixin_agg_usage = String(scope=Scope.user_state_summary, default='mixin_au')


class TestXBlockNoFallback(XBlock):
    """
    Set up a class that contains ModelTypes as fields, but no views or handlers
    """
    content = String(scope=Scope.content, default='c')
    settings = String(scope=Scope.settings, default='s')
    user_state = String(scope=Scope.user_state, default='ss')
    preferences = String(scope=Scope.preferences, default='sp')
    user_info = String(scope=Scope.user_info, default='si')
    by_type = String(scope=Scope(UserScope.NONE, BlockScope.TYPE), default='bt')
    for_all = String(scope=Scope(UserScope.NONE, BlockScope.ALL), default='fa')
    user_def = String(scope=Scope(UserScope.ONE, BlockScope.DEFINITION), default='sd')
    agg_global = String(scope=Scope(UserScope.ALL, BlockScope.ALL), default='ag')
    agg_type = String(scope=Scope(UserScope.ALL, BlockScope.TYPE), default='at')
    agg_def = String(scope=Scope(UserScope.ALL, BlockScope.DEFINITION), default='ad')
    agg_usage = String(scope=Scope.user_state_summary, default='au')



class TestXBlock(TestXBlockNoFallback):
    """
    Test xblock class with fallbock methods
    """
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


# Allow this tuple to be named as if it were a class
TestUsage = namedtuple('TestUsage', 'id, def_id')  # pylint: disable=C0103


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


def test_db_model_keys():
    # Tests that updates to fields are properly recorded in the KeyValueStore,
    # and that the keys have been constructed correctly
    key_store = DictKeyValueStore()
    db_model = DbModel(key_store)
    runtime = Runtime([TestMixin])
    tester = runtime.construct_block_from_class(TestXBlock, db_model, ScopeIds('s0', 'TestXBlock', 'd0', 'u0'))

    assert_false(db_model.has(tester, 'not a field'))

    for field in tester.fields.values():
        new_value = 'new ' + field.name
        assert_false(db_model.has(tester, field.name))
        setattr(tester, field.name, new_value)

    # Write out the values
    tester.save()

    # Make sure everything saved correctly
    for field in tester.fields.values():
        assert_true(db_model.has(tester, field.name))

    def get_key_value(scope, student_id, block_scope_id, field_name):
        """Gets the value, from `key_store`, of a Key with the given values."""
        new_key = KeyValueStore.Key(scope, student_id, block_scope_id, field_name)
        return key_store.db_dict[new_key]

    # Examine each value in the database and ensure that keys were constructed correctly
    assert_equals('new content', get_key_value(Scope.content, None, 'd0', 'content'))
    assert_equals('new settings', get_key_value(Scope.settings, None, 'u0', 'settings'))
    assert_equals('new user_state', get_key_value(Scope.user_state, 's0', 'u0', 'user_state'))
    assert_equals('new preferences', get_key_value(Scope.preferences, 's0', 'TestXBlock', 'preferences'))
    assert_equals('new user_info', get_key_value(Scope.user_info, 's0', None, 'user_info'))
    assert_equals('new by_type', get_key_value(Scope(UserScope.NONE, BlockScope.TYPE), None, 'TestXBlock', 'by_type'))
    assert_equals('new for_all', get_key_value(Scope(UserScope.NONE, BlockScope.ALL), None, None, 'for_all'))
    assert_equals('new user_def', get_key_value(Scope(UserScope.ONE, BlockScope.DEFINITION), 's0', 'd0', 'user_def'))
    assert_equals('new agg_global', get_key_value(Scope(UserScope.ALL, BlockScope.ALL), None, None, 'agg_global'))
    assert_equals('new agg_type', get_key_value(Scope(UserScope.ALL, BlockScope.TYPE), None, 'TestXBlock', 'agg_type'))
    assert_equals('new agg_def', get_key_value(Scope(UserScope.ALL, BlockScope.DEFINITION), None, 'd0', 'agg_def'))
    assert_equals('new agg_usage', get_key_value(Scope.user_state_summary, None, 'u0', 'agg_usage'))
    assert_equals('new mixin_content', get_key_value(Scope.content, None, 'd0', 'mixin_content'))
    assert_equals('new mixin_settings', get_key_value(Scope.settings, None, 'u0', 'mixin_settings'))
    assert_equals('new mixin_user_state', get_key_value(Scope.user_state, 's0', 'u0', 'mixin_user_state'))
    assert_equals('new mixin_preferences', get_key_value(Scope.preferences, 's0', 'TestXBlock', 'mixin_preferences'))
    assert_equals('new mixin_user_info', get_key_value(Scope.user_info, 's0', None, 'mixin_user_info'))
    assert_equals('new mixin_by_type', get_key_value(Scope(UserScope.NONE, BlockScope.TYPE), None, 'TestXBlock', 'mixin_by_type'))
    assert_equals('new mixin_for_all', get_key_value(Scope(UserScope.NONE, BlockScope.ALL), None, None, 'mixin_for_all'))
    assert_equals('new mixin_user_def', get_key_value(Scope(UserScope.ONE, BlockScope.DEFINITION), 's0', 'd0', 'mixin_user_def'))
    assert_equals('new mixin_agg_global', get_key_value(Scope(UserScope.ALL, BlockScope.ALL), None, None, 'mixin_agg_global'))
    assert_equals('new mixin_agg_type', get_key_value(Scope(UserScope.ALL, BlockScope.TYPE), None, 'TestXBlock', 'mixin_agg_type'))
    assert_equals('new mixin_agg_def', get_key_value(Scope(UserScope.ALL, BlockScope.DEFINITION), None, 'd0', 'mixin_agg_def'))
    assert_equals('new mixin_agg_usage', get_key_value(Scope.user_state_summary, None, 'u0', 'mixin_agg_usage'))


class MockRuntimeForQuerying(Runtime):
    """Mock out a runtime for querypath_parsing test"""
    # OK for this mock class to not override abstract methods or call base __init__
    # pylint: disable=W0223, W0231
    def __init__(self):
        super(MockRuntimeForQuerying, self).__init__()
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
    db_model = DbModel(key_store)
    tester = TestXBlock(Mock(), db_model, Mock())
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
    tester = TestXBlockNoFallback(Mock(), db_model, Mock())
    ultimate_string = "ultimate update"
    with assert_raises(NoSuchHandlerError):
        runtime.handle(tester, 'test_nonexistant_fallback_handler', ultimate_string)


def test_runtime_render():
    key_store = DictKeyValueStore()
    db_model = DbModel(key_store)
    tester = TestXBlock(Mock(), db_model, Mock())
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
    tester = TestXBlockNoFallback(Mock(), db_model, Mock())
    with assert_raises(NoSuchViewError):
        runtime.render(tester, [update_string], 'test_nonexistant_view')


class SerialDefaultKVS(DictKeyValueStore):
    """
    A kvs which gives each call to default the next int (nonsensical but for testing default fn)
    """
    def __init__(self, *args, **kwargs):
        super(SerialDefaultKVS, self).__init__(*args, **kwargs)
        self.default_counter = 0

    def default(self, _key):
        self.default_counter += 1
        return self.default_counter


class TestIntegerXblock(XBlock):
    counter = Integer(scope=Scope.content)


def test_default_fn():
    key_store = SerialDefaultKVS()
    db_model = DbModel(key_store)
    tester = TestIntegerXblock(Mock(), db_model, Mock())
    tester2 = TestIntegerXblock(Mock(), db_model, Mock())

    # ensure value is not in tester before any actions
    assert_false(db_model.has(tester, 'counter'))
    # ensure value is same over successive calls for same DbModel
    first_call = tester.counter
    assert_equals(first_call, 1)
    assert_equals(first_call, tester.counter)
    # ensure the value is not saved in the object
    assert_false(db_model.has(tester, 'counter'))
    # ensure save does not save the computed default back to the object
    tester.save()
    assert_false(db_model.has(tester, 'counter'))

    # ensure second object gets another value
    second_call = tester2.counter
    assert_equals(second_call, 2)


class TestSimpleMixin(object):
    """Toy class for mixin testing"""
    field_x = List(scope=Scope.content)
    field_y = String(scope=Scope.user_state, default="default_value")

    @property
    def field_x_with_default(self):
        """
        Test method for generating programmatic default values for fields
        """
        return self.field_x or [1, 2, 3]


class FieldTester(XBlock):
    """Test XBlock for field access testing"""
    field_a = Integer(scope=Scope.settings)
    field_b = Integer(scope=Scope.content, default=10)
    field_c = Integer(scope=Scope.user_state, default='field c')


# Test that access to fields from mixins works as expected
def test_mixin_field_access():
    runtime = Runtime([TestSimpleMixin])

    field_tester = runtime.construct_block_from_class(
        FieldTester,
        DictModel({
            'field_a': 5,
            'field_x': [1, 2, 3],
        }),
        Mock(),
    )

    assert_equals(5, field_tester.field_a)
    assert_equals(10, field_tester.field_b)
    assert_equals('field c', field_tester.field_c)
    assert_equals([1, 2, 3], field_tester.field_x)
    assert_equals('default_value', field_tester.field_y)

    field_tester.field_x = ['a', 'b']
    field_tester.save()
    assert_equals(['a', 'b'], field_tester._field_data.get(field_tester, 'field_x'))

    del field_tester.field_x
    assert_equals([], field_tester.field_x)
    assert_equals([1, 2, 3], field_tester.field_x_with_default)

    with assert_raises(AttributeError):
        getattr(field_tester, 'field_z')
    with assert_raises(AttributeError):
        delattr(field_tester, 'field_z')

    field_tester.field_z = 'foo'
    assert_equals('foo', field_tester.field_z)
    assert_false(field_tester._field_data.has(field_tester, 'field_z'))


# Test that the classes generated via the mixin process are cached
# (and only generated once)
def test_only_generate_classes_once():
    runtime = Runtime([TestSimpleMixin])

    assert_is(
        runtime.construct_block_from_class(FieldTester, Mock(), Mock()).__class__,
        runtime.construct_block_from_class(FieldTester, Mock(), Mock()).__class__,
    )

    assert_is_not(
        runtime.construct_block_from_class(FieldTester, Mock(), Mock()).__class__,
        runtime.construct_block_from_class(TestXBlock, Mock(), Mock()).__class__,
    )
