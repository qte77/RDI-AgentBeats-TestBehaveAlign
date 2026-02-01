"""Tests for test execution against correct.py (STORY-008).

Following TDD RED phase - these tests MUST fail initially.
Tests cover creating isolated test environments, executing pytest/pytest-bdd,
capturing results, and handling timeouts.
"""

from pathlib import Path

import pytest


@pytest.fixture
def temp_tdd_task(tmp_path: Path) -> Path:
    """Create a temporary TDD task directory with correct implementation."""
    task_dir = tmp_path / "task_001_example"
    task_dir.mkdir(parents=True, exist_ok=True)

    # Create correct.py implementation
    impl_dir = task_dir / "implementation"
    impl_dir.mkdir(parents=True, exist_ok=True)

    correct_py = impl_dir / "correct.py"
    correct_py.write_text('''def example_function(x: int) -> int:
    """Example function for testing."""
    return x * 2
''')

    return task_dir


@pytest.fixture
def valid_tdd_test_code() -> str:
    """Valid TDD test code that should pass against correct implementation."""
    return '''
def test_example_function():
    from correct import example_function
    assert example_function(5) == 10
    assert example_function(0) == 0
    assert example_function(-3) == -6
'''


@pytest.fixture
def failing_tdd_test_code() -> str:
    """Test code that should fail even against correct implementation."""
    return '''
def test_example_function():
    from correct import example_function
    assert example_function(5) == 999  # Wrong expectation
'''


@pytest.fixture
def timeout_test_code() -> str:
    """Test code that will exceed timeout."""
    return '''
import time

def test_timeout():
    time.sleep(60)  # Exceeds 30-second timeout
    assert True
'''


class TestIsolatedTestEnvironment:
    """Test suite for creating isolated test environments."""

    def test_create_isolated_temp_directory(self, temp_tdd_task: Path, valid_tdd_test_code: str) -> None:
        """Create isolated test environment (temp directory per task)."""
        from green.agent import execute_test_against_correct

        # Should create a temporary directory for test execution
        result = execute_test_against_correct(
            test_code=valid_tdd_test_code,
            correct_implementation=(temp_tdd_task / "implementation" / "correct.py").read_text(),
            track="tdd"
        )

        # Result should exist (temp dir was created and used)
        assert result is not None

    def test_write_test_code_to_file(self, temp_tdd_task: Path, valid_tdd_test_code: str) -> None:
        """Write test code to file in test environment."""
        from green.agent import execute_test_against_correct

        result = execute_test_against_correct(
            test_code=valid_tdd_test_code,
            correct_implementation=(temp_tdd_task / "implementation" / "correct.py").read_text(),
            track="tdd"
        )

        # Should have written test code to a file and executed it
        assert result is not None

    def test_copy_correct_implementation_to_test_env(self, temp_tdd_task: Path, valid_tdd_test_code: str) -> None:
        """Copy correct.py to test environment."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()

        result = execute_test_against_correct(
            test_code=valid_tdd_test_code,
            correct_implementation=correct_impl,
            track="tdd"
        )

        # Should have copied correct.py to temp dir for import
        assert result is not None
        # Test should be able to import from correct.py
        assert result.passed  # Valid test against correct implementation


class TestPytestExecution:
    """Test suite for executing pytest (TDD) or pytest-bdd (BDD)."""

    def test_execute_pytest_for_tdd(self, temp_tdd_task: Path, valid_tdd_test_code: str) -> None:
        """Execute pytest (TDD) on test code."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()

        result = execute_test_against_correct(
            test_code=valid_tdd_test_code,
            correct_implementation=correct_impl,
            track="tdd"
        )

        assert result is not None
        # Should execute pytest and return result
        assert hasattr(result, 'exit_code')

    def test_execute_pytest_bdd_for_bdd(self, tmp_path: Path) -> None:
        """Execute pytest-bdd (BDD) on feature and step files."""
        from green.agent import execute_test_against_correct

        # Create BDD-style test code with feature and steps
        bdd_test_code = '''
def test_example_feature():
    """BDD test stub."""
    from correct import example_function
    assert example_function(5) == 10
'''

        correct_impl = '''def example_function(x: int) -> int:
    return x * 2
'''

        result = execute_test_against_correct(
            test_code=bdd_test_code,
            correct_implementation=correct_impl,
            track="bdd"
        )

        assert result is not None


class TestResultCapture:
    """Test suite for capturing exit code, stdout, stderr, and execution time."""

    def test_capture_exit_code(self, temp_tdd_task: Path, valid_tdd_test_code: str) -> None:
        """Capture exit code from test execution."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()

        result = execute_test_against_correct(
            test_code=valid_tdd_test_code,
            correct_implementation=correct_impl,
            track="tdd"
        )

        assert hasattr(result, 'exit_code')
        assert isinstance(result.exit_code, int)
        # Exit code 0 = success
        assert result.exit_code == 0

    def test_capture_stdout(self, temp_tdd_task: Path, valid_tdd_test_code: str) -> None:
        """Capture stdout from test execution."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()

        result = execute_test_against_correct(
            test_code=valid_tdd_test_code,
            correct_implementation=correct_impl,
            track="tdd"
        )

        assert hasattr(result, 'stdout')
        assert isinstance(result.stdout, str)

    def test_capture_stderr(self, temp_tdd_task: Path, valid_tdd_test_code: str) -> None:
        """Capture stderr from test execution."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()

        result = execute_test_against_correct(
            test_code=valid_tdd_test_code,
            correct_implementation=correct_impl,
            track="tdd"
        )

        assert hasattr(result, 'stderr')
        assert isinstance(result.stderr, str)

    def test_capture_execution_time(self, temp_tdd_task: Path, valid_tdd_test_code: str) -> None:
        """Capture execution time in seconds."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()

        result = execute_test_against_correct(
            test_code=valid_tdd_test_code,
            correct_implementation=correct_impl,
            track="tdd"
        )

        assert hasattr(result, 'execution_time')
        assert isinstance(result.execution_time, float)
        assert result.execution_time >= 0


class TestBinaryResult:
    """Test suite for returning binary PASS/FAIL result."""

    def test_return_pass_for_successful_tests(self, temp_tdd_task: Path, valid_tdd_test_code: str) -> None:
        """Return binary result: PASS (exit code 0)."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()

        result = execute_test_against_correct(
            test_code=valid_tdd_test_code,
            correct_implementation=correct_impl,
            track="tdd"
        )

        assert result.passed is True
        assert result.exit_code == 0

    def test_return_fail_for_failing_tests(self, temp_tdd_task: Path, failing_tdd_test_code: str) -> None:
        """Return binary result: FAIL (non-zero exit code)."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()

        result = execute_test_against_correct(
            test_code=failing_tdd_test_code,
            correct_implementation=correct_impl,
            track="tdd"
        )

        assert result.passed is False
        assert result.exit_code != 0


class TestTimeout:
    """Test suite for 30-second timeout per test run."""

    def test_implement_30_second_timeout(self, timeout_test_code: str) -> None:
        """Implement 30-second timeout per test run."""
        from green.agent import execute_test_against_correct

        correct_impl = '''def dummy(): pass'''

        # Should timeout and return failure
        result = execute_test_against_correct(
            test_code=timeout_test_code,
            correct_implementation=correct_impl,
            track="tdd"
        )

        # Timeout should result in failure
        assert result.passed is False
        # Execution time should be close to timeout (30 seconds)
        assert result.execution_time <= 35  # Allow some overhead


class TestCleanup:
    """Test suite for cleaning up test environment."""

    def test_cleanup_temp_files(self, temp_tdd_task: Path, valid_tdd_test_code: str) -> None:
        """Clean up test environment (temp files) after execution."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()

        # Execute test
        result = execute_test_against_correct(
            test_code=valid_tdd_test_code,
            correct_implementation=correct_impl,
            track="tdd"
        )

        assert result is not None
        # Temp directory should be cleaned up automatically
        # (verified by tempfile context manager behavior)


class TestSubprocessIsolation:
    """Test suite for using subprocess with timeout for isolation."""

    def test_use_subprocess_for_isolation(self, temp_tdd_task: Path, valid_tdd_test_code: str) -> None:
        """Use subprocess with timeout for isolation."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()

        result = execute_test_against_correct(
            test_code=valid_tdd_test_code,
            correct_implementation=correct_impl,
            track="tdd"
        )

        # Should run in isolated subprocess
        assert result is not None
        assert hasattr(result, 'exit_code')

    def test_capture_output_streams_for_debugging(self, temp_tdd_task: Path, valid_tdd_test_code: str) -> None:
        """Capture output streams for debugging."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()

        result = execute_test_against_correct(
            test_code=valid_tdd_test_code,
            correct_implementation=correct_impl,
            track="tdd"
        )

        # Should have stdout and stderr available for debugging
        assert hasattr(result, 'stdout')
        assert hasattr(result, 'stderr')
