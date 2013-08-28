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

def add_xml_scenario(scname, description, xml):
    """
    Add a scenario defined in XML.
    """
    assert scname not in SCENARIOS
    usage = parse_xml_string(xml, Usage)
    SCENARIOS[scname] = Scenario(description, usage)

def remove_scenario(scname):
    """
    Remove a named scenario from the global list.
    """
    del SCENARIOS[scname]

def add_class_scenarios(class_name, cls):
    """
    Add scenarios from a class to the global collection of scenarios.
    """
    # Each XBlock class can provide scenarios to display in the workbench.
    if hasattr(cls, "workbench_scenarios"):
        for i, (desc, xml) in enumerate(cls.workbench_scenarios()):
            scname = "%s.%d" % (class_name, i)
            add_xml_scenario(scname, desc, xml)
    else:
        # No specific scenarios, just show it with three generic children.
        default_children = [Usage("debugchild", []) for _ in xrange(3)]
        scname = "%s.0" % class_name
        usage = Usage(class_name, default_children)
        SCENARIOS[scname] = Scenario(class_name, usage)

def _do_once():
    """
    Called once when the module is imported to create the global scenarios.
    """
    # Get all the XBlock classes, and add their scenarios.
    for class_name, cls in XBlock.load_classes():
        add_class_scenarios(class_name, cls)

_do_once()
