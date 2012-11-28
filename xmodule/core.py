import inspect
import json
from webob import Response
from .widget import Widget

def needs_children(fn):
    fn.needs_children = True
    return fn

def needs_settings(fn):
    return fn

def register_view(name):
    return _register_method('view', name)

def register_handler(name):
    return _register_method('handler', name)

def _register_method(registration_type, name):
    def wrapper(fn):
        setattr(fn, '_' + registration_type, name)
        return fn
    return wrapper


class Plugin(object):
    @classmethod
    def load_classes(cls):
        # This should be Plugin.load_classes
        for c in cls.__subclasses__():
            yield c.__name__, c

    @classmethod
    def load_class(cls, name):
        # This should be Plugin.load_class
        for c in cls.__subclasses__():
            if c.__name__ == name:
                return c


class MissingXModuleRegistration(Exception):
    pass

class XModule(Plugin):
    def __init__(self, runtime, db):
        self.runtime = runtime
        self.db = db

    def _find_registered_method(self, registration_type, name):
        for _, fn in inspect.getmembers(self, inspect.ismethod):
            fn_name = getattr(fn, '_' + registration_type, None)
            if fn_name == name:
                return fn
        raise MissingXModuleRegistration(self.__class__, registration_type, name)

    def handle(self, handler_name, data):
        return self._find_registered_method('handler', handler_name)(data)

    def render(self, context, view_name=None):
        if context._view_name is None:
            assert view_name, "You must provide a view name to render a tree of XModules"
            context._view_name = view_name
        else:
            view_name = context._view_name
        widget = self._find_registered_method('view', view_name)(context)
        return self.runtime.wrap_child(self, widget, context)

    @property
    def content(self):
        return self.db.query(student=False, module=ModuleScope.DEFINITION)

    @property
    def student_state(self):
        return self.db.query(student=True, module=ModuleScope.USAGE)

    @property
    def student_preferences(self):
        return self.db.query(student=True, module=ModuleScope.TYPE)

    @property
    def student_info(self):
        return self.db.query(student=True, module=ModuleScope.ALL)

    #self.settings is different

class ModuleScope(object):
    USAGE, DEFINITION, TYPE, ALL = xrange(4)

def depends_on(student=True, module=ModuleScope.USAGE, keys=None):
    """A caching decorator."""
    def _dec(f):
        cache_key = f.__name__+f.__class__.__name__
        if keys:
            val = db.query(student=student, module=module, keys=keys)
            for k in keys:
                cache_key += val[k]
        if student and not keys:
            # Student=True, no keys
            cache_key += student_id
        return f
    return _dec


def cache_for_student_demographics(name):
    return depends_on(student=True, module=ALL, keys=[name])

cache_for_all_students = depends_on(student=False)
# What other caching scopes do we need?  ModuleScope.TYPE is implied.

def noop_decorator(f):
    return f

def varies_on_id(module):
    # key = $def_id or $usage_id
    return noop_decorator

def varies_on_settings(keys):
    # key = settings[k]
    return noop_decorator

def varies_on_data(student=False, module=ModuleScope.ALL, keys=None):
    # key = db.query(s=, m=, k=)
    return noop_decorator

def varies_on_children(f):
    # This means, don't cache?
    return f

def expires(seconds):
    # cache expiration
    return noop_decorator


#-- specific modules --------

class HelloWorldModule(XModule):
    @register_view('student_view')
    def student_view(self, context):
        return Widget("Hello, world!")

class VerticalModule(XModule):

    @register_view('student_view')
    @needs_children
    def render_student(self, context):
        result = Widget()
        # TODO: self.runtime.children is actual children here, not ids...
        child_widgets = [child.render(context) for child in self.runtime.children]
        result.add_widgets_resources(child_widgets)
        result.add_content(self.runtime.render_template("vertical.html", children=child_widgets))
        return result


class ThumbsModule(XModule):

    @register_view('student_view')
    @cache_for_all_students # @depends_on(student=False)
    def render_student(self, context):
        self.content.setdefault('votes', {})
        widget = Widget(self.runtime.render_template("upvotes.html",
            upvotes=self.content['votes'].get('up', 0),
            downvotes=self.content['votes'].get('down', 0),
        ))
        widget.add_css("""
            .upvote { color: green }
            .downvote { color: red }
            """)
        widget.add_javascript("""
            function ThumbsModule(runtime, element) {
                function update_votes(votes) {
                    $('.upvote .count', element).text(votes.up);
                    $('.downvote .count', element).text(votes.down);
                }

                var handler_url = runtime.handler('vote')
                $(element).bind('ajaxSend', function(elm, xhr, s) {
                    runtime.prep_xml_http_request(xhr);
                });

                $('.upvote', element).bind('click.ThumbsModule.up', function() {
                    $.post(handler_url, JSON.stringify({vote_type: 'up'})).success(update_votes);
                });

                $('.downvote', element).bind('click.ThumbsModule.up', function() {
                    $.post(handler_url, JSON.stringify({vote_type: 'down'})).success(update_votes);
                });
            };
            """)
        widget.initialize_js('ThumbsModule')
        return widget

    @register_handler('vote')
    def handle_vote(self, data):
        #if self.student.voted:
        #    log.error("cheater!")
        #    return
        if data['vote_type'] not in ('up', 'down'):
            log.error('error!')
            return

        self.content.setdefault('votes', {})
        self.content['votes'].setdefault(data['vote_type'], 0)
        self.content['votes'][data['vote_type']] += 1
        self.student_state['voted'] = True

        return Response(body=json.dumps(self.content['votes']), content_type='application/json')
