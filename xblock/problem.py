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

import inspect
import random
import string  # pylint: disable=W0402
import time

from xblock.core import XBlock
from xblock.fields import Integer, Scope, String, Any, Boolean, Dict
from xblock.run_script import run_script
from xblock.fragment import Fragment


class ProblemBlock(XBlock):
    """A generalized container of InputBlocks and Checkers.

    """
    script = String(help="Python code to compute values", scope=Scope.content, default="")
    seed = Integer(help="Random seed for this student", scope=Scope.user_state, default=0)
    problem_attempted = Boolean(help="Has the student attempted this problem?", scope=Scope.user_state, default=False)
    has_children = True

    @classmethod
    def parse_xml(cls, node, runtime, keys):
        block = runtime.construct_xblock_from_class(cls, keys)

        # Find <script> children, turn them into script content.
        for child in node:
            if child.tag == "script":
                block.script += child.text
            else:
                block.runtime.add_node_as_child(block, child)

        return block

    def set_student_seed(self):
        """Set a random seed for the student so they each have different but repeatable data."""
        # Don't return zero, that's the default, and the sign that we should make a new seed.
        self.seed = int(time.time() * 1000) % 100 + 1

    def calc_context(self, context):
        """If we have a script, run it, and return the resulting context."""
        if self.script:
            # Seed the random number for the student
            if not self.seed:
                self.set_student_seed()
            random.seed(self.seed)
            script_vals = run_script(self.script)
            context = dict(context)
            context.update(script_vals)
        return context

    # The content controls how the Inputs attach to Graders
    def student_view(self, context=None):
        """Provide the default student view."""
        if context is None:
            context = {}

        context = self.calc_context(context)

        result = Fragment()
        named_child_frags = []
        # self.children is an attribute obtained from ChildrenModelMetaclass, so disable the
        # static pylint checking warning about this.
        for child_id in self.children:  # pylint: disable=E1101
            child = self.runtime.get_block(child_id)
            frag = self.runtime.render_child(child, "problem_view", context)
            result.add_frag_resources(frag)
            named_child_frags.append((child.name, frag))
        result.add_css("""
            .problem {
                border: solid 1px #888; padding: 3px;
            }
            """)
        result.add_content(self.runtime.render_template(
            "problem.html",
            named_children=named_child_frags
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

    @XBlock.json_handler
    def check(self, submissions):
        """
        Processess the `submissions` with each provided Checker.

        First calls the submit() method on each InputBlock. Then, for each Checker,
        finds the values it needs and passes them to the appropriate `check()` method.

        Returns a dictionary of 'submit_results': {input_name: user_submitted_results},
        'check_results': {checker_name: results_passed_through_checker}

        """
        self.problem_attempted = True
        context = self.calc_context({})

        child_map = {}
        # self.children is an attribute obtained from ChildrenModelMetaclass, so disable the
        # static pylint checking warning about this.
        for child_id in self.children:  # pylint: disable=E1101
            child = self.runtime.get_block(child_id)
            if child.name:
                child_map[child.name] = child

        # For each InputBlock, call the submit() method with the browser-sent
        # input data.
        submit_results = {}
        for input_name, submission in submissions.items():
            child = child_map[input_name]
            submit_results[input_name] = child.submit(submission)
            child.save()

        # For each Checker, find the values it wants, and pass them to its
        # check() method.
        checkers = list(self.runtime.querypath(self, "./checker"))
        check_results = {}
        for checker in checkers:
            arguments = checker.arguments
            kwargs = {}
            kwargs.update(arguments)
            for arg_name, arg_value in arguments.items():
                if arg_value.startswith("."):
                    values = list(self.runtime.querypath(self, arg_value))
                    # TODO: What is the specific promised semantic of the iterability
                    # of the value returned by querypath?
                    kwargs[arg_name] = values[0]
                elif arg_value.startswith("$"):
                    kwargs[arg_name] = context.get(arg_value[1:])
                elif arg_value.startswith("="):
                    kwargs[arg_name] = int(arg_value[1:])
                else:
                    raise ValueError("Couldn't interpret checker argument: %r" % arg_value)
            result = checker.check(**kwargs)
            if checker.name:
                check_results[checker.name] = result

        return {
            'submit_results': submit_results,
            'check_results': check_results,
        }

    @XBlock.json_handler
    def rerandomize(self, unused):
        """Set a new random seed for the student."""
        self.set_student_seed()
        return {'status': 'ok'}

    @staticmethod
    def workbench_scenarios():
        """A few canned scenarios for display in the workbench."""
        return [
            ("problem with thumbs and textbox",
             """\
                <problem>
                    <html>
                        <p>You have three constraints to satisfy:</p>
                        <ol>
                            <li>The upvotes and downvotes must be equal.</li>
                            <li>You must enter the number of upvotes into the text field.</li>
                            <li>The number of upvotes must be $numvotes.</li>
                        </ol>
                    </html>

                    <thumbs name='thumb'/>
                    <textinput name='vote_count' input_type='int'/>

                    <script>
                        # Compute the random answer.
                        import random
                        numvotes = random.randrange(2,5)
                    </script>
                    <equality name='votes_equal' left='./thumb/@upvotes' right='./thumb/@downvotes'>
                        Upvotes match downvotes
                    </equality>
                    <equality name='votes_named' left='./thumb/@upvotes' right='./vote_count/@student_input'>
                        Number of upvotes matches entered string
                    </equality>
                    <equality name='votes_specified' left='./thumb/@upvotes' right='$numvotes'>
                        Number of upvotes is $numvotes
                    </equality>
                </problem>
             """),

            ("three problems 2",
             """
                <vertical>
                    <attempts_scoreboard/>
                    <problem>
                        <html><p>What is $a+$b?</p></html>
                        <textinput name="sum_input" input_type="int" />
                        <equality name="sum_checker" left="./sum_input/@student_input" right="$c" />
                        <script>
                            import random
                            a = random.randint(2, 5)
                            b = random.randint(1, 4)
                            c = a + b
                        </script>
                    </problem>

                    <sidebar>
                        <problem>
                            <html><p>What is $a &#215; $b?</p></html>
                            <textinput name="sum_input" input_type="int" />
                            <equality name="sum_checker" left="./sum_input/@student_input" right="$c" />
                            <script>
                                import random
                                a = random.randint(2, 6)
                                b = random.randint(3, 7)
                                c = a * b
                            </script>
                        </problem>
                    </sidebar>

                    <problem>
                        <html><p>What is $a+$b?</p></html>
                        <textinput name="sum_input" input_type="int" />
                        <equality name="sum_checker" left="./sum_input/@student_input" right="$c" />
                        <script>
                            import random
                            a = random.randint(3, 5)
                            b = random.randint(2, 6)
                            c = a + b
                        </script>
                    </problem>
                </vertical>
             """),
        ]


class InputBlock(XBlock):
    """Base class for blocks that accept inputs.

    """
    def submit(self, submission):
        """
        Called with the result of the javascript Block's submit() function.
        Returns any data, which is passed to the Javascript handle_submit
        function.

        """
        pass


@XBlock.tag("checker")
class CheckerBlock(XBlock):
    """Base class for blocks that check answers.

    """
    arguments = Dict(help="The arguments expected by `check`")

    def set_arguments_from_xml(self, node):
        """
        Set the `arguments` field from XML attributes based on `check` arguments.
        """
        # Introspect the .check() method, and collect arguments it expects.
        argspec = inspect.getargspec(self.check)
        arguments = {}
        for arg in argspec.args[1:]:
            arguments[arg] = node.attrib.pop(arg)
        self.arguments = arguments

    @classmethod
    def parse_xml(cls, node, runtime, keys):
        """
        Parse the XML for a checker. A few arguments are handled specially,
        then the rest get the usual treatment.
        """
        block = super(CheckerBlock, cls).parse_xml(node, runtime, keys)
        block.set_arguments_from_xml(node)
        return block

    def check(self, **kwargs):
        """
        Called with the data provided by the ProblemBlock.
        Returns any data, which will be passed to the Javascript handle_check
        function.

        """
        raise NotImplementedError()


class TextInputBlock(InputBlock):
    """An XBlock that accepts text input."""

    input_type = String(help="Type of conversion to attempt on input string")
    student_input = Any(help="Last input submitted by the student", default="", scope=Scope.user_state)

    def student_view(self, context=None):  # pylint: disable=W0613
        """Returns default student view."""
        return Fragment(u"<p>I can only appear inside problems.</p>")

    def problem_view(self, context=None):  # pylint: disable=W0613
        """Returns a view of the problem - a javascript text input field."""
        html = u"<input type='text' name='input' value='{0}'><span class='message'></span>".format(self.student_input)
        result = Fragment(html)
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
    """An XBlock that checks the equality of two student data fields."""

    # Content: the problem will hook us up with our data.
    content = String(help="Message describing the equality test", scope=Scope.content, default="Equality test")

    # Student data
    left = Any(scope=Scope.user_state)
    right = Any(scope=Scope.user_state)
    attempted = Boolean(scope=Scope.user_state)

    def problem_view(self, context=None):
        """Renders the problem view.

        The view is specific to whether or not this problem was attempted, and, if so,
        if it was answered correctly.

        """
        correct = self.left == self.right

        # TODO: I originally named this class="data", but that conflicted with
        # the CSS on the page! :(  We might have to do something to namespace
        # things.
        # TODO: Should we have a way to spit out JSON islands full of data?
        # Note the horror of mixed Python-Javascript data below...
        content = string.Template(self.content).substitute(**context)
        result = Fragment(u"""
            <span class="mydata" data-attempted='{self.attempted}' data-correct='{correct}'>
                {content}
                <span class='indicator'></span>
            </span>
            """.format(self=self, content=content, correct=correct)
        )
        # TODO: This is a runtime-specific URL.  But if each XBlock ships their
        # own copy of underscore.js, we won't be able to uniquify them.
        # Perhaps runtimes can offer a palette of popular libraries so that
        # XBlocks can refer to them in XBlock-standard ways?
        result.add_javascript_url("/static/js/vendor/underscore-min.js")

        # TODO: The image tag here needs a magic URL, not a hard-coded one.
        result.add_resource(u"""
            <script type="text/template" id="xblock-equality-template">
                <% if (attempted !== "True") { %>
                    (Not attempted)
                <% } else { %>
                    <img src="/resource/workbench/images/<%= (correct === "True") ? "correct" : "incorrect" %>-icon.png">
                <% } %>
            </script>
            """, "text/html")

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

    def check(self, left, right):  # pylint: disable=W0221
        self.attempted = True
        self.left = left
        self.right = right
        return left == right


class AttemptsScoreboardBlock(XBlock):
    """
    Show attempts on problems in my nieces.
    """

    def student_view(self, context=None):  # pylint: disable=W0613
        """Provide default student view."""
        # Get the attempts for all problems in my parent.
        if self.parent:
            # these two lines are equivalent, and both work:
            attempts = list(self.runtime.query(self).parent().descendants().attr("problem_attempted"))
            attempts = list(self.runtime.querypath(self, "..//@problem_attempted"))
            num_problems = len(attempts)
            attempted = sum(attempts)
            if num_problems == 0:
                content = u"There are no problems here..."
            elif attempted == num_problems:
                content = u"Great! You attempted all %d problems!" % num_problems
            else:
                content = u"Hmm, you've only tried %d out of %d problems..." % (attempted, num_problems)
        else:
            content = u"I have nothing to live for! :("
        return Fragment(content)
