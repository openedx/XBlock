"""
This module defines CompletableXBlockMixin and completion mode enumeration.
"""
from __future__ import absolute_import, unicode_literals

class XBlockCompletionMode(object):
    """
    Enumeration for completion modes.
    """
    COMPLETABLE = "completable"
    AGGREGATOR = "aggregator"
    EXCLUDED = "excluded"


class CompletableXBlockMixin(object):
    """
    This mixin sets attributes and provides helper method to integrate XBlock with Completion API.
    """

    has_custom_completion = True
    completion_method = XBlockCompletionMode.COMPLETABLE

    # Completion_percent is somewhat misleading name - as it is actually a ratio. But this is how edx-platform calls it,
    # so use the same name here for consistency
    # https://github.com/edx/XBlock/pull/368#discussion_r146560619
    def emit_completion(self, completion_percent):
        """
        Emits completion event through Completion API.

        Unlike grading API, calling this method allows completion to go down - i.e. emitting a value of 0.0 on
        a previously completed block indicates that it is no longer considered complete.

        Arguments:
            completion_percent (float): Completion in range [0.0; 1.0] (inclusive), where 0.0 means the block
            is not completed, 1.0 means the block is fully completed.

        Returns:
            None
        """
        if not self.has_custom_completion or self.completion_method != 'completable':
            raise AttributeError(
                "Using `emit_completion` requires `has_custom_completion == True` (was {}) "
                "and `completion_method == 'completable'` (was {})".format(
                    self.has_custom_completion, self.completion_method
                )
            )

        if completion_percent is None or not 0.0 <= completion_percent <= 1.0:
            raise ValueError("Completion ratio must be in [0.0; 1.0] interval, {} given".format(completion_percent))

        self.runtime.publish(
            self,
            'completion',
            {'completion': completion_percent},
        )
