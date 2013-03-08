"""Example scenarios to display in the workbench.

This code is in the Workbench layer.

"""

from collections import namedtuple

from xblock.core import XBlock
from xblock.parse import parse_xml_string
from .runtime import Usage

# Build the scenarios, which are named trees of usages.

Scenario = namedtuple("Scenario", "description usage")

SCENARIOS = []

for name, cls in XBlock.load_classes():
    # Each XBlock class can provide scenarios to display in the workbench.
    if hasattr(cls, "workbench_scenarios"):
        for desc, xml in cls.workbench_scenarios():
            SCENARIOS.append(Scenario(desc, parse_xml_string(xml, Usage)))
    else:
        # No specific scenarios, just show it with three generic children.
        default_children = [Usage("debugchild", []) for _ in xrange(3)]
        SCENARIOS.append(Scenario(name, Usage(name, default_children)))

SCENARIOS.extend([
    Scenario(
        "a bunch of html",
        Usage("html", [], {
            'content': u"""
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
])

# Create all the initial states in the usages

for scenario in SCENARIOS:
    scenario.usage.store_initial_state()
