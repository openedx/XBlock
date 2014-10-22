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
3) Whether we are using the block first vs field first versions of the
   accessors (block.field vs field.read_from(block))

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

from xblock.core import XBlock
from xblock.fields import Integer, List
from xblock.field_data import DictFieldData

from xblock.test.tools import assert_is, assert_is_not, assert_equals, assert_not_equals, assert_true, assert_false

# Ignore statements that 'have no effect', since the effect is to read
# from the descriptor
# pylint: disable=W0104


# Allow base classes to leave out class attributes and that they access
# without pylint complaining
# pylint: disable=E1101
# ~~~~~~~~~~~~~ Classes defining test operations ~~~~~~~~~~~~~~~~~~~~~~
class BlockFirstOperations(object):
    """
    Defines operations using the block-first implementations

    Requires from subclasses:
        self.block  # An xblock to operate on, which has a field `field`
    """

    def get(self):
        """Retrieve the field from the block"""
        return self.block.field

    def set(self, value):
        """Set the field on the block"""
        self.block.field = value

    def delete(self):
        """Unset the field from the block"""
        del self.block.field

    def is_default(self):
        """Return if the field is set on the block"""
        return not self.block.__class__.field.is_set_on(self.block)


class FieldFirstOperations(object):
    """
    Defines operations using the field-first implementations

    Requires from subclasses:
        self.block  # An xblock to operate on, which has a field `field`
    """

    def get(self):
        """Retrieve the field from the block"""
        return self.block.__class__.field.read_from(self.block)

    def set(self, value):
        """Set the field on the block"""
        self.block.__class__.field.write_to(self.block, value)

    def delete(self):
        """Unset the field from the block"""
        self.block.__class__.field.delete_from(self.block)

    def is_default(self):
        """Return if the field is set on the block"""
        return not self.block.__class__.field.is_set_on(self.block)


# ~~~~~~~~~~~~~ Classes defining test properties ~~~~~~~~~~~~~~~~~~~~~~
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
        first_get = self.get()
        second_get = self.get()

        assert_is(first_get, second_get)

    def test_get_with_save_preserves_identity(self):
        first_get = self.get()
        self.block.save()
        second_get = self.get()

        assert_is(first_get, second_get)

    def test_set_preserves_identity(self):
        first_get = self.get()
        assert_is_not(self.new_value, first_get)
        self.set(self.new_value)
        second_get = self.get()

        assert_is(self.new_value, second_get)
        assert_is_not(first_get, second_get)

    def test_set_with_save_preserves_identity(self):
        first_get = self.get()
        self.set(self.new_value)
        self.block.save()
        second_get = self.get()

        assert_is(self.new_value, second_get)
        assert_is_not(first_get, second_get)

    def test_set_with_save_makes_non_default(self):
        self.set(self.new_value)
        self.block.save()
        assert_false(self.is_default())

    def test_set_without_save_makes_non_default(self):
        self.set(self.new_value)
        assert_false(self.is_default())

    def test_delete_without_save_writes(self):
        self.delete()
        assert_false(self.field_data.has(self.block, 'field'))
        assert_true(self.is_default())

    def test_delete_with_save_writes(self):
        self.delete()
        self.block.save()
        if self.persist_default:
            assert self.field_data.has(self.block, 'field')
        else:
            assert_false(self.field_data.has(self.block, 'field'))
            assert_true(self.is_default())


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

        self.set(copy.deepcopy(self.new_value))
        self.block.save()
        self.mutate(self.get())
        self.block.save()
        final_value = self.field_data.get(self.block, 'field')
        assert_equals(reference_value, final_value)

    def test_mutation_with_save_makes_non_default(self):
        self.mutate(self.get())
        self.block.save()
        assert_false(self.is_default())

    def test_mutation_without_save_makes_non_default(self):
        self.mutate(self.get())
        assert_false(self.is_default())


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
        """Return a new :class:`~xblock.field_data.FieldData` for testing"""
        return DictFieldData({'field': copy.deepcopy(self.initial_value)})

    def test_get_gets_initial_value(self):
        assert_equals(self.field_data.get(self.block, 'field'), self.get())

    def test_get_with_save_doesnt_write(self):
        initial_value = self.field_data.get(self.block, 'field')
        self.get()
        self.block.save()
        final_value = self.field_data.get(self.block, 'field')

        assert_equals(initial_value, final_value)

    def test_set_with_save_writes(self):
        initial_value = self.field_data.get(self.block, 'field')
        assert_is_not(self.new_value, initial_value)
        self.set(self.new_value)
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
        assert_false(self.field_data.has(self.block, 'field'))
        self.get()
        self.block.save()
        assert_equals(self.persist_default, self.field_data.has(self.block, 'field'))

    def test_set_with_save_writes(self):
        assert_false(self.field_data.has(self.block, 'field'))
        self.set(self.new_value)
        self.block.save()
        assert_equals(self.new_value, self.field_data.get(self.block, 'field'))

    def test_delete_without_save_succeeds(self):
        assert_false(self.field_data.has(self.block, 'field'))
        self.delete()
        assert_false(self.field_data.has(self.block, 'field'))

    def test_delete_with_save_succeeds(self):
        self.delete()
        self.block.save()
        assert_equals(self.persist_default, self.field_data.has(self.block, 'field'))


class DefaultValueMutationProperties(object):
    """
    Properties testing mutation of default field values

    Requires from subclasses:
        self.mutate(value)  # Update value in place
        self.block  # An initialized xblock with a field named `field`
        self.field_data  # The field_data used by self.block
    """
    def test_mutation_without_save_doesnt_write(self):
        assert_false(self.field_data.has(self.block, 'field'))

        mutable = self.get()
        self.mutate(mutable)

        assert_false(self.field_data.has(self.block, 'field'))

    def test_mutation_with_save_writes(self):
        assert_false(self.field_data.has(self.block, 'field'))

        mutable = self.get()
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

        mutable = self.get()
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

        mutable = self.get()
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
        self.field_default  # The default value for the field
        self.get_field_data()  # A function that returns a new :class:`~xblock.field_data.FieldData` instance
    """
    def setUp(self):
        class TestBlock(XBlock):
            """Testing block for all field API tests"""
            field = self.field_class(default=copy.deepcopy(self.field_default),
                                     persist_default=self.persist_default)

        self.field_data = self.get_field_data()
        self.block = TestBlock(Mock(), self.field_data, Mock())


class DictFieldDataWithSequentialDefault(DictFieldData):
    """:class:`~xblock.test.tools.DictFieldData` that generates a sequence of default values"""
    def __init__(self, storage, sequence):
        super(DictFieldDataWithSequentialDefault, self).__init__(storage)
        self._sequence = sequence

    def default(self, block, name):
        return next(self._sequence)


class StaticFieldDataDefaultTestCases(UniversalTestCases, DefaultValueProperties):
    """Set up tests of static default values"""
    def get_field_data(self):
        """Return a new :class:`~xblock.field_data.FieldData` for testing"""
        return DictFieldData({})


class ComputedFieldDataDefaultTestCases(UniversalTestCases, DefaultValueProperties):
    """Set up tests of computed default values"""
    def get_field_data(self):
        """Return a new :class:`~xblock.field_data.FieldData` for testing"""
        return DictFieldDataWithSequentialDefault({}, self.default_iterator)


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
class TestImmutableWithStaticFieldDataDefault(ImmutableTestCases, StaticFieldDataDefaultTestCases):
    __test__ = False


class TestImmutableWithInitialValue(ImmutableTestCases, InitialValueProperties):
    __test__ = False
    initial_value = 75


class TestImmutableWithComputedFieldDataDefault(ImmutableTestCases, ComputedFieldDataDefaultTestCases):
    __test__ = False

    @property
    def default_iterator(self):
        return iter(xrange(1000))


class TestMutableWithStaticFieldDataDefault(MutableTestCases, StaticFieldDataDefaultTestCases, DefaultValueMutationProperties):
    __test__ = False


class TestMutableWithInitialValue(MutableTestCases, InitialValueProperties, InitialValueMutationProperties):
    __test__ = False
    initial_value = [1, 2, 3]


class TestMutableWithComputedFieldDataDefault(MutableTestCases, ComputedFieldDataDefaultTestCases, DefaultValueMutationProperties):
    __test__ = False

    @property
    def default_iterator(self):
        return ([None] * i for i in xrange(1000))


class TestImmutableWithCallableDefault(TestImmutableWithStaticFieldDataDefault):
    __test__ = False

    @property
    def field_default(self):
        sequence = iter(xrange(1000))
        return lambda: next(sequence)


class TestMutableWithCallableDefault(TestImmutableWithStaticFieldDataDefault):
    __test__ = False

    @property
    def field_default(self):
        sequence = ([None] * i for i in iter(xrange(1000)))
        return lambda: next(sequence)


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
        self.get()


class GetSaveNoopPrefix(object):
    """
    Mixin that prefixes existing field tests with a call to `self.block.field` and then `self.block.save()`

    This operation is a noop which shouldn't affect whether the tests pass.

    Requires from subclasses:
        self.block  # An initialized xblock with a field named `field`
    """
    def setUp(self):
        super(GetSaveNoopPrefix, self).setUp()
        self.get()
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

for operation_backend in (BlockFirstOperations, FieldFirstOperations):
    for persist_default in (False, True):
        for noop_prefix in (None, GetNoopPrefix, GetSaveNoopPrefix, SaveNoopPrefix):
            for base_test_case in (TestImmutableWithComputedFieldDataDefault, TestImmutableWithInitialValue,
                                   TestImmutableWithStaticFieldDataDefault, TestMutableWithComputedFieldDataDefault,
                                   TestMutableWithInitialValue, TestMutableWithStaticFieldDataDefault,
                                   TestImmutableWithCallableDefault, TestMutableWithCallableDefault):

                test_name = base_test_case.__name__ + "With" + operation_backend.__name__
                test_classes = (operation_backend, base_test_case)
                if persist_default:
                    test_name += "AndPersistDefault"
                if not persist_default and noop_prefix is not None:
                    test_name += "And" + noop_prefix.__name__
                    test_classes = (noop_prefix, ) + test_classes

                vars()[test_name] = type(test_name, test_classes, {'__test__': True,
                                                                   'persist_default': persist_default})

# If we don't delete the loop variables, then they leak into the global namespace
# and cause the last class looped through to be tested twice. Surprise!
# pylint: disable=W0631
del operation_backend
del noop_prefix
del base_test_case
del persist_default
