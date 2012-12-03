import json
from webob import Response

from .core import XBlock, Scope, Int, Boolean, register_view, register_handler, expires, varies_on_block
from .widget import Widget

class ThumbsBlock(XBlock):

    upvotes = Int(help="Number of up votes made on this thumb", default=0, scope=Scope.content)
    downvotes = Int(help="Number of down votes made on this thumb", default=0, scope=Scope.content)
    voted = Boolean(help="Whether a student has already voted on a thumb", default=False, scope=Scope.student_state)

    @register_view('student_view')
    @varies_on_block('definition')
    @expires(seconds=5)
    def render_student(self, context):
        widget = Widget(self.runtime.render_template("upvotes.html",
            upvotes=self.upvotes,
            downvotes=self.downvotes,
        ))
        widget.add_css("""
            .upvote, .downvote {
                cursor: pointer;
                border: 1px solid #888;
                padding: 0 .5em;
            }
            .upvote { color: green; }
            .downvote { color: red; }
            """)
        widget.add_javascript("""
            function ThumbsBlock(runtime, element) {
                function update_votes(votes) {
                    $('.upvote .count', element).text(votes.up);
                    $('.downvote .count', element).text(votes.down);
                }

                var handler_url = runtime.handler_url('vote')
                $(element).bind('ajaxSend', function(elm, xhr, s) {
                    runtime.prep_xml_http_request(xhr);
                });

                $('.upvote', element).bind('click.ThumbsBlock.up', function() {
                    $.post(handler_url, JSON.stringify({vote_type: 'up'})).success(update_votes);
                });

                $('.downvote', element).bind('click.ThumbsBlock.up', function() {
                    $.post(handler_url, JSON.stringify({vote_type: 'down'})).success(update_votes);
                });
            };
            """)
        widget.initialize_js('ThumbsBlock')
        return widget

    @register_handler('vote')
    def handle_vote(self, request):
        #if self.student.voted:
        #    log.error("cheater!")
        #    return
        data = json.loads(request.body)
        if data['vote_type'] not in ('up', 'down'):
            log.error('error!')
            return

        if data['vote_type'] == 'up':
            self.upvotes += 1
        else:
            self.downvotes += 1

        self.voted = True

        return Response(
            body=json.dumps({'up': self.upvotes, 'down': self.downvotes}),
            content_type='application/json'
        )
