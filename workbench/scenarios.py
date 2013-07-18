"""Example scenarios to display in the workbench.

This code is in the Workbench layer.

"""

from collections import namedtuple

from xblock.core import XBlock
from xblock.parse import parse_xml_string
from .runtime import Usage

# Build the scenarios, which are named trees of usages.

Scenario = namedtuple("Scenario", "description usage")  # pylint: disable=C0103

SCENARIOS = {}

for class_name, cls in XBlock.load_classes():
    # Each XBlock class can provide scenarios to display in the workbench.
    if hasattr(cls, "workbench_scenarios"):
        for i, (desc, xml) in enumerate(cls.workbench_scenarios()):
            scname = "%s.%d" % (class_name, i)
            usage = parse_xml_string(xml, Usage)
            SCENARIOS[scname] = Scenario(desc, usage)
    else:
        # No specific scenarios, just show it with three generic children.
        default_children = [Usage("debugchild", []) for _ in xrange(3)]
        scname = "%s.0" % class_name
        usage = Usage(class_name, default_children)
        SCENARIOS[scname] = Scenario(class_name, usage)

SCENARIOS.update({
    'gettysburg': Scenario(
        "a bunch of html",
        Usage("html", [], {
            'content': u"""
                <h2>Gettysburg Address</h2>

                <p>Four score and seven years ago our fathers brought forth on
                this continent a new nation, conceived in liberty, and dedicated to
                the proposition that all men are created equal.</p>

                <p>Now we are engaged in a great civil war, testing whether
                that nation, or any nation so conceived and so dedicated, can long
                endure. We are met on a great battle-field of that war. We have
                come to dedicate a portion of that field, as a final resting place
                for those who here gave their lives that that nation might live. It
                is altogether fitting and proper that we should do this.</p>

                <p>But, in a larger sense, we can not dedicate, we can not
                consecrate, we can not hallow this ground. The brave men, living
                and dead, who struggled here, have consecrated it, far above our
                poor power to add or detract. The world will little note, nor long
                remember what we say here, but it can never forget what they did
                here. It is for us the living, rather, to be dedicated here to the
                unfinished work which they who fought here have thus far so nobly
                advanced. It is rather for us to be here dedicated to the great
                task remaining before us &mdash; that from these honored dead we
                take increased devotion to that cause for which they gave the last
                full measure of devotion &mdash; that we here highly resolve that
                these dead shall not have died in vain &mdash; that this nation,
                under God, shall have a new birth of freedom &mdash; and that
                government of the people, by the people, for the people, shall not
                perish from the earth.</p>
                """,
        }),
    ),

    'two_inputs': Scenario(
        "problem with two inputs",
        Usage("problem", [
            Usage("textinput"),
            Usage("textinput"),
        ]),
    ),

    'seq_progress': Scenario(
        "sequence with progress_sliders",
        Usage("sequence", [
            Usage("vertical", [
                Usage("slider"),
                Usage("progress_slider"),
            ]),
            Usage("vertical", [
                Usage("thumbs"),
                Usage("slider"),
                Usage("progress_slider"),
            ]),
            Usage("vertical", [
                Usage("thumbs"),
                Usage("slider"),
                Usage("progress_slider"),
                Usage("progress_slider"),
                Usage("progress_slider"),
            ]),
        ]),
    ),

    'three_problems': Scenario(
        "three problems",
        Usage("vertical", [
            Usage("attempts_scoreboard"),
            Usage("problem", [
                Usage("html", [], {'content': u"<p>What is $a+$b?</p>"}),
                Usage("textinput", [], {'input_type': 'int', 'name': 'sum_input'}),
                Usage("equality", [], {
                    'content': u'',
                    'name': 'sum_checker',
                    'arguments': {
                        'left': './sum_input/@student_input',
                        'right': '$c',
                    },
                }),
            ], {
                'script': """
                    import random
                    a = random.randint(2, 5)
                    b = random.randint(1, 4)
                    c = a + b
                    """,
            }),
            Usage("sidebar", [
                Usage("problem", [
                    Usage("html", [], {'content': u"<p>What is $a &times; $b?</p>"}),
                    Usage("textinput", [], {'input_type': 'int', 'name': 'sum_input'}),
                    Usage("equality", [], {
                        'content': u'',
                        'name': 'sum_checker',
                        'arguments': {
                            'left': './sum_input/@student_input',
                            'right': '$c',
                        },
                    }),
                ], {
                    'script': """
                        import random
                        a = random.randint(2, 6)
                        b = random.randint(3, 7)
                        c = a * b
                        """,
                }),
            ]),
            Usage("problem", [
                Usage("html", [], {'content': u"<p>What is $a+$b?</p>"}),
                Usage("textinput", [], {'input_type': 'int', 'name': 'sum_input'}),
                Usage("equality", [], {
                    'content': u'',
                    'name': 'sum_checker',
                    'arguments': {
                        'left': './sum_input/@student_input',
                        'right': '$c',
                    },
                }),
            ], {
                'script': """
                    import random
                    a = random.randint(3, 5)
                    b = random.randint(2, 6)
                    c = a + b
                    """,
            }),
        ]),
    ),
})
