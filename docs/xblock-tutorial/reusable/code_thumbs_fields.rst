.. code-block:: python

    class ThumbsBlockBase(object):
        upvotes = Integer(help="Number of up votes", default=0, 
            scope=Scope.user_state_summary)
        downvotes = Integer(help="Number of down votes", default=0, 
            scope=Scope.user_state_summary)
        voted = Boolean(help="Has this student voted?", default=False, 
            scope=Scope.user_state)
