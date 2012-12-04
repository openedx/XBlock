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
    Scenario("problem with two inputs",
        Usage("problem", "x", [
            Usage("textinput", "x", []),
            Usage("textinput", "x", []),
        ]),
    ),
    Scenario("three thumbs at once",
        Usage("vertical", "x", [
            Usage("thumbs", "def1", []),
            Usage("thumbs", "def2", []),
            Usage("thumbs", "def3", []),
        ])
    ),
    Scenario("problem with thumbs and textbox",
        Usage("problem", "p1", [
            Usage("thumbs", "x", []),
            Usage("textinput", "textin", [], {'input_type': 'int'}),
            Usage("equality", "e1", [], {'message': 'Upvotes match downvotes'}),
            Usage("equality", "e2", [], {'message': 'Number of upvotes matches entered string'}),
            Usage("equality", "e3", [], {'message': 'Number of upvotes is 3'}),
        ], {
            'children_names': ['thumb', 'votecount', 'votes_equal', 'votes_named', 'votes_specified'],
            'checker_arguments': {
                'votes_equal': {
                    'left': {'_type': 'reference', 'ref_name': 'thumb.upvotes'},
                    'right': {'_type': 'reference', 'ref_name': 'thumb.downvotes'},
                },
                'votes_named': {
                    'left': {'_type': 'reference', 'ref_name': 'thumb.upvotes'},
                    'right': {'_type': 'reference', 'ref_name': 'votecount.student_input'},
                },
                'votes_specified': {
                    'left': {'_type': 'reference', 'ref_name': 'thumb.upvotes'},
                    'right': 3,
                }
            }
        }),
    ),
])
