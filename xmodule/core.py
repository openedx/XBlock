import inspect
from .widget import Widget

def needs_children(fn):
    fn.needs_children = True
    return fn

def needs_settings(fn):
    return fn

def register_view(name):
    def wrapper(fn):
        fn.view_name = name
        return fn
    return wrapper

register_handler = register_view


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


class MissingXModuleView(Exception):
    pass

class XModule(Plugin):
    def __init__(self, runtime, db):
        self.runtime = runtime
        self.db = db

    def find_view(self, view_name):
        for name, fn in inspect.getmembers(self, inspect.ismethod):
            fn_view_name = getattr(fn, 'view_name', None)
            if fn_view_name == view_name:
                return fn
        raise MissingXModuleView(self.__class__, view_name)

    def render(self, view_name, context):
        context._view_name = view_name
        widget = self.find_view(view_name)(context)
        context._view_name = None
        return widget

    def render_child(self, child, context, view_name=None):
        view_name = view_name or context._view_name
        widget = child.find_view(view_name)(context)
        return widget

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
        child_widgets = [self.render_child(child, context) for child in self.runtime.children]
        result.add_widget_resources(child_widgets)
        result.add_content(self.runtime.render_template("vertical.html",
            children=child_widgets
        ))
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
        return widget

    @register_handler('vote')
    def handle_vote(self, context, data):
        #if self.student.voted:
        #    log.error("cheater!")
        #    return
        if data['vote_type'] not in ('up', 'down'):
            log.error('error!')
            return

        self.content.setdefault('votes', {})
        self.content['votes'].setdefault(data['vote_type'], 0)
        self.content['votes'][data['vote_type']] += 1
        self.student['voted'] = True
