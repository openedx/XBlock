"""An XBlock providing thumbs-up/thumbs-down voting.
"""

from xblock.core import XBlock, Scope, Integer, Boolean
from xblock.fragment import Fragment
from xblock.problem import InputBlock

import logging
log = logging.getLogger(__name__)


class ThumbsBlock(InputBlock):
    """
    An XBlock with thumbs-up/thumbs-down voting.

    Vote totals are stored for all students to see.  Each student is recorded
    as has-voted or not.

    This demonstrates multiple data scopes and ajax handlers.

    """

    upvotes = Integer(help="Number of up votes", default=0, scope=Scope.content)
    downvotes = Integer(help="Number of down votes", default=0, scope=Scope.content)
    voted = Boolean(help="Has this student voted?", default=False, scope=Scope.student_state)

    def student_view(self, context):
        frag = Fragment(u"""
            <p>
                <span class='upvote'><span class='count'>{self.upvotes}</span>&uarr;</span>
                <span class='downvote'><span class='count'>{self.downvotes}</span>&darr;</span>
            </p>
            """.format(self=self))
        frag.add_css("""
            .upvote, .downvote {
                cursor: pointer;
                border: 1px solid #888;
                padding: 0 .5em;
            }
            .upvote { color: green; }
            .downvote { color: red; }
            """)
        frag.add_javascript("""
            function ThumbsBlock(runtime, element) {
                function update_votes(votes) {
                    $('.upvote .count', element).text(votes.up);
                    $('.downvote .count', element).text(votes.down);
                }

                var handler_url = runtime.handler_url('vote');

                $('.upvote', element).bind('click.ThumbsBlock.up', function() {
                    $.post(handler_url, JSON.stringify({vote_type: 'up'})).success(update_votes);
                });

                $('.downvote', element).bind('click.ThumbsBlock.up', function() {
                    $.post(handler_url, JSON.stringify({vote_type: 'down'})).success(update_votes);
                });
            };
            """)
        frag.initialize_js('ThumbsBlock')
        return frag

    problem_view = student_view

    @XBlock.json_handler
    def vote(self, data):
        # Here is where we would prevent a student from voting twice, but then
        # we couldn't click more than once in the demo!
        #
        # if self.student.voted:
        #    log.error("cheater!")
        #    return
        if data['vote_type'] not in ('up', 'down'):
            log.error('error!')
            return

        if data['vote_type'] == 'up':
            self.upvotes += 1
        else:
            self.downvotes += 1

        self.voted = True

        return {'up': self.upvotes, 'down': self.downvotes}

    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("three thumbs at once",
            """\
                <vertical>
                    <thumbs/>
                    <thumbs/>
                    <thumbs/>
                </vertical>
             """)
        ]
