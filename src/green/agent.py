"""Green Agent - Test Quality Evaluator.

Orchestrates test evaluation workflow with track-based execution.
Single executor with simple if/else mode switching (KISS principle).
"""

from pathlib import Path

from green.settings import Settings


class GreenAgent:
    """Green Agent executor.

    Supports both TDD and BDD evaluation modes through simple mode switching.
    No inheritance or complex abstractions - just straightforward if/else logic.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize Green Agent with configuration.

        Args:
            settings: Configuration loaded from scenario.toml and environment
        """
        self.settings = settings
        self.track = settings.track

    def is_tdd_mode(self) -> bool:
        """Check if running in TDD mode.

        Returns:
            True if track is "tdd", False otherwise
        """
        return self.track == "tdd"

    def is_bdd_mode(self) -> bool:
        """Check if running in BDD mode.

        Returns:
            True if track is "bdd", False otherwise
        """
        return self.track == "bdd"

    def get_task_directory(self) -> Path:
        """Get task directory path from settings.

        Returns:
            Path to task directory based on current track
        """
        return self.settings.get_task_directory()
