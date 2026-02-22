"""Tests for track configuration loading.

Following TDD RED phase - these tests MUST fail initially.
"""

from pathlib import Path

import pytest


@pytest.fixture
def temp_scenario_file(tmp_path: Path) -> Path:
    """Create temporary scenario.toml for tests."""
    scenario_content = """
[green_agent]
agentbeats_id = "test-green"
env = { LOG_LEVEL = "INFO" }

[[participants]]
agentbeats_id = "test-purple"
name = "purple"
env = { LOG_LEVEL = "INFO" }

[config]
track = "tdd"
task_count = 5
timeout_per_task = 60
"""
    scenario_file = tmp_path / "scenario.toml"
    scenario_file.write_text(scenario_content)
    return scenario_file


@pytest.fixture
def temp_scenario_bdd(tmp_path: Path) -> Path:
    """Create temporary scenario.toml with BDD track."""
    scenario_content = """
[config]
track = "bdd"
task_count = 5
timeout_per_task = 60
"""
    scenario_file = tmp_path / "scenario_bdd.toml"
    scenario_file.write_text(scenario_content)
    return scenario_file


@pytest.fixture
def temp_scenario_invalid(tmp_path: Path) -> Path:
    """Create temporary scenario.toml with invalid track."""
    scenario_content = """
[config]
track = "invalid"
task_count = 5
timeout_per_task = 60
"""
    scenario_file = tmp_path / "scenario_invalid.toml"
    scenario_file.write_text(scenario_content)
    return scenario_file


@pytest.fixture
def temp_scenario_missing_track(tmp_path: Path) -> Path:
    """Create temporary scenario.toml without track field."""
    scenario_content = """
[config]
task_count = 5
timeout_per_task = 60
"""
    scenario_file = tmp_path / "scenario_missing.toml"
    scenario_file.write_text(scenario_content)
    return scenario_file


class TestSettingsConfiguration:
    """Test suite for configuration loading from scenario.toml."""

    def test_load_config_from_toml(
        self, temp_scenario_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Load configuration from scenario.toml using toml parser."""
        from green.settings import Settings

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        settings = Settings.from_file(temp_scenario_file)

        assert settings.track == "tdd"
        assert settings.task_count == 5
        assert settings.timeout_per_task == 60

    def test_load_tdd_track(
        self, temp_scenario_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Read track from scenario.toml config - TDD mode."""
        from green.settings import Settings

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        settings = Settings.from_file(temp_scenario_file)

        assert settings.track == "tdd"
        assert settings.is_tdd_mode() is True
        assert settings.is_bdd_mode() is False

    def test_load_bdd_track(self, temp_scenario_bdd: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Read track from scenario.toml config - BDD mode."""
        from green.settings import Settings

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        settings = Settings.from_file(temp_scenario_bdd)

        assert settings.track == "bdd"
        assert settings.is_bdd_mode() is True
        assert settings.is_tdd_mode() is False

    def test_fail_on_invalid_track(
        self, temp_scenario_invalid: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Validate track is supported - fail on invalid value."""
        from green.settings import Settings, SettingsError

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Should raise error for invalid track
        with pytest.raises(SettingsError, match="Invalid configuration"):
            Settings.from_file(temp_scenario_invalid)

    def test_fail_on_missing_track(self, temp_scenario_missing_track: Path) -> None:
        """Fail fast if required config missing - track field."""
        from green.settings import Settings, SettingsError

        # Should raise error for missing track
        with pytest.raises(SettingsError, match="track"):
            Settings.from_file(temp_scenario_missing_track)

    def test_load_openai_env_vars(
        self, temp_scenario_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Load OpenAI env vars: OPENAI_API_KEY, OPENAI_BASE_URL."""
        from green.settings import Settings

        # Set environment variables
        monkeypatch.setenv("OPENAI_API_KEY", "test-api-key-123")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

        settings = Settings.from_file(temp_scenario_file)

        assert settings.openai_api_key == "test-api-key-123"
        assert settings.openai_base_url == "https://api.openai.com/v1"

    def test_openai_base_url_optional(
        self, temp_scenario_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """OPENAI_BASE_URL is optional - support OpenAI-compatible endpoints."""
        from green.settings import Settings

        # Only set API key, not base URL
        monkeypatch.setenv("OPENAI_API_KEY", "test-api-key-123")
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

        settings = Settings.from_file(temp_scenario_file)

        assert settings.openai_api_key == "test-api-key-123"
        assert settings.openai_base_url is None

    def test_fail_on_missing_openai_api_key(
        self, temp_scenario_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Fail fast if OPENAI_API_KEY is missing."""
        from green.settings import Settings, SettingsError

        # Remove API key from environment
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        # Should raise error for missing API key
        with pytest.raises(SettingsError, match="OPENAI_API_KEY"):
            Settings.from_file(temp_scenario_file)

    def test_get_task_directory_tdd(
        self, temp_scenario_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Load TDD tasks from data/tasks/tdd/."""
        from green.settings import Settings

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        settings = Settings.from_file(temp_scenario_file)
        task_dir = settings.get_task_directory()

        assert "data/tasks/tdd" in str(task_dir)
        assert task_dir.parts[-2] == "tdd"

    def test_get_task_directory_bdd(
        self, temp_scenario_bdd: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Load BDD tasks from data/tasks/bdd/."""
        from green.settings import Settings

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        settings = Settings.from_file(temp_scenario_bdd)
        task_dir = settings.get_task_directory()

        assert "data/tasks/bdd" in str(task_dir)
        assert task_dir.parts[-2] == "bdd"

    def test_settings_immutable(
        self, temp_scenario_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Settings should be immutable after creation."""
        from green.settings import Settings

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        settings = Settings.from_file(temp_scenario_file)

        # Pydantic models are frozen, so this should raise
        with pytest.raises(Exception):
            settings.track = "bdd"  # type: ignore
