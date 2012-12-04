"""Problem XBlock, and friends."""

import json

from .core import XBlock, Object, Scope, List, String, Any
from .util import call_once_property
from .widget import Widget
from webob import Response


class ProblemBlock(XBlock):

    checker_arguments = Object(help="Map of checker names to `check` arguments", scope=Scope.content, default={})
    children_names = List(help="List of names for child elements", scope=Scope.content, default=[])
    has_children = True

    # The content controls how the Inputs attach to Graders
    @XBlock.view("student_view")
    def student_view(self, context):
        if self.children_names is None:
            self.children_names = ["unnamed_child_%d" % idx for idx in range(len(self.children))]
        result = Widget()
        named_child_widgets = [
            (name, self.runtime.render_child(child, context, "problem_view"))
            for name, child
            in self.named_children
        ]
        result.add_widgets_resources(widget for _, widget in named_child_widgets)
        result.add_content(self.runtime.render_template("problem.html",
            named_children=named_child_widgets
        ))
        result.add_javascript("""
            function ProblemBlock(runtime, element) {

                var handler_url = runtime.handler_url('check')
                $(element).bind('ajaxSend', function(elm, xhr, s) {
                    runtime.prep_xml_http_request(xhr);
                });

                function update_checkers() {}

                $(element).find('.check').bind('click', function() {
                    var data = {};
                    for (var i = 0; i < runtime.children.length; i++) {
                        var child = runtime.children[i];
                        var name = $(child.element).closest('.problem-child').data('name');
                        if (typeof child.submit == 'function') {
                            data[name] = runtime.children[i].submit();
                        } else {
                            data[name] = null;
                        }
                    }
                    $.post(handler_url, JSON.stringify(data)).success(update_checkers);
                });
            }
            """)
        result.initialize_js('ProblemBlock')
        return result

    @call_once_property
    def named_children(self):
        names = self.children_names + ["unnamed_child_%d" % idx for idx in range(len(self.children) - len(self.children_names))]

        return zip(names, self.children)

    @call_once_property
    def child_name_map(self):
        return dict(self.named_children)

    @XBlock.handler("check")
    def check_answer(self, request):
        submissions = json.loads(request.body)

        for input_name, submission in submissions.items():
            self.child_name_map[input_name].submit(submission)

        results = {}
        for checker, arguments in self.checker_arguments.items():
            kwargs = {}
            kwargs.update(arguments)
            for arg_name, arg_value in arguments.items():
                if isinstance(arg_value, dict) and arg_value.get('_type') == 'reference':
                    child, _, attribute = arg_value['ref_name'].partition('.')
                    kwargs[arg_name] = getattr(self.child_name_map[child], attribute)
            results[checker] = self.child_name_map[checker].check(**kwargs)

        return Response(json.dumps(results))


class InputBlock(XBlock):

    def submit(self, submission):
        """
        Called with the result of the javascript Block's submit() function.
        """
        pass

class CheckerBlock(XBlock):
    pass


class TextInputBlock(InputBlock):

    input_type = String(help="Type of input string")
    student_input = String(help="Last input submitted by the student", default="", scope=Scope.student_state)

    @XBlock.view("student_view")
    def student_view(self, context):
        return Widget("<p>I can only appear inside problems.</p>")

    @XBlock.view("problem_view")
    def problem_view(self, context):
        result = Widget("<input type='text' name='input' value='%s'>" % self.student_input)
        result.add_javascript("""
            function TextInputBlock(runtime, element) {
                return {
                    submit: function() {
                        return $(element).find(':input').serializeArray();
                    }
                }
            }
            """)
        result.initialize_js('TextInputBlock')
        return result

    def submit(self, submission):
        self.student_input = submission[0]['value']
        if self.input_type == 'int':
            try:
                self.student_input = int(submission[0]['value'])
            except ValueError:
                pass

class EqualityCheckerBlock(CheckerBlock):

    left = Any(scope=Scope.student_state)
    right = Any(scope=Scope.student_state)
    attempted = Any(scope=Scope.student_state)
    message = String(help="Message describing the equality test", scope=Scope.content, default="Equality test")

    @XBlock.view('problem_view')
    def problem(self, context):
        if not self.attempted:
            correct = "Not attempted"
        else:
            correct = self.left == self.right

        return Widget("<span>%s: %s</span>" % (self.message, correct))


    def check(self, left, right):
        self.attempted = True
        self.left = left
        self.right = right
        return left == right
