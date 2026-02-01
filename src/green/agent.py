"""Green Agent - Test Quality Evaluator.

Orchestrates test evaluation workflow with track-based execution.
Single executor with simple if/else mode switching (KISS principle).
"""

import json
from pathlib import Path
from typing import Literal

from green.models import Task
from green.settings import Settings


class TaskLoadError(Exception):
    """Raised when task loading fails due to missing or invalid files."""

    pass


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


def load_task(task_dir: Path, track: Literal["tdd", "bdd"]) -> Task:
    """Load task specification and implementations from directory.

    Reads task directory structure, parses spec files, loads implementations,
    and validates metadata using Pydantic models.

    Args:
        task_dir: Path to task directory (data/tasks/{track}/python/{task_id}/)
        track: Evaluation track ("tdd" or "bdd")

    Returns:
        Task instance with validated data

    Raises:
        TaskLoadError: If required files are missing or invalid
    """
    # Load metadata.json
    metadata_file = task_dir / "metadata.json"
    if not metadata_file.exists():
        raise TaskLoadError(f"Missing metadata.json in {task_dir}")

    try:
        metadata = json.loads(metadata_file.read_text())
    except (json.JSONDecodeError, OSError) as e:
        raise TaskLoadError(f"Failed to read metadata.json: {e}")

    task_id = metadata.get("task_id", "")
    function_name = metadata.get("function_name", "")

    # Load spec file based on track
    if track == "tdd":
        spec_file = task_dir / "spec.py"
        if not spec_file.exists():
            raise TaskLoadError(f"Missing spec.py in {task_dir}")
        spec = spec_file.read_text()
    else:  # bdd
        spec_file = task_dir / "spec.feature"
        if not spec_file.exists():
            raise TaskLoadError(f"Missing spec.feature in {task_dir}")
        spec = spec_file.read_text()

    # Load implementations
    impl_dir = task_dir / "implementation"
    correct_file = impl_dir / "correct.py"
    buggy_file = impl_dir / "buggy.py"

    if not correct_file.exists():
        raise TaskLoadError(f"Missing correct.py in {task_dir}/implementation")
    if not buggy_file.exists():
        raise TaskLoadError(f"Missing buggy.py in {task_dir}/implementation")

    correct_implementation = correct_file.read_text()
    buggy_implementation = buggy_file.read_text()

    # Create and validate Task using Pydantic
    return Task(
        task_id=task_id,
        function_name=function_name,
        track=track,
        spec=spec,
        correct_implementation=correct_implementation,
        buggy_implementation=buggy_implementation,
    )
