"""Example scenarios to display in the workbench.

This code is in the Workbench layer.

"""

from collections import namedtuple

from xblock.core import XBlock

from .runtime import WorkbenchRuntime

# Build the scenarios, which are named trees of usages.

Scenario = namedtuple("Scenario", "description usage_id")  # pylint: disable=C0103

SCENARIOS = {}


def add_xml_scenario(scname, description, xml):
    """
    Add a scenario defined in XML.
    """
    assert scname not in SCENARIOS, "Already have a %r scenario" % scname
    runtime = WorkbenchRuntime()
    usage_id = runtime.parse_xml_string(xml)
    SCENARIOS[scname] = Scenario(description, usage_id)


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


def _do_once():
    """
    Called once when the module is imported to create the global scenarios.
    """
    # Get all the XBlock classes, and add their scenarios.
    for class_name, cls in XBlock.load_classes():
        add_class_scenarios(class_name, cls)


_do_once()
