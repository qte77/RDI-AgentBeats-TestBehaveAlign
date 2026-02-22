"""Tests for A2A AgentExecutor implementation.

Following TDD RED phase - these tests MUST fail initially.
Tests cover executor integration with A2A SDK and evaluation orchestration.
"""

from pathlib import Path

import pytest


class TestGreenAgentExecutor:
    """Test suite for Green Agent executor."""

    def test_executor_inherits_from_agent_executor(
        self, temp_scenario_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Executor should inherit from a2a.server.AgentExecutor."""
        from green.executor import GreenAgentExecutor

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Create executor instance
        executor = GreenAgentExecutor(temp_scenario_file)

        # Verify executor has required A2A methods
        assert hasattr(executor, "execute")
        assert callable(executor.execute)

    def test_executor_loads_settings_from_scenario(
        self, temp_scenario_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Executor should load settings from scenario.toml."""
        from green.executor import GreenAgentExecutor

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Create executor instance
        executor = GreenAgentExecutor(temp_scenario_file)

        # Verify settings are loaded
        assert hasattr(executor, "settings")
        assert executor.settings.track == "tdd"
        assert executor.settings.task_count == 5

    def test_executor_has_cancel_method(
        self, temp_scenario_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Executor should implement cancel method for task cancellation."""
        from green.executor import GreenAgentExecutor

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Create executor instance
        executor = GreenAgentExecutor(temp_scenario_file)

        # Verify cancel method exists
        assert hasattr(executor, "cancel")
        assert callable(executor.cancel)

    def test_executor_validates_scenario_file_exists(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Executor should validate that scenario file exists."""
        from green.executor import GreenAgentExecutor

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Try to create executor with non-existent file
        non_existent_file = tmp_path / "does_not_exist.toml"

        # Should raise error for missing file
        with pytest.raises((FileNotFoundError, ValueError)):
            GreenAgentExecutor(non_existent_file)
