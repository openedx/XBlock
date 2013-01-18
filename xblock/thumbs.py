"""An XBlock providing thumbs-up/thumbs-down voting.

This code is in the XBlock layer.

"""

import json
from webob import Response

from .core import XBlock, Scope, Integer, Boolean, expires, varies_on_block
from .fragment import Fragment
from .problem import InputBlock

import logging
log = logging.getLogger(__name__)


class ThumbsBlock(InputBlock):
    """
    An XBlock with thumbs-up/thumbs-down voting.

    Vote totals are stored for all students to see.  Each student is recorded
    as has-voted or not.

    This demonstrates multiple data scopes and ajax handlers.

    """

    upvotes = Integer(help="Number of up votes made on this thumb", default=0, scope=Scope.content)
    downvotes = Integer(help="Number of down votes made on this thumb", default=0, scope=Scope.content)
    voted = Boolean(help="Whether a student has already voted on a thumb", default=False, scope=Scope.student_state)

    @varies_on_block('definition')
    @expires(seconds=5)
    def student_view(self, context):
        frag = Fragment(self.runtime.render_template(
            "upvotes.html",
            upvotes=self.upvotes,
            downvotes=self.downvotes,
        ))
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
