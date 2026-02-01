"""Configuration settings for Green Agent.

Loads configuration from scenario.toml and environment variables.
Validates track selection and required credentials.
"""

import os
from pathlib import Path
from typing import Literal

import tomli
from pydantic import BaseModel, Field, ValidationError, field_validator


class SettingsError(Exception):
    """Raised when configuration is invalid or missing."""

    pass


class Settings(BaseModel):
    """Green Agent configuration settings.

    Loads track configuration, task paths, and API credentials.
    Immutable after creation (frozen=True).
    """

    model_config = {"frozen": True}

    track: Literal["tdd", "bdd"] = Field(..., description="Evaluation track: tdd or bdd")
    task_count: int = Field(..., description="Number of tasks to evaluate")
    timeout_per_task: int = Field(..., description="Timeout per task in seconds")
    openai_api_key: str = Field(..., description="OpenAI API key from environment")
    openai_base_url: str | None = Field(None, description="Optional OpenAI-compatible base URL")

    @field_validator("track")
    @classmethod
    def validate_track(cls, v: str) -> str:
        """Validate track is either 'tdd' or 'bdd'."""
        if v not in ("tdd", "bdd"):
            raise ValueError(f"Invalid track '{v}'. Must be 'tdd' or 'bdd'.")
        return v

    @classmethod
    def from_file(cls, config_path: Path) -> "Settings":
        """Load settings from scenario.toml file.

        Args:
            config_path: Path to scenario.toml file

        Returns:
            Settings instance with loaded configuration

        Raises:
            SettingsError: If config is invalid or required fields missing
        """
        try:
            # Read TOML config
            with open(config_path, "rb") as f:
                config = tomli.load(f)

            # Extract config section
            if "config" not in config:
                raise SettingsError("Missing [config] section in scenario.toml")

            cfg = config["config"]

            # Validate required fields
            if "track" not in cfg:
                raise SettingsError("Missing required field 'track' in [config]")

            # Load OpenAI credentials from environment
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise SettingsError("Missing required environment variable: OPENAI_API_KEY")

            openai_base_url = os.getenv("OPENAI_BASE_URL")

            # Create settings instance
            return cls(
                track=cfg["track"],
                task_count=cfg.get("task_count", 5),
                timeout_per_task=cfg.get("timeout_per_task", 60),
                openai_api_key=openai_api_key,
                openai_base_url=openai_base_url,
            )

        except (OSError, tomli.TOMLDecodeError) as e:
            raise SettingsError(f"Failed to load config from {config_path}: {e}")
        except (ValueError, ValidationError) as e:
            raise SettingsError(f"Invalid configuration: {e}")

    def is_tdd_mode(self) -> bool:
        """Check if running in TDD mode."""
        return self.track == "tdd"

    def is_bdd_mode(self) -> bool:
        """Check if running in BDD mode."""
        return self.track == "bdd"

    def get_task_directory(self) -> Path:
        """Get task directory path based on track.

        Returns:
            Path to data/tasks/{track}/python/
        """
        return Path("data") / "tasks" / self.track / "python"
