"""Problem XBlock, and friends."""

import json

from .core import XBlock, Object, Scope, List, String, Any
from .widget import Widget
from webob import Response


class ProblemBlock(XBlock):

    checker_arguments = Object(help="Map of checker names to `check` arguments", scope=Scope.content, default={})
    has_children = True

    # The content controls how the Inputs attach to Graders
    @XBlock.view("student_view")
    def student_view(self, context):
        result = Widget()
        named_child_widgets = [
            (child.name, self.runtime.render_child(child, context, "problem_view"))
            for child
            in self.children
        ]
        result.add_widgets_resources(widget for _, widget in named_child_widgets)
        result.add_content(self.runtime.render_template("problem.html",
            named_children=named_child_widgets
        ))
        result.add_javascript("""
            function ProblemBlock(runtime, element) {

                function call_if_exists(obj, fn) {
                    if (typeof obj[fn] == 'function') {
                        return obj[fn].apply(obj, Array.prototype.slice.call(arguments, 2));
                    } else {
                        return undefined;
                    }
                }

                var handler_url = runtime.handler_url('check')
                $(element).bind('ajaxSend', function(elm, xhr, s) {
                    runtime.prep_xml_http_request(xhr);
                });

                function handle_check_results(results) {
                    $.each(results.submit_results || {}, function(input, result) {
                        call_if_exists(runtime.child_map[input], 'handle_submit', result);
                    });
                    $.each(results.check_results || {}, function(checker, result) {
                        call_if_exists(runtime.child_map[checker], 'handle_check', result);
                    });
                }

                $(element).find('.check').bind('click', function() {
                    var data = {};
                    for (var i = 0; i < runtime.children.length; i++) {
                        var child = runtime.children[i];
                        if (child.name !== undefined) {
                            data[child.name] = call_if_exists(child, 'submit');
                        }
                    }
                    $.post(handler_url, JSON.stringify(data)).success(handle_check_results);
                });
            }
            """)
        result.initialize_js('ProblemBlock')
        return result

    @XBlock.json_handler("check")
    def check_answer(self, submissions):
        submit_results = {}
        for input_name, submission in submissions.items():
            submit_results[input_name] = self.child_map[input_name].submit(submission)

        check_results = {}
        for checker, arguments in self.checker_arguments.items():
            kwargs = {}
            kwargs.update(arguments)
            for arg_name, arg_value in arguments.items():
                if isinstance(arg_value, dict) and arg_value.get('_type') == 'reference':
                    child, _, attribute = arg_value['ref_name'].partition('.')
                    kwargs[arg_name] = getattr(self.child_map[child], attribute)
            check_results[checker] = self.child_map[checker].check(**kwargs)

        return {
            'submit_results': submit_results,
            'check_results': check_results,
        }


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
        result = Widget("<input type='text' name='input' value='%s'><span class='message'></span>" % self.student_input)
        result.add_javascript("""
            function TextInputBlock(runtime, element) {
                return {
                    submit: function() {
                        return $(element).find(':input').serializeArray();
                    },
                    handle_submit: function(result) {
                        $(element).find('.message').text((result || {}).error || '');
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
                return {'error': '"%s" is not an integer' % self.student_input}
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

        result = Widget("<span>%s: <span class='value'>%s</span></span>" % (self.message, correct))

        result.add_javascript("""
            function EqualityCheckerBlock(runtime, element) {
                return {
                    handle_check: function(result) {
                        $(element).find('.value').text(result ? 'True' : 'False');
                    }
                }
            }
            """)

        result.initialize_js('EqualityCheckerBlock')
        return result


    def check(self, left, right):
        self.attempted = True
        self.left = left
        self.right = right
        return left == right
