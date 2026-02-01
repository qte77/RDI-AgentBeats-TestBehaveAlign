"""Tests for agent track configuration handling.

Following TDD RED phase - these tests MUST fail initially.
Tests track handling in agent module.
"""

from pathlib import Path

import pytest


@pytest.fixture
def mock_settings_tdd(monkeypatch: pytest.MonkeyPatch):
    """Mock settings with TDD track."""

    class MockSettings:
        track = "tdd"
        task_count = 5
        timeout_per_task = 60
        openai_api_key = "test-key"
        openai_base_url = None

        def is_tdd_mode(self) -> bool:
            return self.track == "tdd"

        def is_bdd_mode(self) -> bool:
            return self.track == "bdd"

        def get_task_directory(self) -> Path:
            return Path("data/tasks/tdd/python")

    return MockSettings()


@pytest.fixture
def mock_settings_bdd(monkeypatch: pytest.MonkeyPatch):
    """Mock settings with BDD track."""

    class MockSettings:
        track = "bdd"
        task_count = 5
        timeout_per_task = 60
        openai_api_key = "test-key"
        openai_base_url = None

        def is_tdd_mode(self) -> bool:
            return self.track == "tdd"

        def is_bdd_mode(self) -> bool:
            return self.track == "bdd"

        def get_task_directory(self) -> Path:
            return Path("data/tasks/bdd/python")

    return MockSettings()


class TestAgentTrackConfiguration:
    """Test suite for agent track configuration handling."""

    def test_agent_uses_tdd_track(self, mock_settings_tdd) -> None:
        """Agent uses TDD track from settings - use pytest for TDD."""
        from green.agent import GreenAgent

        agent = GreenAgent(settings=mock_settings_tdd)

        assert agent.track == "tdd"
        assert agent.is_tdd_mode() is True

    def test_agent_uses_bdd_track(self, mock_settings_bdd) -> None:
        """Agent uses BDD track from settings - use pytest-bdd for BDD."""
        from green.agent import GreenAgent

        agent = GreenAgent(settings=mock_settings_bdd)

        assert agent.track == "bdd"
        assert agent.is_bdd_mode() is True

    def test_agent_single_executor_with_mode_switch(
        self, mock_settings_tdd, mock_settings_bdd
    ) -> None:
        """Single executor with mode switch (KISS principle, no inheritance)."""
        from green.agent import GreenAgent

        # Should be the same class for both TDD and BDD
        agent_tdd = GreenAgent(settings=mock_settings_tdd)
        agent_bdd = GreenAgent(settings=mock_settings_bdd)

        # Both should be instances of the same class (no inheritance/subclasses)
        assert type(agent_tdd) is type(agent_bdd)
        assert agent_tdd.__class__.__name__ == "GreenAgent"
        assert agent_bdd.__class__.__name__ == "GreenAgent"

    def test_agent_loads_task_directory_tdd(self, mock_settings_tdd) -> None:
        """Agent loads task directory based on TDD track."""
        from green.agent import GreenAgent

        agent = GreenAgent(settings=mock_settings_tdd)
        task_dir = agent.get_task_directory()

        assert "tdd" in str(task_dir)

    def test_agent_loads_task_directory_bdd(self, mock_settings_bdd) -> None:
        """Agent loads task directory based on BDD track."""
        from green.agent import GreenAgent

        agent = GreenAgent(settings=mock_settings_bdd)
        task_dir = agent.get_task_directory()

        assert "bdd" in str(task_dir)

    def test_agent_track_included_in_results_placeholder(self, mock_settings_tdd) -> None:
        """Include track in results output (placeholder test)."""
        from green.agent import GreenAgent

        agent = GreenAgent(settings=mock_settings_tdd)

        # Placeholder - will be fully tested in later stories when results are implemented
        # For now, just verify track is accessible
        assert agent.track == "tdd"

    def test_agent_simple_if_else_for_track_handling(self, mock_settings_tdd) -> None:
        """Simple if/else for track handling - no complex abstractions."""
        from green.agent import GreenAgent

        agent = GreenAgent(settings=mock_settings_tdd)

        # Agent should have simple methods to check track mode
        # This tests KISS principle - simple boolean checks, no strategy pattern
        assert callable(agent.is_tdd_mode)
        assert callable(agent.is_bdd_mode)

        # Should return boolean
        assert isinstance(agent.is_tdd_mode(), bool)
        assert isinstance(agent.is_bdd_mode(), bool)
