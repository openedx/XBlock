"""Example scenarios to display in the workbench.

This code is in the Workbench layer.

"""
from collections import namedtuple

from django.conf import settings
from django.template.defaultfilters import slugify

from xblock.core import XBlock
from .runtime import WorkbenchRuntime, WORKBENCH_KVS

# Build the scenarios, which are named trees of usages.

Scenario = namedtuple("Scenario", "description usage_id xml")  # pylint: disable=C0103

SCENARIOS = {}


def add_xml_scenario(scname, description, xml):
    """
    Add a scenario defined in XML.
    """
    assert scname not in SCENARIOS, "Already have a %r scenario" % scname
    runtime = WorkbenchRuntime()

    # WorkbenchRuntime has an id_generator, but most runtimes won't
    # (because the generator will be contextual), so we
    # pass it explicitly to parse_xml_string.
    runtime.id_generator.set_scenario(slugify(description))
    usage_id = runtime.parse_xml_string(xml, runtime.id_generator)
    SCENARIOS[scname] = Scenario(description, usage_id, xml)


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


def init_scenarios():
    """
    Create all the scenarios declared in all the XBlock classes.
    """
    # Clear any existing scenarios, since this is used repeatedly during testing.
    SCENARIOS.clear()
    if settings.WORKBENCH['reset_state_on_restart']:
        WORKBENCH_KVS.clear()
    else:
        WORKBENCH_KVS.prep_for_scenario_loading()

    # Get all the XBlock classes, and add their scenarios.
    for class_name, cls in sorted(XBlock.load_classes()):
        add_class_scenarios(class_name, cls)
