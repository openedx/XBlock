"""Problem XBlock, and friends."""

import json

from .core import XBlock, register_view, register_handler, Object, Scope, List, String
from .util import call_once_property
from .widget import Widget
from webob import Response


class ProblemBlock(XBlock):

    checker_arguments = Object(help="Map of checker names to `check` arguments", scope=Scope.content, default={})
    children_names = List(help="List of names for child elements", scope=Scope.content, default=[])
    has_children = True

    # The content controls how the Inputs attach to Graders
    @register_view("student_view")
    def student_view(self, context):
        result = Widget()
        child_widgets = [self.runtime.render_child(child, context, "problem_view") for child in self.children]
        result.add_widgets_resources(child_widgets)
        result.add_content(self.runtime.render_template("problem.html",
            named_children=zip(self.children_names, child_widgets))
        )
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
    def child_name_map(self):
        return dict(zip(self.children_names, self.children))

    @register_handler("check")
    def check_answer(self, request):
        submissions = json.loads(request.body)

        for input_name, submission in submissions.items():
            self.child_name_map[input_name].submit(submission)

        results = {}
        for checker, arguments in self.checker_arguments:
            for arg_name, arg_value in arguments.items():
                if isinstance(arg_value, dict) and arg_value.get('_type') == 'reference':
                    child, _, attribute = arg_value['ref_name'].partition('.')
                    arguments[arg_name] = getattr(self.child_name_map[child], attribute)
            results[checker] = self.child_name_map[checker].check(**arguments)

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

    student_input = String(help="Last input submitted by the student", default="", scope=Scope.student_state)

    @register_view("student_view")
    def student_view(self, context):
        return Widget("<p>I can only appear inside problems.</p>")

    @register_view("problem_view")
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