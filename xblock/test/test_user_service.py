"""
Tests for the UserService
"""
import collections
from xblock.reference.user_service import XBlockUser, UserService
from xblock.test.tools import assert_equals, assert_raises, assert_is_instance, assert_false


class SingleUserService(UserService):
    """
    This is a dummy user service for testing that always returns a single user.
    """
    def __init__(self, user):
        super(SingleUserService, self).__init__()
        self.user = user

    def get_current_user(self):
        return self.user


def test_dummy_user_service_current_user():
    """
    Tests that get_current_user() works on a dummy user service.
    """
    user = XBlockUser(full_name="tester")
    user_service = SingleUserService(user)
    current_user = user_service.get_current_user()
    assert_equals(current_user, user)
    assert_equals(current_user.full_name, "tester")
    # assert that emails is an Iterable but not a string
    assert_is_instance(current_user.emails, collections.Iterable)
    assert_false(isinstance(current_user.emails, basestring))
    # assert that opt_attrs is a Mapping
    assert_is_instance(current_user.opt_attrs, collections.Mapping)


def test_dummy_user_service_exception():
    """
    Tests NotImplemented error raised by UserService when not instantiated with kwarg get_current_user
    """
    user_service = UserService()
    with assert_raises(NotImplementedError):
        user_service.get_current_user()
