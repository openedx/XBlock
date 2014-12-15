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

    This is just to tell XBlock authors what fields they can expect from this service, and how to reference them
        - course_id
        - display_name
        - org
        - number

    All of these fields will exist in an instantiated object of this class, but those fields may return None.
    """
    def __init__(self, **kwargs):
        # Set standardized attributes
        self.course_id = kwargs.get('course_id')
        self.display_name = kwargs.get('display_name')
        self.org = kwargs.get('org')
        self.number = kwargs.get('number')
