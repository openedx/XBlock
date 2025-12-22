"""
Test Scorable block.
"""

# pylint: disable=protected-access
from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import Mock

import ddt
from pytz import UTC

from xblock import scorable


class StubScorableBlock(scorable.ScorableXBlockMixin):
    """
    A very simple scorable block that needs no backing
    """
    location = 'Here'

    _scoring_error = False
    _allows_rescore = None

    def __init__(self, initial):
        self.result = initial
        self.runtime = Mock()

    def allows_rescore(self):
        if self._allows_rescore is not None:
            return self._allows_rescore
        else:
            return super().allows_rescore()

    def has_submitted_answer(self):
        return self.get_score() is not None

    def get_score(self):
        return self.result

    def set_score(self, score):
        self.result = score

    def calculate_score(self):
        if self._scoring_error:
            raise RuntimeError('Whoops')  # Any error will do

        return scorable.Score(raw_earned=1.6, raw_possible=2.0)


@ddt.ddt
class RescoreTestCase(TestCase):
    """
    Test scorable block behavior
    """
    @ddt.data(True, False)
    def test_basic(self, only_if_higher):
        block = StubScorableBlock(scorable.Score(raw_earned=2.0, raw_possible=2.0))
        block.rescore(only_if_higher=only_if_higher)

        # The new score is published to the grade infrastructure with
        # only_if_higher set appropriately.
        block.runtime.publish.assert_called_with(
            block,
            'grade',
            {
                'value': 1.6,
                'max_value': 2.0,
                'only_if_higher': only_if_higher,
            }
        )

    def test_not_yet_scored(self):
        block = StubScorableBlock(None)
        with self.assertRaises(ValueError):
            block.rescore(only_if_higher=False)

    def test_disallow_rescore(self):
        block = StubScorableBlock(scorable.Score(raw_earned=0.0, raw_possible=1.0))
        block._allows_rescore = False
        with self.assertRaises(TypeError):
            block.rescore(only_if_higher=False)

    def test_scoring_error(self):
        block = StubScorableBlock(scorable.Score(raw_earned=0.0, raw_possible=1.0))
        block._scoring_error = True
        with self.assertRaises(RuntimeError):
            block.rescore(only_if_higher=False)


@ddt.ddt
class ShowCorrectnessTest(TestCase):
    """
    Tests the correctness_available method
    """

    def setUp(self):
        super().setUp()

        now = datetime.now(UTC)
        day_delta = timedelta(days=1)
        self.yesterday = now - day_delta
        self.today = now
        self.tomorrow = now + day_delta

    def test_show_correctness_default(self):
        """
        Test that correctness is visible by default.
        """
        assert scorable.ShowCorrectness.correctness_available()

    @ddt.data(
        (scorable.ShowCorrectness.ALWAYS, True),
        (scorable.ShowCorrectness.ALWAYS, False),
        # Any non-constant values behave like "always"
        ("", True),
        ("", False),
        ("other-value", True),
        ("other-value", False),
    )
    @ddt.unpack
    def test_show_correctness_always(self, show_correctness, has_staff_access):
        """
        Test that correctness is visible when show_correctness is turned on.
        """
        assert scorable.ShowCorrectness.correctness_available(
            show_correctness=show_correctness, has_staff_access=has_staff_access
        )

    @ddt.data(True, False)
    def test_show_correctness_never(self, has_staff_access):
        """
        Test that show_correctness="never" hides correctness from learners and course staff.
        """
        assert not scorable.ShowCorrectness.correctness_available(
            show_correctness=scorable.ShowCorrectness.NEVER, has_staff_access=has_staff_access
        )

    @ddt.data(
        # Correctness not visible to learners if due date in the future
        ("tomorrow", False, False),
        # Correctness is visible to learners if due date in the past
        ("yesterday", False, True),
        # Correctness is visible to learners if due date in the past (just)
        ("today", False, True),
        # Correctness is visible to learners if there is no due date
        (None, False, True),
        # Correctness is visible to staff if due date in the future
        ("tomorrow", True, True),
        # Correctness is visible to staff if due date in the past
        ("yesterday", True, True),
        # Correctness is visible to staff if there is no due date
        (None, True, True),
    )
    @ddt.unpack
    def test_show_correctness_past_due(self, due_date_str, has_staff_access, expected_result):
        """
        Test show_correctness="past_due" to ensure:
        * correctness is always visible to course staff
        * correctness is always visible to everyone if there is no due date
        * correctness is visible to learners after the due date, when there is a due date.
        """
        if due_date_str is None:
            due_date = None
        else:
            due_date = getattr(self, due_date_str)
        assert (
            scorable.ShowCorrectness.correctness_available(
                scorable.ShowCorrectness.PAST_DUE, due_date, has_staff_access
            ) == expected_result
        )

    @ddt.data(True, False)
    def test_show_correctness_never_but_include_grade(self, has_staff_access):
        """
        Test that show_correctness="never_but_include_grade" hides correctness from learners and course staff.
        """
        assert not scorable.ShowCorrectness.correctness_available(
            show_correctness=scorable.ShowCorrectness.NEVER_BUT_INCLUDE_GRADE, has_staff_access=has_staff_access
        )
