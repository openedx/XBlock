function ThumbsBlock(runtime, element) {
    function update_votes(votes) {
        $('.upvote .count', element).text(votes.up);
        $('.downvote .count', element).text(votes.down);
    }

    var handler_url = runtime.handler_url('vote');

    $('.upvote', element).click(function(eventObject) {
        $.ajax({type: "POST",
                url: handler_url,
                data: JSON.stringify({vote_type: 'up'}),
                success: update_votes});
    });

    $('.downvote', element).click(function(eventObject) {
        $.ajax({type: "POST",
                url: handler_url,
                data: JSON.stringify({vote_type: 'down'}),
                success: update_votes});
    });
};
