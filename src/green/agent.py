"""Green Agent - Test Quality Evaluator.

Orchestrates test evaluation workflow with track-based execution.
Single executor with simple if/else mode switching (KISS principle).
"""

import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Literal

from green.models import Task, TestExecutionResult
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


def execute_test_against_correct(
    test_code: str, correct_implementation: str, track: Literal["tdd", "bdd"]
) -> TestExecutionResult:
    """Execute generated tests against correct implementation.

    Creates isolated test environment, writes test code and implementation,
    executes pytest with timeout, captures results, and cleans up.

    Args:
        test_code: Generated test code to execute
        correct_implementation: Correct implementation code
        track: Evaluation track ("tdd" or "bdd")

    Returns:
        TestExecutionResult with exit code, stdout, stderr, execution time, and pass/fail status
    """
    # Create isolated temp directory for test execution
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Write correct.py to temp directory
        correct_file = temp_path / "correct.py"
        correct_file.write_text(correct_implementation)

        # Write test code to file
        test_file = temp_path / "test_generated.py"
        test_file.write_text(test_code)

        # Execute pytest with 30-second timeout
        start_time = time.time()
        try:
            result = subprocess.run(
                ["pytest", str(test_file), "-v"],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )
            exit_code = result.returncode
            stdout = result.stdout
            stderr = result.stderr
        except subprocess.TimeoutExpired as e:
            # Handle timeout - tests failed due to timeout
            exit_code = 1  # Non-zero exit code for failure
            stdout = e.stdout.decode() if e.stdout else ""
            stderr = e.stderr.decode() if e.stderr else ""
            stderr += "\nERROR: Test execution exceeded 30-second timeout"

        execution_time = time.time() - start_time

        # Return binary result: PASS (0) or FAIL (non-zero)
        return TestExecutionResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            execution_time=execution_time,
            passed=(exit_code == 0),
        )
        # Temp directory automatically cleaned up by context manager
