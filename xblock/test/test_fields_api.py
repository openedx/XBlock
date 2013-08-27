"""
Tests outwardly observable behaviour of fields

This test suite attempts to cover the interactions between several
orthogonal attributes that affect the behaviour of xblock fields.

1) Whether the field is mutable or immutable
2) Whether the field is in one of 3 different states
    a) The field has no stored value
        i) The default is statically defined on the field
        ii) The default is computed by the field_data
    b) The field has a stored value

In addition, all of the test cases should behave the same in the
presence of certain preceding noop operations (such as reading the
field from the block, or saving the block before any changes have
been made)

In order to make sure that all of the possible combinations have been
covered, we define sets of test properties (which actually implement the
tests of the various operations), and test setup (which set up the
particular combination of initial conditions that we want to test)
"""

import copy
from mock import Mock

# Nose dynamically defines assert_* functions
# pylint: disable=E0611
from nose.tools import assert_is, assert_is_not, assert_raises, assert_equals, assert_not_equals
# pylint: enable=E0611

from xblock.core import XBlock
from xblock.fields import Integer, List
from xblock.test.tools import DictModel

# Ignore statements that 'have no effect', since the effect is to read
# from the descriptor
# pylint: disable=W0104


# ~~~~~~~~~~~~~ Classes defining test properties ~~~~~~~~~~~~~~~~~~~~~~

# Allow base classes to leave out class attributes and that they access
# without pylint complaining
# pylint: disable=E1101
class UniversalProperties(object):
    """
    Properties that can be tested without knowing whether a field
    has an initial value or a default value

    Requires from subclasses:
        self.new_value  # The value to update the field to during testing
        self.block  # An initialized xblock with a field named `field`
        self.field_data  # The field_data used by self.block
    """

    def test_get_preserves_identity(self):
        first_get = self.block.field
        second_get = self.block.field

        assert_is(first_get, second_get)

    def test_get_with_save_preserves_identity(self):
        first_get = self.block.field
        self.block.save()
        second_get = self.block.field

        assert_is(first_get, second_get)

    def test_set_preserves_identity(self):
        first_get = self.block.field
        assert_is_not(self.new_value, first_get)
        self.block.field = self.new_value
        second_get = self.block.field

        assert_is(self.new_value, second_get)
        assert_is_not(first_get, second_get)

    def test_set_with_save_preserves_identity(self):
        first_get = self.block.field
        self.block.field = self.new_value
        self.block.save()
        second_get = self.block.field

        assert_is(self.new_value, second_get)
        assert_is_not(first_get, second_get)

    def test_delete_without_save_writes(self):
        del self.block.field
        with assert_raises(KeyError):
            self.field_data.get(self.block, 'field')

    def test_delete_with_save_writes(self):
        del self.block.field
        self.block.save()
        with assert_raises(KeyError):
            self.field_data.get(self.block, 'field')


class MutationProperties(object):
    """
    Properties of mutable fields that can be tested without knowing
    whether the field has an initial value or a default value

    Requires from subclasses:
        self.mutate(value)  # Update value in place
        self.new_value  # The value to update the field to during testing
        self.block  # An initialized xblock with a field named `field`
        self.field_data  # The field_data used by self.block
    """

    def test_set_save_get_mutate_save(self):
        reference_value = copy.deepcopy(self.new_value)
        self.mutate(reference_value)

        # Verify that the test isn't vacuously true
        assert_not_equals(self.new_value, reference_value)

        self.block.field = copy.deepcopy(self.new_value)
        self.block.save()
        self.mutate(self.block.field)
        self.block.save()
        final_value = self.field_data.get(self.block, 'field')
        assert_equals(reference_value, final_value)


class InitialValueProperties(object):
    """
    Properties dependent on the field having an initial value

    Requires from subclasses:
        self.initial_value: The initial value for the field
        self.new_value  # The value to update the field to during testing
        self.block  # An initialized xblock with a field named `field`
        self.field_data  # The field_data used by self.block
    """
    def get_field_data(self):
        """Return a new :class:`~xblock.fields.FieldData` for testing"""
        return DictModel({'field': copy.deepcopy(self.initial_value)})

    def test_get_gets_initial_value(self):
        assert_equals(self.field_data.get(self.block, 'field'), self.block.field)

    def test_get_with_save_doesnt_write(self):
        initial_value = self.field_data.get(self.block, 'field')
        self.block.field
        self.block.save()
        final_value = self.field_data.get(self.block, 'field')

        assert_equals(initial_value, final_value)

    def test_set_with_save_writes(self):
        initial_value = self.field_data.get(self.block, 'field')
        assert_is_not(self.new_value, initial_value)
        self.block.field = self.new_value
        self.block.save()
        assert_equals(self.new_value, self.field_data.get(self.block, 'field'))


class DefaultValueProperties(object):
    """
    Properties dependent on the field not having an initial value

    Requires from subclasses:
        self.new_value  # The value to update the field to during testing
        self.block  # An initialized xblock with a field named `field`
        self.field_data  # The field_data used by self.block
    """
    def test_get_with_save_doesnt_write(self):
        with assert_raises(KeyError):
            self.field_data.get(self.block, 'field')
        self.block.field
        self.block.save()
        with assert_raises(KeyError):
            self.field_data.get(self.block, 'field')

    def test_set_with_save_writes(self):
        with assert_raises(KeyError):
            self.field_data.get(self.block, 'field')
        self.block.field = self.new_value
        self.block.save()
        assert_equals(self.new_value, self.field_data.get(self.block, 'field'))

    def test_delete_without_save_succeeds(self):
        with assert_raises(KeyError):
            self.field_data.get(self.block, 'field')

        del self.block.field

        with assert_raises(KeyError):
            self.field_data.get(self.block, 'field')

    def test_delete_with_save_succeeds(self):
        del self.block.field
        self.block.save()
        with assert_raises(KeyError):
            self.field_data.get(self.block, 'field')


class DefaultValueMutationProperties(object):
    """
    Properties testing mutation of default field values

    Requires from subclasses:
        self.mutate(value)  # Update value in place
        self.block  # An initialized xblock with a field named `field`
        self.field_data  # The field_data used by self.block
    """
    def test_mutation_without_save_doesnt_write(self):
        with assert_raises(KeyError):
            self.field_data.get(self.block, 'field')

        mutable = self.block.field
        self.mutate(mutable)

        with assert_raises(KeyError):
            self.field_data.get(self.block, 'field')

    def test_mutation_with_save_writes(self):
        with assert_raises(KeyError):
            self.field_data.get(self.block, 'field')

        mutable = self.block.field
        reference_copy = copy.deepcopy(mutable)
        self.mutate(reference_copy)

        # Verify that the test isn't vacuously true
        assert_not_equals(mutable, reference_copy)

        self.mutate(mutable)
        self.block.save()

        final_value = self.field_data.get(self.block, 'field')
        assert_equals(reference_copy, final_value)


class InitialValueMutationProperties(object):
    """
    Properties testing mutation of set field value

    Requires from subclasses:
        self.mutate(value)  # Update value in place
        self.block  # An initialized xblock with a field named `field`
        self.field_data  # The field_data used by self.blocks
    """
    def test_mutation_without_save_doesnt_write(self):
        initial_value = self.field_data.get(self.block, 'field')
        reference_copy = copy.deepcopy(initial_value)

        mutable = self.block.field
        self.mutate(mutable)

        # Verify that the test isn't vacuously true
        assert_not_equals(reference_copy, mutable)

        final_value = self.field_data.get(self.block, 'field')
        assert_equals(reference_copy, final_value)
        assert_equals(initial_value, final_value)

    def test_mutation_with_save_writes(self):
        initial_value = self.field_data.get(self.block, 'field')
        reference_copy = copy.deepcopy(initial_value)
        self.mutate(reference_copy)

        # verify that the test isn't vacuously true
        assert_not_equals(initial_value, reference_copy)

        mutable = self.block.field
        self.mutate(mutable)
        self.block.save()

        final_value = self.field_data.get(self.block, 'field')
        assert_equals(reference_copy, final_value)


# ~~~~~ Classes linking initial conditions to the properties that test them ~~~~~~
class UniversalTestCases(UniversalProperties):
    """
    Test setup for testing the :class:`~xblock.fields.Field` API

    Requires from subclasses:
        self.field_class  # The class of the field to test
        self.field_default  # The static default value for the field
        self.get_field_data()  # A function that returns a new :class:`~xblock.fields.FieldData` instance
    """
    def setUp(self):
        class TestBlock(XBlock):
            """Testing block for all field API tests"""
            field = self.field_class(default=copy.deepcopy(self.field_default))

        self.field_data = self.get_field_data()
        self.block = TestBlock(Mock(), self.field_data, Mock())


class DictModelWithSequentialDefault(DictModel):
    """:class:`~xblock.test.tools.DictModel` that generates a sequence of default values"""
    def __init__(self, storage, sequence):
        super(DictModelWithSequentialDefault, self).__init__(storage)
        self._sequence = sequence

    def default(self, block, name):
        return next(self._sequence)


class StaticDefaultTestCases(UniversalTestCases, DefaultValueProperties):
    """Set up tests of static default values"""
    def get_field_data(self):
        """Return a new :class:`~xblock.fields.FieldData` for testing"""
        return DictModel({})


class ComputedDefaultTestCases(UniversalTestCases, DefaultValueProperties):
    """Set up tests of computed default values"""
    def get_field_data(self):
        """Return a new :class:`~xblock.fields.FieldData` for testing"""
        return DictModelWithSequentialDefault({}, self.default_iterator)


class ImmutableTestCases(UniversalTestCases):
    """Set up tests of an immutable field"""
    field_class = Integer
    field_default = 99
    new_value = 101


class MutableTestCases(UniversalTestCases, MutationProperties):
    """Set up tests of a mutable field"""
    field_class = List
    field_default = []
    new_value = ['a', 'b']

    def mutate(self, value):
        """Modify the supplied value"""
        value.append('foo')
# pylint: enable=E1101


# pylint: disable=C0111
class TestImmutableWithStaticDefault(ImmutableTestCases, StaticDefaultTestCases):
    pass


class TestImmutableWithInitialValue(ImmutableTestCases, InitialValueProperties):
    initial_value = 75


class TestImmutableWithComputedDefault(ImmutableTestCases, ComputedDefaultTestCases):
    @property
    def default_iterator(self):
        return iter(xrange(1000))


class TestMutableWithStaticDefault(MutableTestCases, StaticDefaultTestCases, DefaultValueMutationProperties):
    pass


class TestMutableWithInitialValue(MutableTestCases, InitialValueProperties, InitialValueMutationProperties):
    initial_value = [1, 2, 3]


class TestMutableWithComputedDefault(MutableTestCases, ComputedDefaultTestCases, DefaultValueMutationProperties):
    @property
    def default_iterator(self):
        return ([None] * i for i in xrange(1000))


# ~~~~~~~~~~~~~ Classes for testing noops before other tests ~~~~~~~~~~~~~~~~~~~~

# Allow base classes to leave out class attributes and that they access
# without pylint complaining
# pylint: disable=E1101
class GetNoopPrefix(object):
    """
    Mixin that prefixes existing field tests with a call to `self.block.field`.

    This operation is a noop which shouldn't affect whether the tests pass.

    Requires from subclasses:
        self.block  # An initialized xblock with a field named `field`
    """
    def setUp(self):
        super(GetNoopPrefix, self).setUp()
        self.block.field


class GetSaveNoopPrefix(object):
    """
    Mixin that prefixes existing field tests with a call to `self.block.field` and then `self.block.save()`

    This operation is a noop which shouldn't affect whether the tests pass.

    Requires from subclasses:
        self.block  # An initialized xblock with a field named `field`
    """
    def setUp(self):
        super(GetSaveNoopPrefix, self).setUp()
        self.block.field
        self.block.save()


class SaveNoopPrefix(object):
    """
    Mixin that prefixes existing field tests with a call to `self.block.save()`

    This operation is a noop which shouldn't affect whether the tests pass.

    Requires from subclasses:
        self.block  # An initialized xblock with a field named `field`
    """
    def setUp(self):
        super(SaveNoopPrefix, self).setUp()
        self.block.save()
# pylint: enable=E1101


for noop_prefix in (GetNoopPrefix, GetSaveNoopPrefix, SaveNoopPrefix):
    for base_test_case in (
        TestImmutableWithComputedDefault, TestImmutableWithInitialValue, TestImmutableWithStaticDefault,
        TestMutableWithComputedDefault, TestMutableWithInitialValue, TestMutableWithStaticDefault
    ):
        test_name = base_test_case.__name__ + "And" + noop_prefix.__name__
        vars()[test_name] = type(test_name, (noop_prefix, base_test_case), {})

# If we don't delete the loop variables, then they leak into the global namespace
# and cause the last class looped through to be tested twice. Surprise!
# pylint: disable=W0631
del noop_prefix
del base_test_case
