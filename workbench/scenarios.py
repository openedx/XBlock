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
