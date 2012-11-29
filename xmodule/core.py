import inspect
import json
from collections import namedtuple
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


class ModuleScope(object):
    USAGE, DEFINITION, TYPE, ALL = xrange(4)


class Scope(namedtuple('ScopeBase', 'student module')):
    pass

Scope.content = Scope(student=True, module=ModuleScope.DEFINITION)
Scope.student_state = Scope(student=True, module=ModuleScope.USAGE)
Scope.student_preferencs = Scope(student=True, module=ModuleScope.TYPE)
Scope.student_info = Scope(student=True, module=ModuleScope.ALL)
Scope.settings = object()
Scope.children = object()



class ModelType(object):
    sequence = 0

    def __init__(self, help=None, default=None, scope=Scope.content):
        self._seq = self.sequence
        self._name = "unknown"
        self.help = help
        self.default = default
        self.scope = scope
        ModelType.sequence += 1

    @property
    def name(self):
        return self._name

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self._name)

    def __lt__(self, other):
        return self._seq < other._seq


class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        fields = []
        for n, v in attrs.items():
            if isinstance(v, ModelType):
                v._name = n
                fields.append(v)
        fields.sort()
        attrs['fields'] = fields
        return super(ModelMetaclass, cls).__new__(cls, name, bases, attrs)


class ModelBase(object):
    __metaclass__ = ModelMetaclass

Int = Float = Boolean = ModelType

class Children(ModelType):
    def __init__(self, help="A list of all XModule children of this module"):
        super(Children, self).__init__(help=help, default=[], scope=Scope.children)



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

def varies_on_model(attrs):
    # key = (getattr(self, attr) for attr in attrs)
    return noop_decorator

def expires(seconds):
    # cache expiration
    return noop_decorator

# -- Base Module
class XModule(Plugin):

    class Model(ModelBase):
        pass

    def __init__(self, runtime, model):
        self.runtime = runtime
        self.model = model

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

    def __getattr__(self, name):
        if name in self.__dict__.setdefault('model', {}):
            return self.__dict__['model'][name]

        raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))

    def __setattr__(self, name, value):
        if name in self.__dict__.setdefault('model', {}):
            self.__dict__['model'][name] = value

        self.__dict__[name] = value


#-- specific modules --------

class HelloWorldModule(XModule):
    @register_view('student_view')
    def student_view(self, context):
        return Widget("Hello, world!")

class VerticalModule(XModule):

    class Model(ModelBase):
        children = Children()

    @register_view('student_view')
    @needs_children
    def render_student(self, context):
        result = Widget()
        # TODO: self.runtime.children is actual children here, not ids...
        child_widgets = [child.render(context) for child in self.children]
        result.add_widgets_resources(child_widgets)
        result.add_content(self.runtime.render_template("vertical.html", children=child_widgets))
        return result


class ThumbsModule(XModule):

    class Model(ModelBase):
        upvotes = Int(help="Number of up votes made on this thumb", default=0, scope=Scope.content)
        downvotes = Int(help="Number of down votes made on this thumb", default=0, scope=Scope.content)
        voted = Boolean(help="Whether a student has already voted on a thumb", default=False, scope=Scope.student_state)

    @register_view('student_view')
    @cache_for_all_students # @depends_on(student=False)
    def render_student(self, context):
        widget = Widget(self.runtime.render_template("upvotes.html",
            upvotes=self.upvotes,
            downvotes=self.downvotes,
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

        if data['vote_type'] == 'up':
            self.upvotes += 1
        else:
            self.downvotes += 1

        self.voted = True

        return Response(
            body=json.dumps({'up': self.upvotes, 'down': self.downvotes}),
            content_type='application/json'
        )
