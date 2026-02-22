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


def _execute_test_in_isolation(
    test_code: str, implementation: str, implementation_filename: str
) -> TestExecutionResult:
    """Execute tests against an implementation in isolated environment.

    Internal helper function that creates isolated test environment,
    writes test code and implementation, executes pytest with timeout,
    captures results, and cleans up.

    Args:
        test_code: Generated test code to execute
        implementation: Implementation code to test against
        implementation_filename: Name of implementation file (e.g., "correct.py" or "buggy.py")

    Returns:
        TestExecutionResult with exit code, stdout, stderr, execution time, and pass/fail status
    """
    # Create isolated temp directory for test execution
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Write implementation to temp directory
        impl_file = temp_path / implementation_filename
        impl_file.write_text(implementation)

        # Write test code to file
        test_file = temp_path / "test_generated.py"
        test_file.write_text(test_code)

        # Block network access in test subprocess (STORY-008 AC fix)
        conftest = temp_path / "conftest.py"
        conftest.write_text(
            "import socket as _socket\n"
            "_original = _socket.socket\n"
            "def _guard(*a, **kw):\n"
            "    raise OSError('Network access disabled in test environment')\n"
            "_socket.socket = _guard\n"
        )

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
            return TestExecutionResult(
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                execution_time=execution_time,
                passed=False,
                failure_type="timeout",
            )

        execution_time = time.time() - start_time

        # Classify failure type using pytest exit codes:
        # 0 = passed, 1 = assertion failures, 2+ = infrastructure (collection/syntax/usage)
        if exit_code == 0:
            failure_type = "none"
        elif exit_code == 1:
            failure_type = "assertion"
        else:
            failure_type = "infrastructure"

        return TestExecutionResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            execution_time=execution_time,
            passed=(exit_code == 0),
            failure_type=failure_type,
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
    return _execute_test_in_isolation(test_code, correct_implementation, "correct.py")


def execute_test_against_buggy(
    test_code: str, buggy_implementation: str, track: Literal["tdd", "bdd"]
) -> TestExecutionResult:
    """Execute generated tests against buggy implementation.

    Creates isolated test environment, writes test code and buggy implementation,
    executes pytest with timeout, captures results, and cleans up.

    Tests are expected to FAIL when run against buggy code (detecting injected bugs).
    The result indicates whether the tests detected the bug:
    - passed=False (exit_code != 0): Bug detected (tests failed as expected)
    - passed=True (exit_code == 0): Bug missed (tests passed despite buggy code)

    Args:
        test_code: Generated test code to execute
        buggy_implementation: Buggy implementation with injected defects
        track: Evaluation track ("tdd" or "bdd")

    Returns:
        TestExecutionResult with exit code, stdout, stderr, execution time, and pass/fail status.
        Assertion failures in stdout/stderr indicate bug detection.
    """
    return _execute_test_in_isolation(test_code, buggy_implementation, "buggy.py")


def calculate_fault_detection_score(
    correct_result: TestExecutionResult | None, buggy_result: TestExecutionResult | None
) -> float:
    """Calculate fault detection score for a single task.

    Calculates whether tests correctly pass on correct implementation AND
    fail on buggy implementation (detecting the injected bug).

    Formula: fault_detection = 1.0 if (passed_correct AND failed_buggy) else 0.0

    Args:
        correct_result: Test execution result against correct implementation (or None)
        buggy_result: Test execution result against buggy implementation (or None)

    Returns:
        1.0 if tests passed correct AND failed buggy (perfect detection)
        0.0 otherwise (failed to detect bug, or tests themselves broken)
    """
    # Handle edge cases: None results
    if correct_result is None or buggy_result is None:
        return 0.0

    # Perfect fault detection: tests pass on correct, fail on buggy
    if correct_result.passed and not buggy_result.passed:
        return 1.0

    # All other cases: 0.0
    # - Tests failed on correct (tests broken)
    # - Tests passed on buggy (missed bug)
    # - Tests failed on both (tests broken)
    return 0.0


def aggregate_fault_detection_scores(scores: list[float]) -> float:
    """Aggregate fault detection scores across multiple tasks.

    Uses simple averaging to calculate overall fault detection rate.

    Args:
        scores: List of per-task fault detection scores (each in range [0.0, 1.0])

    Returns:
        Average fault detection score, or 0.0 for empty list
    """
    if not scores:
        return 0.0

    return sum(scores) / len(scores)
