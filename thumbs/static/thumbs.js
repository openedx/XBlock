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
