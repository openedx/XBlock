"""
This file supports the XBlock service that returns data about users.
"""

from xblock.reference.plugins import Service


class UserService(Service):
    """
    UserService returns information about users.  Initially only data about the currently-logged-in user.

    This service returns personally-identifiable information (PII).
    """
    def get_current_user(self):
        """
        This is default, example implementation.  Anything real needs to override

        This is expected to return an instance of XBlockUser
        """
        raise NotImplementedError()


class XBlockUser(object):
    """
    A model representation of user data returned by the UserService.

    This is just to tell XBlock authors what fields they can expect from this service, and how to reference them
        - is_authenticated
        - email
        - full_name
        - username
        - user_id
    All of these fields will exist in an instantiated object of this class, but those fields may return None.
    Also, all of this data can be considered personally-identifiable information (PII).
    """
    def __init__(self, **kwargs):
        # Set standardized attributes
        self.is_authenticated = kwargs.get('is_authenticated')
        self.email = kwargs.get('email')
        self.full_name = kwargs.get('full_name')
        self.username = kwargs.get('username')
        self.user_id = kwargs.get('user_id')
