"""Example scenarios to display in the debugger.

This code is in the Debugger layer.

"""

from collections import namedtuple

from xblock.core import XBlock
from xblock.parse import parse_xml_string
from .runtime import Usage

# Build the scenarios, which are named trees of usages.

Scenario = namedtuple("Scenario", "description usage")

SCENARIOS = []

for name, cls in XBlock.load_classes():
    default_children = [Usage("debugchild", []) for _ in xrange(3)]
    SCENARIOS.append(Scenario(name, Usage(name, default_children)))

SCENARIOS.extend([
    Scenario(
        "a bunch of html",
        Usage("html", [], {
            'content': """
                <h2>Installing Enthought for Windows</h2>

                <p>To download Enthought on your Windows machine, you should follow these steps:</p>

                <ul>
                    <li><p>Visit the <a href="http://www.enthought.com/products/epd_free.php" target="_blank">Enthought website</a>.</p></li>

                    <li><p>Click on the Download Button.</p></li>

                    <li><p>On the subsequent page, select the download file for Windows. Do NOT
                    download the 64 bit version, even if your operating system is 64-bit.</p></li>

                    <li><p>Once the file has downloaded to your system, complete the
                    installation by double-clicking the .msi file. Follow the instructions
                    to install on your machine.</p></li>

                </ul>

                <p>Once you have completed the installation, you should be ready to use
                the Python environment. To do this, follow these steps:</p>

                <ul><li><p>Find the Enthought system on your machine and open the Idle program.
                    </p><p>Click on the Start menu, then click on All Programs. Find
                    the Enthought folder in the list. Open the folder and click on Idle.</p>
                </li>
                </ul>
                """,
        }),
    ),
    Scenario(
        "problem with two inputs",
        Usage("problem", [
            Usage("textinput"),
            Usage("textinput"),
        ]),
    ),
    Scenario(
        "three thumbs at once",
        Usage("vertical", [
            Usage("thumbs", [], {'upvotes': 3, 'downvotes': 1}),
            Usage("thumbs"),
            Usage("thumbs"),
        ])
    ),
    Scenario(
        "problem with thumbs and textbox",
        Usage("problem", [
            Usage("html", [], {
                'content': """
                    <p>You have three constraints to satisfy:</p>
                    <ol>
                        <li>The upvotes and downvotes must be equal.</li>
                        <li>You must enter the number of upvotes into the text field.</li>
                        <li>The number of upvotes must be $numvotes.</li>
                    </ol>
                    """}),
            Usage("thumbs", [], {'name': 'thumb'}),
            Usage("textinput", [], {'input_type': 'int', 'name': 'vote_count'}),
            Usage("equality", [], {
                'content': 'Upvotes match downvotes',
                'name': 'votes_equal',
                'arguments': {
                    'left': './thumb/@upvotes',
                    'right': './thumb/@downvotes',
                },
            }),
            Usage("equality", [], {
                'content': 'Number of upvotes matches entered string',
                'name': 'votes_named',
                'arguments': {
                    'left': './thumb/@upvotes',
                    'right': './vote_count/@student_input',
                },
            }),
            Usage("equality", [], {
                'content': 'Number of upvotes is $numvotes',
                'name': 'votes_specified',
                'arguments': {
                    'left': './thumb/@upvotes',
                    'right': '$numvotes',
                }
            }),
        ], {
            'script': """
                # Compute the random answer.
                import random
                numvotes = random.randrange(2,5)
                """,
        }),
    ),
    Scenario(
        "problem with thumbs and textbox, from XML",
        parse_xml_string("""\
            <problem>
                <p>You have three constraints to satisfy:</p>
                <ol>
                    <li>The upvotes and downvotes must be equal.</li>
                    <li>You must enter the number of upvotes into the text field.</li>
                    <li>The number of upvotes must be $numvotes.</li>
                </ol>

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
        """, Usage),
    ),
    Scenario(
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
    Scenario(
        "three problems",
        Usage("vertical", [
            Usage("attempts_scoreboard"),
            Usage("problem", [
                Usage("html", [], {'content': "<p>What is $a+$b?</p>"}),
                Usage("textinput", [], {'input_type': 'int', 'name': 'sum_input'}),
                Usage("equality", [], {
                    'content': '',
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
                    Usage("html", [], {'content': "<p>What is $a &times; $b?</p>"}),
                    Usage("textinput", [], {'input_type': 'int', 'name': 'sum_input'}),
                    Usage("equality", [], {
                        'content': '',
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
                Usage("html", [], {'content': "<p>What is $a+$b?</p>"}),
                Usage("textinput", [], {'input_type': 'int', 'name': 'sum_input'}),
                Usage("equality", [], {
                    'content': '',
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
])

# Create all the initial states in the usages

for scenario in SCENARIOS:
    scenario.usage.store_initial_state()
