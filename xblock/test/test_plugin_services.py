"""
Tests for runtime services provided by installed packages via the
``xblock.service.v1`` entry-point group.
"""
import pytest

from xblock.core import XBlock
from xblock.exceptions import NoSuchServiceError
from xblock.fields import ScopeIds
from xblock.runtime import ServiceProvider
from xblock.test.tools import TestRuntime


class DummyAIService:
    """A service provider class, as a plugin package would define it."""

    def __init__(self, **kwargs):
        self.runtime = kwargs.get('runtime')
        self.xblock = kwargs.get('xblock')

    def run_profile(self, profile_id, user_input):
        """A representative service method."""
        return f"ran {profile_id} with {user_input!r}"


@XBlock.wants('ai_extensions')
class WantsAIBlock(XBlock):
    """An XBlock that can optionally use the ai_extensions service."""


@XBlock.needs('ai_extensions')
class NeedsAIBlock(XBlock):
    """An XBlock that requires the ai_extensions service."""


def make_block(block_class, runtime=None):
    """Construct a block of `block_class` in a fresh TestRuntime."""
    runtime = runtime or TestRuntime()
    return runtime.construct_xblock_from_class(
        block_class, ScopeIds('user', 'test', 'def_id', 'usage_id'),
    )


@ServiceProvider.register_temp_plugin(
    DummyAIService, identifier='ai_extensions', group='xblock.service.v1',
)
def test_plugin_service_loaded_from_entry_point():
    block = make_block(WantsAIBlock)
    service = block.runtime.service(block, 'ai_extensions')
    assert isinstance(service, DummyAIService)
    assert service.runtime is block.runtime
    assert service.xblock is block
    assert service.run_profile('profile-1', 'hi') == "ran profile-1 with 'hi'"


@ServiceProvider.register_temp_plugin(
    DummyAIService, identifier='ai_extensions', group='xblock.service.v1',
)
def test_runtime_service_shadows_plugin_service():
    sentinel = object()
    runtime = TestRuntime(services={'ai_extensions': sentinel})
    block = make_block(WantsAIBlock, runtime=runtime)
    assert block.runtime.service(block, 'ai_extensions') is sentinel


@ServiceProvider.register_temp_plugin(
    DummyAIService, identifier='ai_extensions', group='xblock.service.v1',
)
def test_runtime_none_service_disables_plugin_service():
    wants_block = make_block(
        WantsAIBlock, runtime=TestRuntime(services={'ai_extensions': None}),
    )
    assert wants_block.runtime.service(wants_block, 'ai_extensions') is None

    needs_block = make_block(
        NeedsAIBlock, runtime=TestRuntime(services={'ai_extensions': None}),
    )
    with pytest.raises(NoSuchServiceError):
        needs_block.runtime.service(needs_block, 'ai_extensions')


def test_missing_plugin_service_wanted_returns_none():
    block = make_block(WantsAIBlock)
    assert block.runtime.service(block, 'ai_extensions') is None


def test_missing_plugin_service_needed_raises():
    block = make_block(NeedsAIBlock)
    with pytest.raises(NoSuchServiceError):
        block.runtime.service(block, 'ai_extensions')


@ServiceProvider.register_temp_plugin(
    DummyAIService, identifier='ai_extensions', group='xblock.service.v1',
)
def test_undeclared_plugin_service_still_raises():
    block = make_block(XBlock)  # declares neither needs nor wants
    with pytest.raises(NoSuchServiceError):
        block.runtime.service(block, 'ai_extensions')
