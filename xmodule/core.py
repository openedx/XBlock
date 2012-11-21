


class ModuleScope(object):
    id, type = xrange(2)


def scope(name, by_student=True, by_course=True, by_module=ModuleScope.id, attr=None, attrs=None):
    def wrapper(fn):
        return fn
    return wrapper


def requires_children(fn):
    return fn


def register_view(name):
    def wrapper(fn):
        return fn
    return wrapper

register_handler = register_view


class Widget(object):
    pass


class XModule(object):
    pass


class VerticalModule(XModule):

    @register_view('student')
    @requires_children
    def render_student(self, context):
        result = Widget()
        child_widgets = [self.render_child(child) for child in context.children]
        result.add_widget_resources(child_widgets)
        result.add_content(render_template("vertical.html",
            children=[w.content for w in child_widgets]
        ))


class ThumbsModule(XModule):

    votes_scope = scope('votes', by_student=False, attr='votes')

    @register_view('student')
    @votes_scope
    def render_student(self, context):
        return Widget(render_template("upvotes.html",
            upvotes=context.votes['up'],
            downvotes=context.votes['down'],
        ))

    @register_handler('vote')
    @votes_scope
    def handle_vote(self, context, data):
        if data['vote_type'] not in ('up', 'down'):
            log.error('error!')
            return

        context.votes[data['vote_type']] += 1

