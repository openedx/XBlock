"""Example scenarios to display in the debugger.

This code is in the Debugger layer.

"""

from collections import namedtuple

from xblock.core import XBlock
from .runtime import Usage

# Build the scenarios, which are named trees of usages.

Scenario = namedtuple("Scenario", "description usage")

SCENARIOS = []
default_children = [Usage("debugchild", "dbgdefn", []) for _ in xrange(3)]

for name, cls in XBlock.load_classes():
    SCENARIOS.append(Scenario(name, Usage(name, "defn999", default_children)))

SCENARIOS.extend([
    Scenario("a bunch of html",
        Usage("html", "x", [], {'content':"""
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
                                    """}),
    ),
    Scenario("problem with two inputs",
        Usage("problem", "x", [
            Usage("textinput", "x", []),
            Usage("textinput", "x", []),
        ]),
    ),
    Scenario("three thumbs at once",
        Usage("vertical", "x", [
            Usage("thumbs", "def1", [], {'upvotes': 3, 'downvotes': 1}),
            Usage("thumbs", "def2", []),
            Usage("thumbs", "def3", []),
        ])
    ),
    Scenario("problem with thumbs and textbox",
        Usage("problem", "p1", [
            Usage("html", "x", [], {'content': """
                                    <p>You have three constraints to satisfy:</p>
                                    <ol>
                                        <li>The upvotes and downvotes must be equal.</li>
                                        <li>You must enter the number of upvotes into the text field.</li>
                                        <li>The number of upvotes must be 3.</li>
                                    </ol>
                                    """}),
            Usage("thumbs", "x", [], {'name': 'thumb'}),
            Usage("textinput", "textin", [], {'input_type': 'int', 'name': 'vote_count'}),
            Usage("equality", "e1", [], {'message': 'Upvotes match downvotes', 'name': 'votes_equal'}),
            Usage("equality", "e2", [], {'message': 'Number of upvotes matches entered string', 'name': 'votes_named'}),
            Usage("equality", "e3", [], {'message': 'Number of upvotes is 3', 'name': 'votes_specified'}),
        ], {
            'checker_arguments': {
                'votes_equal': {
                    'left': {'_type': 'reference', 'ref_name': 'thumb.upvotes'},
                    'right': {'_type': 'reference', 'ref_name': 'thumb.downvotes'},
                },
                'votes_named': {
                    'left': {'_type': 'reference', 'ref_name': 'thumb.upvotes'},
                    'right': {'_type': 'reference', 'ref_name': 'vote_count.student_input'},
                },
                'votes_specified': {
                    'left': {'_type': 'reference', 'ref_name': 'thumb.upvotes'},
                    'right': 3,
                }
            }
        }),
    ),
    Scenario("sequence with progress_sliders",
        Usage("sequence", "s-a", [
            Usage("vertical", "v-a", [
                Usage("slider", "s-aa", []),
                Usage("progress_slider", "ps-ab", []),
            ]),
            Usage("vertical", "v-b", [
                Usage("thumbs", "t-ba", []),
                Usage("slider", "ps-bb", []),
                Usage("progress_slider", "ps-bc", []),
            ]),
            Usage("vertical", "v-c", [
                Usage("thumbs", "t-ca", []),
                Usage("slider", "ps-cb", []),
                Usage("progress_slider", "ps-cc", []),
                Usage("progress_slider", "ps-cd", []),
                Usage("progress_slider", "ps-ce", []),
            ]),
        ]),
    ),
])
