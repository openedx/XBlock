from .widget import Widget




def needs_children(fn):
    return fn


def needs_settings(fn):
    return fn


def register_view(name):
    def wrapper(fn):
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
        for method_name, method_fn in inspect.getmembers(self, inspect.ismethod):
            if getattr(method_fn, 'view_name', None) == view_name:
                return method_fn
        raise MissingXModuleView(self.__class__, view_name)


class VerticalModule(XModule):

    @register_view('student')
    @needs_children
    def render_student(self, context):
        result = Widget()
        child_widgets = [self.render_child(child) for child in context.children]
        result.add_widget_resources(child_widgets)
        result.add_content(render_template("vertical.html",
            children=[w.content for w in child_widgets]
        ))


class ModuleScope(object):
    USAGE, DEFINITION, TYPE, ALL = xrange(4)

class Database(object):
    def query(self, student=True, module=ModuleScope.USAGE, keys=None):
        """Get a data object optionally scoped by `student`, `course`, and `module`."""
        return SOMETHING

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


# In the runtime, to set up the XModule:
if 0:
    self.content = self.db.query(student=False, module=ModuleScope.DEFINITION)
    self.student = self.db.query(student=True, module=ModuleScope.USAGE)
    self.preferences = self.db.query(student=True, module=ModuleScope.TYPE)
    self.student_info = self.db.query(student=True, module=ModuleScope.ALL)
    #self.settings is different

class ThumbsModule(XModule):

    @register_view('student')
    @cache_for_all_students # @depends_on(student=False)
    def render_student(self, context):
        # With named scopes:
        return Widget(render_template("upvotes.html",
            upvotes=self.content.votes.get('up', 0),
            downvotes=self.content.votes.get('down', 0),
        ))
        # Pyotr's way:
        content = self.db.query(module_id=True, module_type=False, student=False, keys=['votes'])
        return Widget(render_template("upvotes.html",
            upvotes=content.votes.get('up', 0),
            downvotes=content.votes.get('down', 0),
        ))

    @register_handler('vote')
    def handle_vote(self, context, data):
        if self.student.voted:
            log.error("cheater!")
            return
        if data['vote_type'] not in ('up', 'down'):
            log.error('error!')
            return

        self.content.votes.setdefault(data['vote_type'], 0)
        self.content.votes[data['vote_type']] += 1
        self.student.voted = True
