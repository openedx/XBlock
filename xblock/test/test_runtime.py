# -*- coding: utf-8 -*-
"""Tests the features of xblock/runtime"""
# Allow tests to access private members of classes
# pylint: disable=W0212

from collections import namedtuple
from datetime import datetime
from mock import Mock, patch
from unittest import TestCase

from web_fragments.fragment import Fragment
from xblock.core import XBlock, XBlockMixin
from xblock.fields import BlockScope, Scope, String, ScopeIds, List, UserScope, Integer
from xblock.exceptions import (
    NoSuchDefinition,
    NoSuchHandlerError,
    NoSuchServiceError,
    NoSuchUsage,
    NoSuchViewError,
    FieldDataDeprecationWarning,
)
from xblock.runtime import (
    DictKeyValueStore,
    IdReader,
    KeyValueStore,
    KvsFieldData,
    Mixologist,
    ObjectAggregator,
)
from xblock.field_data import DictFieldData, FieldData

from xblock.test.tools import (
    assert_equals, assert_false, assert_true, assert_raises,
    assert_raises_regexp, assert_is, assert_is_not, assert_in, unabc,
    WarningTestMixin, TestRuntime
)


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

    def handler_without_correct_decoration(self, request, suffix=''):
        """a handler which is missing the @XBlock.handler decoration."""
        pass


class TestXBlock(TestXBlockNoFallback):
    """
    Test xblock class with fallback methods
    """
    @XBlock.handler
    def existing_handler(self, request, suffix=''):  # pylint: disable=unused-argument
        """ an existing handler to be used """
        self.user_state = request
        return "I am the existing test handler"

    @XBlock.handler
    def fallback_handler(self, handler_name, request, suffix=''):  # pylint: disable=unused-argument
        """ test fallback handler """
        self.user_state = request
        if handler_name == 'test_fallback_handler':
            return "I have been handled"
        if handler_name == 'handler_without_correct_decoration':
            return "gone to fallback"

    def student_view(self, context):
        """ an existing view to be used """
        self.preferences = context[0]
        return Fragment(self.preferences)

    def fallback_view(self, view_name, context):
        """ test fallback view """
        self.preferences = context[0]
        if view_name == 'test_fallback_view':
            return Fragment(self.preferences)
        else:
            return Fragment(u"{} default".format(view_name))


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
    field_data = KvsFieldData(key_store)
    runtime = TestRuntime(Mock(), mixins=[TestMixin], services={'field-data': field_data})
    tester = runtime.construct_xblock_from_class(TestXBlock, ScopeIds('s0', 'TestXBlock', 'd0', 'u0'))

    assert_false(field_data.has(tester, 'not a field'))

    for field in tester.fields.values():
        new_value = 'new ' + field.name
        assert_false(field_data.has(tester, field.name))
        if isinstance(field, List):
            new_value = [new_value]
        setattr(tester, field.name, new_value)

    # Write out the values
    tester.save()

    # Make sure everything saved correctly
    for field in tester.fields.values():
        assert_true(field_data.has(tester, field.name))

    def get_key_value(scope, user_id, block_scope_id, field_name):
        """Gets the value, from `key_store`, of a Key with the given values."""
        new_key = KeyValueStore.Key(scope, user_id, block_scope_id, field_name)
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
    assert_equals(
        'new mixin_by_type',
        get_key_value(Scope(UserScope.NONE, BlockScope.TYPE), None, 'TestXBlock', 'mixin_by_type')
    )
    assert_equals(
        'new mixin_for_all',
        get_key_value(Scope(UserScope.NONE, BlockScope.ALL), None, None, 'mixin_for_all')
    )
    assert_equals(
        'new mixin_user_def',
        get_key_value(Scope(UserScope.ONE, BlockScope.DEFINITION), 's0', 'd0', 'mixin_user_def')
    )
    assert_equals(
        'new mixin_agg_global',
        get_key_value(Scope(UserScope.ALL, BlockScope.ALL), None, None, 'mixin_agg_global')
    )
    assert_equals(
        'new mixin_agg_type',
        get_key_value(Scope(UserScope.ALL, BlockScope.TYPE), None, 'TestXBlock', 'mixin_agg_type')
    )
    assert_equals(
        'new mixin_agg_def',
        get_key_value(Scope(UserScope.ALL, BlockScope.DEFINITION), None, 'd0', 'mixin_agg_def')
    )
    assert_equals('new mixin_agg_usage', get_key_value(Scope.user_state_summary, None, 'u0', 'mixin_agg_usage'))


@unabc("{} shouldn't be used in tests")
class MockRuntimeForQuerying(TestRuntime):
    """Mock out a runtime for querypath_parsing test"""
    # unabc doesn't squash pylint errors
    # pylint: disable=abstract-method
    def __init__(self, **kwargs):
        self.mock_query = Mock()
        super(MockRuntimeForQuerying, self).__init__(**kwargs)

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
    field_data = KvsFieldData(key_store)
    runtime = TestRuntime(services={'field-data': field_data})
    tester = TestXBlock(runtime, scope_ids=Mock(spec=ScopeIds))
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

    # request to use a handler which doesn't have XBlock.handler decoration
    # should use the fallback
    new_update_string = "new update"
    assert_equals(runtime.handle(tester, 'handler_without_correct_decoration', new_update_string),
                  'gone to fallback')
    assert_equals(tester.user_state, new_update_string)

    # handler can't be found & no fallback handler supplied, should throw an exception
    tester = TestXBlockNoFallback(runtime, scope_ids=Mock(spec=ScopeIds))
    ultimate_string = "ultimate update"
    with assert_raises(NoSuchHandlerError):
        runtime.handle(tester, 'test_nonexistant_fallback_handler', ultimate_string)

    # request to use a handler which doesn't have XBlock.handler decoration
    # and no fallback should raise NoSuchHandlerError
    with assert_raises(NoSuchHandlerError):
        runtime.handle(tester, 'handler_without_correct_decoration', 'handled')


def test_runtime_render():
    key_store = DictKeyValueStore()
    field_data = KvsFieldData(key_store)
    runtime = MockRuntimeForQuerying(services={'field-data': field_data})
    block_type = 'test'
    def_id = runtime.id_generator.create_definition(block_type)
    usage_id = runtime.id_generator.create_usage(def_id)
    tester = TestXBlock(runtime, scope_ids=ScopeIds('user', block_type, def_id, usage_id))
    # string we want to update using the handler
    update_string = u"user state update"

    # test against the student view
    frag = runtime.render(tester, 'student_view', [update_string])
    assert_in(update_string, frag.body_html())
    assert_equals(tester.preferences, update_string)

    # test against the fallback view
    update_string = u"new update"
    frag = runtime.render(tester, 'test_fallback_view', [update_string])
    assert_in(update_string, frag.body_html())
    assert_equals(tester.preferences, update_string)

    # test block-first
    update_string = u"penultimate update"
    frag = tester.render('student_view', [update_string])
    assert_in(update_string, frag.body_html())
    assert_equals(tester.preferences, update_string)

    # test against the no-fallback XBlock
    update_string = u"ultimate update"
    tester = TestXBlockNoFallback(Mock(), scope_ids=Mock(spec=ScopeIds))
    with assert_raises(NoSuchViewError):
        runtime.render(tester, 'test_nonexistent_view', [update_string])


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
    """
    XBlock with an integer field, for testing.
    """
    counter = Integer(scope=Scope.content)


def test_default_fn():
    key_store = SerialDefaultKVS()
    field_data = KvsFieldData(key_store)
    runtime = TestRuntime(services={'field-data': field_data})
    tester = TestIntegerXblock(runtime, scope_ids=Mock(spec=ScopeIds))
    tester2 = TestIntegerXblock(runtime, scope_ids=Mock(spec=ScopeIds))

    # ensure value is not in tester before any actions
    assert_false(field_data.has(tester, 'counter'))
    # ensure value is same over successive calls for same DbModel
    first_call = tester.counter
    assert_equals(first_call, 1)
    assert_equals(first_call, tester.counter)
    # ensure the value is not saved in the object
    assert_false(field_data.has(tester, 'counter'))
    # ensure save does not save the computed default back to the object
    tester.save()
    assert_false(field_data.has(tester, 'counter'))

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
    field_c = Integer(scope=Scope.user_state, default=42)


# Test that access to fields from mixins works as expected
def test_mixin_field_access():
    field_data = DictFieldData({
        'field_a': 5,
        'field_x': [1, 2, 3],
    })
    runtime = TestRuntime(Mock(), mixins=[TestSimpleMixin], services={'field-data': field_data})

    field_tester = runtime.construct_xblock_from_class(FieldTester, Mock())

    assert_equals(5, field_tester.field_a)
    assert_equals(10, field_tester.field_b)
    assert_equals(42, field_tester.field_c)
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


class Dynamic(object):
    """
    Object for testing that sets attrs based on __init__ kwargs
    """
    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)


class TestObjectAggregator(object):
    """
    Test that the ObjectAggregator behaves correctly
    """
    def setUp(self):
        # Create some objects that only have single attributes
        self.first = Dynamic(first=1)
        self.second = Dynamic(second=2)
        self.agg = ObjectAggregator(self.first, self.second)

    def test_get(self):
        assert_equals(1, self.agg.first)
        assert_equals(2, self.agg.second)
        assert_false(hasattr(self.agg, 'other'))
        with assert_raises(AttributeError):
            self.agg.other  # pylint: disable=W0104

    def test_set(self):
        assert_equals(1, self.agg.first)
        self.agg.first = 10
        assert_equals(10, self.agg.first)
        assert_equals(10, self.first.first)  # pylint: disable=E1101

        with assert_raises(AttributeError):
            self.agg.other = 99
        assert_false(hasattr(self.first, 'other'))
        assert_false(hasattr(self.second, 'other'))

    def test_delete(self):
        assert_equals(1, self.agg.first)
        del self.agg.first
        assert_false(hasattr(self.first, 'first'))
        with assert_raises(AttributeError):
            self.agg.first  # pylint: disable=W0104

        with assert_raises(AttributeError):
            del self.agg.other


class FirstMixin(XBlockMixin):
    """Test class for mixin ordering."""
    number = 1
    field = Integer(default=1)


class SecondMixin(XBlockMixin):
    """Test class for mixin ordering."""
    number = 2
    field = Integer(default=2)


class ThirdMixin(XBlockMixin):
    """Test class for mixin ordering."""
    field = Integer(default=3)


class TestMixologist(object):
    """Test that the Mixologist class behaves correctly."""
    def setUp(self):
        self.mixologist = Mixologist([FirstMixin, SecondMixin])

    # Test that the classes generated by the mixologist are cached
    # (and only generated once)
    def test_only_generate_classes_once(self):
        assert_is(
            self.mixologist.mix(FieldTester),
            self.mixologist.mix(FieldTester),
        )

        assert_is_not(
            self.mixologist.mix(FieldTester),
            self.mixologist.mix(TestXBlock),
        )

    # Test that mixins are applied in order
    def test_mixin_order(self):
        assert_is(1, self.mixologist.mix(FieldTester).number)
        assert_is(1, self.mixologist.mix(FieldTester).fields['field'].default)

    def test_unmixed_class(self):
        assert_is(FieldTester, self.mixologist.mix(FieldTester).unmixed_class)

    def test_mixin_fields(self):
        assert_is(FirstMixin.fields['field'], FirstMixin.field)

    def test_mixed_fields(self):
        mixed = self.mixologist.mix(FieldTester)
        assert_is(mixed.fields['field'], FirstMixin.field)
        assert_is(mixed.fields['field_a'], FieldTester.field_a)

    def test_duplicate_mixins(self):
        singly_mixed = self.mixologist.mix(FieldTester)
        doubly_mixed = self.mixologist.mix(singly_mixed)
        assert_is(singly_mixed, doubly_mixed)
        assert_is(FieldTester, singly_mixed.unmixed_class)

    def test_multiply_mixed(self):
        mixalot = Mixologist([ThirdMixin, FirstMixin])

        pre_mixed = mixalot.mix(self.mixologist.mix(FieldTester))
        post_mixed = self.mixologist.mix(mixalot.mix(FieldTester))

        assert_is(pre_mixed.fields['field'], FirstMixin.field)
        assert_is(post_mixed.fields['field'], ThirdMixin.field)

        assert_is(FieldTester, pre_mixed.unmixed_class)
        assert_is(FieldTester, post_mixed.unmixed_class)

        assert_equals(4, len(pre_mixed.__bases__))  # 1 for the original class + 3 mixin classes
        assert_equals(4, len(post_mixed.__bases__))


@XBlock.needs("i18n", "no_such_service")
@XBlock.wants("secret_service", "another_not_service")
class XBlockWithServices(XBlock):
    """
    Test XBlock class with service declarations.
    """
    def student_view(self, _context):
        """Try out some services."""
        # i18n is available, and works.
        def assert_equals_unicode(str1, str2):
            """`str1` equals `str2`, and both are Unicode strings."""
            assert_equals(str1, str2)
            assert isinstance(str1, unicode)
            assert isinstance(str2, unicode)

        i18n = self.runtime.service(self, "i18n")
        assert_equals_unicode(u"Welcome!", i18n.ugettext("Welcome!"))

        assert_equals_unicode(u"Plural", i18n.ungettext("Singular", "Plural", 0))
        assert_equals_unicode(u"Singular", i18n.ungettext("Singular", "Plural", 1))
        assert_equals_unicode(u"Plural", i18n.ungettext("Singular", "Plural", 2))

        when = datetime(2013, 2, 14, 22, 30, 17)
        assert_equals_unicode(u"2013-02-14", i18n.strftime(when, "%Y-%m-%d"))
        assert_equals_unicode(u"Feb 14, 2013", i18n.strftime(when, "SHORT_DATE"))
        assert_equals_unicode(u"Thursday, February 14, 2013", i18n.strftime(when, "LONG_DATE"))
        assert_equals_unicode(u"Feb 14, 2013 at 22:30", i18n.strftime(when, "DATE_TIME"))
        assert_equals_unicode(u"10:30:17 PM", i18n.strftime(when, "TIME"))

        # secret_service is available.
        assert_equals(self.runtime.service(self, "secret_service"), 17)

        # no_such_service is not available, and raises an exception, because we
        # said we needed it.
        with assert_raises_regexp(NoSuchServiceError, "is not available"):
            self.runtime.service(self, "no_such_service")

        # another_not_service is not available, and returns None, because we
        # didn't need it, we only wanted it.
        assert_is(self.runtime.service(self, "another_not_service"), None)
        return Fragment()


def test_service():
    runtime = TestRuntime(services={
        'secret_service': 17,
        'field-data': DictFieldData({}),
    })
    block_type = 'test'
    def_id = runtime.id_generator.create_definition(block_type)
    usage_id = runtime.id_generator.create_usage(def_id)
    tester = XBlockWithServices(runtime, scope_ids=ScopeIds('user', block_type, def_id, usage_id))

    # Call the student_view to run its assertions.
    runtime.render(tester, 'student_view')


def test_ugettext_calls():
    """
    Test ugettext calls in xblock.
    """
    runtime = TestRuntime()
    block = XBlockWithServices(runtime, scope_ids=Mock(spec=[]))
    assert_equals(block.ugettext('test'), u'test')
    assert_true(isinstance(block.ugettext('test'), unicode))

    # NoSuchServiceError exception should raise if i18n is none/empty.
    runtime = TestRuntime(services={
        'i18n': None
    })
    block = XBlockWithServices(runtime, scope_ids=Mock(spec=[]))
    with assert_raises(NoSuchServiceError):
        block.ugettext('test')


@XBlock.needs("no_such_service_sub")
@XBlock.wants("another_not_service_sub")
class SubXBlockWithServices(XBlockWithServices):
    """
    Test that subclasses can use services declared on the parent.
    """
    def student_view(self, context):
        """Try the services."""
        # First, call the super class, its assertions should still pass.
        super(SubXBlockWithServices, self).student_view(context)

        # no_such_service_sub is not available, and raises an exception,
        # because we said we needed it.
        with assert_raises_regexp(NoSuchServiceError, "is not available"):
            self.runtime.service(self, "no_such_service_sub")

        # another_not_service_sub is not available, and returns None,
        # because we didn't need it, we only wanted it.
        assert_is(self.runtime.service(self, "another_not_service_sub"), None)
        return Fragment()


def test_sub_service():
    runtime = TestRuntime(id_reader=Mock(), services={
        'secret_service': 17,
        'field-data': DictFieldData({}),
    })
    tester = SubXBlockWithServices(runtime, scope_ids=Mock(spec=ScopeIds))

    # Call the student_view to run its assertions.
    runtime.render(tester, 'student_view')


class TestRuntimeGetBlock(TestCase):
    """
    Test the get_block default method on Runtime.
    """
    def setUp(self):
        patcher = patch.object(TestRuntime, 'construct_xblock')
        self.construct_block = patcher.start()
        self.addCleanup(patcher.stop)

        self.id_reader = Mock(IdReader)
        self.user_id = Mock()
        self.field_data = Mock(FieldData)
        self.runtime = TestRuntime(self.id_reader, services={'field-data': self.field_data})
        self.runtime.user_id = self.user_id

        self.usage_id = 'usage_id'

        # Can only get a definition id from the id_reader
        self.def_id = self.id_reader.get_definition_id.return_value

        # Can only get a block type from the id_reader
        self.block_type = self.id_reader.get_block_type.return_value

    def test_basic(self):
        self.runtime.get_block(self.usage_id)

        self.id_reader.get_definition_id.assert_called_with(self.usage_id)
        self.id_reader.get_block_type.assert_called_with(self.def_id)
        self.construct_block.assert_called_with(
            self.block_type,
            ScopeIds(self.user_id, self.block_type, self.def_id, self.usage_id),
            for_parent=None,
        )

    def test_missing_usage(self):
        self.id_reader.get_definition_id.side_effect = NoSuchUsage
        with self.assertRaises(NoSuchUsage):
            self.runtime.get_block(self.usage_id)

    def test_missing_definition(self):
        self.id_reader.get_block_type.side_effect = NoSuchDefinition

        # If we don't have a definition, then the usage doesn't exist
        with self.assertRaises(NoSuchUsage):
            self.runtime.get_block(self.usage_id)


class TestRuntimeDeprecation(WarningTestMixin, TestCase):
    """
    Tests to make sure that deprecated Runtime apis stay usable,
    but raise warnings.
    """

    def test_passed_field_data(self):
        field_data = Mock(spec=FieldData)
        with self.assertWarns(FieldDataDeprecationWarning):
            runtime = TestRuntime(Mock(spec=IdReader), field_data)
        with self.assertWarns(FieldDataDeprecationWarning):
            self.assertEquals(runtime.field_data, field_data)

    def test_set_field_data(self):
        field_data = Mock(spec=FieldData)
        runtime = TestRuntime(Mock(spec=IdReader), None)
        with self.assertWarns(FieldDataDeprecationWarning):
            runtime.field_data = field_data
        with self.assertWarns(FieldDataDeprecationWarning):
            self.assertEquals(runtime.field_data, field_data)
