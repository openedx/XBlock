"""Test Workbench Runtime"""

from xblock.test.tools import assert_equals, assert_false, assert_is_none, assert_true

from xblock.fields import Scope
from xblock.runtime import KeyValueStore
from ..runtime import ScenarioIdManager, WorkbenchDjangoKeyValueStore


def test_scenario_ids():
    # Test basic ID generation meets our expectations
    id_mgr = ScenarioIdManager()

    # No scenario loaded
    assert_equals(id_mgr.create_definition("my_block"), ".my_block.d0")
    # Should increment
    assert_equals(id_mgr.create_definition("my_block"), ".my_block.d1")
    assert_equals(id_mgr.create_definition("my_block"), ".my_block.d2")

    # Slug support
    assert_equals(
        id_mgr.create_definition("my_block", "my_slug"),
        ".my_block.my_slug.d0"
    )
    assert_equals(
        id_mgr.create_definition("my_block", "my_slug"),
        ".my_block.my_slug.d1"
    )

    # Now that we have a scenario, our definition numbering starts over again.
    id_mgr.set_scenario("my_scenario")
    assert_equals(id_mgr.create_definition("my_block"), "my_scenario.my_block.d0")
    assert_equals(id_mgr.create_definition("my_block"), "my_scenario.my_block.d1")

    id_mgr.set_scenario("another_scenario")
    assert_equals(id_mgr.create_definition("my_block"), "another_scenario.my_block.d0")

    # Now make sure our usages are attached to definitions
    assert_is_none(id_mgr.last_created_usage_id())
    assert_equals(
        id_mgr.create_usage("my_scenario.my_block.d0"),
        "my_scenario.my_block.d0.u0"
    )
    assert_equals(
        id_mgr.create_usage("my_scenario.my_block.d0"),
        "my_scenario.my_block.d0.u1"
    )
    assert_equals(id_mgr.last_created_usage_id(), "my_scenario.my_block.d0.u1")


def test_kv_store():
    # Simple test to makes sure we can get things in and out
    kvs = WorkbenchDjangoKeyValueStore()
    key = KeyValueStore.Key(
        scope=Scope.content,
        user_id="rusty",
        block_scope_id="my_scenario.my_block.d0",
        field_name="age"
    )

    assert_false(kvs.has(key))
    kvs.set(key, 7)
    assert_true(kvs.has(key))
    assert_equals(kvs.get(key), 7)
    kvs.delete(key)
    assert_false(kvs.has(key))
