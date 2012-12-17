"""Problem XBlock, and friends.

These implement a general mechanism for problems containing input fields
and checkers, wired together in interesting ways.

This code is in the XBlock layer.

A rough sequence diagram::

      BROWSER (Javascript)                 SERVER (Python)

    Problem    Input     Checker          Problem    Input    Checker
       |         |          |                |         |         |
       | submit()|          |                |         |         |
       +-------->|          |                |         |         |
       |<--------+  submit()|                |         |         |
       +------------------->|                |         |         |
       |<-------------------+                |         |         |
       |         |          |     "check"    |         |         |
       +------------------------------------>| submit()|         |
       |         |          |                +-------->|         |
       |         |          |                |<--------+  check()|
       |         |          |                +------------------>|
       |         |          |                |<------------------|
       |<------------------------------------+         |         |
       | handle_submit()    |                |         |         |
       +-------->| handle_check()            |         |         |
       +------------------->|                |         |         |
       |         |          |                |         |         |

"""

import json
import random
import string
import time

from webob import Response

from .core import XBlock, Int, Object, Scope, List, String, Any, Boolean
from .run_script import run_script
from .widget import Widget


class ProblemBlock(XBlock):
    """A generalized container of InputBlocks and Checkers.

    The `checker_arguments` field maps checker names to check arguments.

    """
    script = String(help="Python code to compute values", scope=Scope.content, default="")
    checker_arguments = Object(help="Map of checker names to `check` arguments", scope=Scope.content, default={})
    seed = Int(help="Random seed for this student", scope=Scope.student_state, default=0)
    attempted = Boolean(help="Has the student attempted this problem?", scope=Scope.student_state, default=False)
    has_children = True

    def set_student_seed(self):
        self.seed = int(time.clock()*10) % 100 + 1

    def calc_context(self, context):
        # If we have a script, run it.
        if self.script:
            # Seed the random number for the student so they each have different but
            # repeatable data.
            if not self.seed:
                self.set_student_seed()
            random.seed(self.seed)
            script_vals = run_script(self.script)
            context = dict(context)
            context.update(script_vals)
        return context

    # The content controls how the Inputs attach to Graders
    @XBlock.view("student_view")
    def student_view(self, context):
        context = self.calc_context(context)

        result = Widget()
        named_child_widgets = []
        for child_id in self.children:
            child = self.runtime.get_child(child_id)
            widget = self.runtime.render_child(child, context, "problem_view")
            result.add_widget_resources(widget)
            named_child_widgets.append((child.name, widget))
        result.add_css("""
            .problem {
                border: solid 1px #888; padding: 3px;
            }
            """)
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

                function handle_check_results(results) {
                    $.each(results.submit_results || {}, function(input, result) {
                        call_if_exists(runtime.child_map[input], 'handle_submit', result);
                    });
                    $.each(results.check_results || {}, function(checker, result) {
                        call_if_exists(runtime.child_map[checker], 'handle_check', result);
                    });
                }

                // To submit a problem, call all the named children's submit() 
                // function, collect their return values, and post that object
                // to the check handler.
                $(element).find('.check').bind('click', function() {
                    var data = {};
                    for (var i = 0; i < runtime.children.length; i++) {
                        var child = runtime.children[i];
                        if (child.name !== undefined) {
                            data[child.name] = call_if_exists(child, 'submit');
                        }
                    }
                    var handler_url = runtime.handler_url('check')
                    $.post(handler_url, JSON.stringify(data)).success(handle_check_results);
                });

                $(element).find('.rerandomize').bind('click', function() {
                    var handler_url = runtime.handler_url('rerandomize');
                    $.post(handler_url, JSON.stringify({}));
                });
            }
            """)
        result.initialize_js('ProblemBlock')
        return result

    @XBlock.json_handler("check")
    def check_answer(self, submissions):
        self.attempted = True
        context = self.calc_context({})

        child_map = {}
        for child_id in self.children:
            child = self.runtime.get_child(child_id)
            if child.name:
                child_map[child.name] = child

        # For each InputBlock, call the submit() method with the browser-sent 
        # input data.
        submit_results = {}
        for input_name, submission in submissions.items():
            submit_results[input_name] = child_map[input_name].submit(submission)

        # For each Checker, find the values it wants, and pass them to its
        # check() method.
        check_results = {}
        for checker, arguments in self.checker_arguments.items():
            kwargs = {}
            kwargs.update(arguments)
            for arg_name, arg_value in arguments.items():
                if isinstance(arg_value, dict):
                    _type = arg_value.get('_type')
                    if _type == 'reference':
                        child, _, attribute = arg_value['ref_name'].partition('.')
                        kwargs[arg_name] = getattr(child_map[child], attribute)
                    elif _type == 'context':
                        kwargs[arg_name] = context.get(arg_value['ref_name'])
            check_results[checker] = child_map[checker].check(**kwargs)

        return {
            'submit_results': submit_results,
            'check_results': check_results,
        }

    @XBlock.json_handler("rerandomize")
    def handle_rerandomize(self, unused):
        self.set_student_seed()
        return {'status': 'ok'}


class InputBlock(XBlock):

    def submit(self, submission):
        """
        Called with the result of the javascript Block's submit() function.
        Returns any data, which is passed to the Javascript handle_submit
        function.

        """
        pass


class CheckerBlock(XBlock):

    def check(self, **kwargs):
        """
        Called with the data provided by the ProblemBlock.
        Returns any data, which will be passed to the Javascript handle_check
        function.

        """
        pass


class TextInputBlock(InputBlock):

    input_type = String(help="Type of conversion to attempt on input string")
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


class EqualityCheckerBlock(CheckerBlock):

    left = Any(scope=Scope.student_state)
    right = Any(scope=Scope.student_state)
    attempted = Boolean(scope=Scope.student_state)
    message = String(help="Message describing the equality test", scope=Scope.content, default="Equality test")

    @XBlock.view('problem_view')
    def problem(self, context):
        correct = self.left == self.right

        # TODO: I originally named this class="data", but that conflicted with
        # the CSS on the page! :(  We might have to do something to namespace
        # things.
        # TODO: Should we have a way to spit out JSON islands full of data?
        # Note the horror of mixed Python-Javascript data below...
        message = string.Template(self.message).substitute(**context)
        result = Widget("""
            <span class="mydata" data-attempted='{self.attempted}' data-correct='{correct}'>
                {message}
                <span class='indicator'></span>
            </span>
            """.format(self=self, message=message, correct=correct)
            )
        # TODO: This is a runtime-specific URL.  But if each XBlock ships their
        # own copy of underscore.js, we won't be able to uniquify them.
        # Perhaps runtimes can offer a palette of popular libraries so that
        # XBlocks can refer to them in XBlock-standard ways?
        result.add_javascript_url("/static/js/vendor/underscore-min.js")

        # TODO: I need a way to add a script tag with a different mimetype to
        # the head.  There's no widget way to do that yet.
        result.add_content("""
            <script type="text/template" id="xblock-equality-template">
                <% if (attempted !== "True") { %>
                    (Not attempted)
                <% } else { %>
                    <img src="/resource/debugger/images/<%= (correct === "True") ? "correct" : "incorrect" %>-icon.png">
                <% } %>
            </script>
            """)

        result.add_javascript("""
            function EqualityCheckerBlock(runtime, element) {
                var template = _.template($("#xblock-equality-template").html());
                function render() {
                    var data = $("span.mydata", element).data();
                    $("span.indicator", element).html(template(data));
                }
                render();
                return {
                    handle_check: function(result) {
                        $("span.mydata", element)
                              .data("correct", result ? "True" : "False")
                              .data("attempted", "True");
                        render();
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
