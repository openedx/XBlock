"""
This file supports the XBlock service that returns data about courses.
"""

from xblock.reference.plugins import Service


class CourseService(Service):
    """
    CourseService returns information about courses.
    """
    def __init__(self, **kwargs):
        super(CourseService, self).__init__(**kwargs)

    def get_current_course(self):
        """
        This is default, example implementation.  Anything real needs to override

        This is expected to return an instance of XBlockCourse
        """
        raise NotImplementedError()


class XBlockCourse(object):
    """
    A model representation of course data returned by the CourseService.

    This is just to tell xblock authors what fields they can expect from this service, and how to reference them
        - id
        - name
        - org
        - number

    Runtimes are not required to conform to this standard and can always
    patch attributes dynamically.
    """
    def __init__(
        self,
        id=None,
        name=None,
        org=None,
        number=None
    ):
        # Set standardized attributes
        self.id = id
        self.name = name
        self.org = org
        self.number = number
