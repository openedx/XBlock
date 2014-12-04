"""
Tests for the CourseService
"""
from xblock.reference.course_service import XBlockCourse, CourseService
from xblock.test.tools import assert_equals, assert_raises


class SingleCourseService(CourseService):
    """
    This is a dummy course service for testing that always returns a single course.
    """
    def __init__(self, course):
        super(SingleCourseService, self).__init__()
        self.course = course

    def get_current_course(self):
        return self.course


def test_dummy_course_service_current_course():
    """
    Tests that get_current_course() works on a dummy course service.
    """
    course = XBlockCourse(course_id="tester")
    course_service = SingleCourseService(course)
    current_course = course_service.get_current_course()
    assert_equals(current_course, course)
    assert_equals(current_course.course_id, "tester")


def test_dummy_course_service_exception():
    """
    Tests NotImplemented error raised by CourseService when not instantiated with kwarg get_current_course
    """
    course_service = CourseService()
    with assert_raises(NotImplementedError):
        course_service.get_current_course()
