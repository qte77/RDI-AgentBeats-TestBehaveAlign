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
    return """
def test_example_function():
    from correct import example_function
    assert example_function(5) == 10
    assert example_function(0) == 0
    assert example_function(-3) == -6
"""


@pytest.fixture
def failing_tdd_test_code() -> str:
    """Test code that should fail even against correct implementation."""
    return """
def test_example_function():
    from correct import example_function
    assert example_function(5) == 999  # Wrong expectation
"""


@pytest.fixture
def timeout_test_code() -> str:
    """Test code that will exceed timeout."""
    return """
import time

def test_timeout():
    time.sleep(60)  # Exceeds 30-second timeout
    assert True
"""


class TestPytestExecution:
    """Test suite for executing pytest (TDD) or pytest-bdd (BDD)."""

    def test_copy_correct_implementation_to_test_env(
        self, temp_tdd_task: Path, valid_tdd_test_code: str
    ) -> None:
        """Copy correct.py to test environment."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()

        result = execute_test_against_correct(
            test_code=valid_tdd_test_code, correct_implementation=correct_impl, track="tdd"
        )

        # Should have copied correct.py to temp dir for import
        assert result is not None
        # Test should be able to import from correct.py
        assert result.passed  # Valid test against correct implementation

    def test_execute_pytest_for_tdd(self, temp_tdd_task: Path, valid_tdd_test_code: str) -> None:
        """Execute pytest (TDD) on test code."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()

        result = execute_test_against_correct(
            test_code=valid_tdd_test_code, correct_implementation=correct_impl, track="tdd"
        )

        assert result is not None
        # Should execute pytest and return result
        assert hasattr(result, "exit_code")

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

        correct_impl = """def example_function(x: int) -> int:
    return x * 2
"""

        result = execute_test_against_correct(
            test_code=bdd_test_code, correct_implementation=correct_impl, track="bdd"
        )

        assert result is not None


class TestResultCapture:
    """Test suite for capturing exit code, stdout, stderr, and execution time."""

    def test_capture_exit_code(self, temp_tdd_task: Path, valid_tdd_test_code: str) -> None:
        """Capture exit code from test execution."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()

        result = execute_test_against_correct(
            test_code=valid_tdd_test_code, correct_implementation=correct_impl, track="tdd"
        )

        assert hasattr(result, "exit_code")
        assert isinstance(result.exit_code, int)
        # Exit code 0 = success
        assert result.exit_code == 0

    def test_capture_stdout(self, temp_tdd_task: Path, valid_tdd_test_code: str) -> None:
        """Capture stdout from test execution."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()

        result = execute_test_against_correct(
            test_code=valid_tdd_test_code, correct_implementation=correct_impl, track="tdd"
        )

        assert hasattr(result, "stdout")
        assert isinstance(result.stdout, str)

    def test_capture_stderr(self, temp_tdd_task: Path, valid_tdd_test_code: str) -> None:
        """Capture stderr from test execution."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()

        result = execute_test_against_correct(
            test_code=valid_tdd_test_code, correct_implementation=correct_impl, track="tdd"
        )

        assert hasattr(result, "stderr")
        assert isinstance(result.stderr, str)

    def test_capture_execution_time(self, temp_tdd_task: Path, valid_tdd_test_code: str) -> None:
        """Capture execution time in seconds."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()

        result = execute_test_against_correct(
            test_code=valid_tdd_test_code, correct_implementation=correct_impl, track="tdd"
        )

        assert hasattr(result, "execution_time")
        assert isinstance(result.execution_time, float)
        assert result.execution_time >= 0


class TestBinaryResult:
    """Test suite for returning binary PASS/FAIL result."""

    def test_return_pass_for_successful_tests(
        self, temp_tdd_task: Path, valid_tdd_test_code: str
    ) -> None:
        """Return binary result: PASS (exit code 0)."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()

        result = execute_test_against_correct(
            test_code=valid_tdd_test_code, correct_implementation=correct_impl, track="tdd"
        )

        assert result.passed is True
        assert result.exit_code == 0

    def test_return_fail_for_failing_tests(
        self, temp_tdd_task: Path, failing_tdd_test_code: str
    ) -> None:
        """Return binary result: FAIL (non-zero exit code)."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()

        result = execute_test_against_correct(
            test_code=failing_tdd_test_code, correct_implementation=correct_impl, track="tdd"
        )

        assert result.passed is False
        assert result.exit_code != 0


class TestTimeout:
    """Test suite for 30-second timeout per test run."""

    def test_implement_30_second_timeout(self, timeout_test_code: str) -> None:
        """Implement 30-second timeout per test run."""
        from green.agent import execute_test_against_correct

        correct_impl = """def dummy(): pass"""

        # Should timeout and return failure
        result = execute_test_against_correct(
            test_code=timeout_test_code, correct_implementation=correct_impl, track="tdd"
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
            test_code=valid_tdd_test_code, correct_implementation=correct_impl, track="tdd"
        )

        assert result is not None
        # Temp directory should be cleaned up automatically
        # (verified by tempfile context manager behavior)


# ============================================================================
# STORY-009: Test execution against buggy.py
# ============================================================================


@pytest.fixture
def temp_buggy_task(tmp_path: Path) -> Path:
    """Create a temporary task directory with buggy implementation."""
    task_dir = tmp_path / "task_001_buggy"
    task_dir.mkdir(parents=True, exist_ok=True)

    # Create buggy.py implementation (off-by-one error)
    impl_dir = task_dir / "implementation"
    impl_dir.mkdir(parents=True, exist_ok=True)

    buggy_py = impl_dir / "buggy.py"
    buggy_py.write_text('''def example_function(x: int) -> int:
    """Example function with bug."""
    return x * 2 + 1  # Off-by-one error
''')

    return task_dir


@pytest.fixture
def good_test_code_detecting_bug() -> str:
    """Test code that should detect the bug in buggy.py."""
    return """
def test_example_function():
    from buggy import example_function
    assert example_function(5) == 10
    assert example_function(0) == 0
    assert example_function(-3) == -6
"""


@pytest.fixture
def weak_test_code_missing_bug() -> str:
    """Weak test code that doesn't detect the bug."""
    return """
def test_example_function():
    from buggy import example_function
    # Only tests that it returns an integer, doesn't check values
    result = example_function(5)
    assert isinstance(result, int)
"""


class TestBuggyExecution:
    """Test suite for executing tests against buggy.py (STORY-009)."""

    def test_execute_against_buggy_implementation(
        self, temp_buggy_task: Path, good_test_code_detecting_bug: str
    ) -> None:
        """Run tests against buggy.py instead of correct.py."""
        from green.agent import execute_test_against_buggy

        buggy_impl = (temp_buggy_task / "implementation" / "buggy.py").read_text()

        result = execute_test_against_buggy(
            test_code=good_test_code_detecting_bug,
            buggy_implementation=buggy_impl,
            track="tdd",
        )

        # Should execute and return result
        assert result is not None
        assert hasattr(result, "exit_code")

    def test_expect_tests_to_fail_on_buggy_code(
        self, temp_buggy_task: Path, good_test_code_detecting_bug: str
    ) -> None:
        """Expect tests to FAIL (detect injected bugs)."""
        from green.agent import execute_test_against_buggy

        buggy_impl = (temp_buggy_task / "implementation" / "buggy.py").read_text()

        result = execute_test_against_buggy(
            test_code=good_test_code_detecting_bug,
            buggy_implementation=buggy_impl,
            track="tdd",
        )

        # Tests should fail when run against buggy implementation
        assert result.passed is False
        assert result.exit_code != 0

    def test_return_bug_detected_when_tests_fail(
        self, temp_buggy_task: Path, good_test_code_detecting_bug: str
    ) -> None:
        """Return binary result: detected bug (FAIL)."""
        from green.agent import execute_test_against_buggy

        buggy_impl = (temp_buggy_task / "implementation" / "buggy.py").read_text()

        result = execute_test_against_buggy(
            test_code=good_test_code_detecting_bug,
            buggy_implementation=buggy_impl,
            track="tdd",
        )

        # Bug detected = tests failed = passed is False
        assert result.passed is False

    def test_return_bug_missed_when_tests_pass(
        self, temp_buggy_task: Path, weak_test_code_missing_bug: str
    ) -> None:
        """Return binary result: missed bug (PASS)."""
        from green.agent import execute_test_against_buggy

        buggy_impl = (temp_buggy_task / "implementation" / "buggy.py").read_text()

        result = execute_test_against_buggy(
            test_code=weak_test_code_missing_bug,
            buggy_implementation=buggy_impl,
            track="tdd",
        )

        # Bug missed = tests passed = passed is True
        assert result.passed is True
        assert result.exit_code == 0


class TestBuggyResultLogging:
    """Test suite for logging test failures and distinguishing error types."""

    def test_log_which_tests_failed(
        self, temp_buggy_task: Path, good_test_code_detecting_bug: str
    ) -> None:
        """Log which specific tests failed and why."""
        from green.agent import execute_test_against_buggy

        buggy_impl = (temp_buggy_task / "implementation" / "buggy.py").read_text()

        result = execute_test_against_buggy(
            test_code=good_test_code_detecting_bug,
            buggy_implementation=buggy_impl,
            track="tdd",
        )

        # Should capture detailed failure information in stdout/stderr
        assert result.stdout or result.stderr
        # Should contain assertion failure information
        assert "assert" in result.stdout.lower() or "assert" in result.stderr.lower()

    def test_distinguish_assertion_failures_from_infrastructure_errors(
        self, temp_buggy_task: Path, good_test_code_detecting_bug: str
    ) -> None:
        """Distinguish assertion failures from import/syntax errors."""
        from green.agent import execute_test_against_buggy

        buggy_impl = (temp_buggy_task / "implementation" / "buggy.py").read_text()

        # Assertion failure: valid tests that detect the bug
        assertion_result = execute_test_against_buggy(
            test_code=good_test_code_detecting_bug,
            buggy_implementation=buggy_impl,
            track="tdd",
        )
        assert assertion_result.passed is False
        assert assertion_result.failure_type == "assertion"

        # Infrastructure failure: syntax error in test code
        syntax_error_test = """
def test_syntax_error():
    this is not valid python
"""
        infra_result = execute_test_against_buggy(
            test_code=syntax_error_test,
            buggy_implementation=buggy_impl,
            track="tdd",
        )
        assert infra_result.passed is False
        assert infra_result.failure_type == "infrastructure"


class TestBuggyIsolation:
    """Test suite for reusing isolation infrastructure from Feature 8."""

    def test_reuse_isolation_infrastructure(
        self, temp_buggy_task: Path, good_test_code_detecting_bug: str
    ) -> None:
        """Reuse test execution infrastructure from Feature 8."""
        from green.agent import execute_test_against_buggy

        buggy_impl = (temp_buggy_task / "implementation" / "buggy.py").read_text()

        result = execute_test_against_buggy(
            test_code=good_test_code_detecting_bug,
            buggy_implementation=buggy_impl,
            track="tdd",
        )

        # Should use same isolated environment approach
        assert result is not None
        # Should have same result structure
        assert hasattr(result, "exit_code")
        assert hasattr(result, "stdout")
        assert hasattr(result, "stderr")
        assert hasattr(result, "execution_time")
        assert hasattr(result, "passed")

    def test_timeout_applies_to_buggy_execution(self, temp_buggy_task: Path) -> None:
        """Same 30-second timeout applies to buggy.py execution."""
        from green.agent import execute_test_against_buggy

        buggy_impl = (temp_buggy_task / "implementation" / "buggy.py").read_text()

        timeout_test = """
import time

def test_timeout():
    time.sleep(60)  # Exceeds 30-second timeout
    assert True
"""

        result = execute_test_against_buggy(
            test_code=timeout_test,
            buggy_implementation=buggy_impl,
            track="tdd",
        )

        # Should timeout and fail
        assert result.passed is False
        assert result.execution_time <= 35  # Allow overhead


class TestFailureClassification:
    """Verify failure_type correctly reflects the cause of test failure."""

    def test_passing_tests_report_no_failure(self, temp_tdd_task: Path) -> None:
        """When tests pass, failure_type is 'none'."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()
        test_code = """
def test_works():
    from correct import example_function
    assert example_function(5) == 10
"""
        result = execute_test_against_correct(
            test_code=test_code, correct_implementation=correct_impl, track="tdd"
        )
        assert result.passed is True
        assert result.failure_type == "none"

    def test_assertion_failure_detected_as_assertion(self, temp_buggy_task: Path) -> None:
        """When tests fail on assertions, failure_type is 'assertion'."""
        from green.agent import execute_test_against_buggy

        buggy_impl = (temp_buggy_task / "implementation" / "buggy.py").read_text()
        test_code = """
def test_detects_bug():
    from buggy import example_function
    assert example_function(5) == 10
"""
        result = execute_test_against_buggy(
            test_code=test_code, buggy_implementation=buggy_impl, track="tdd"
        )
        assert result.passed is False
        assert result.failure_type == "assertion"

    def test_syntax_error_detected_as_infrastructure(self, temp_tdd_task: Path) -> None:
        """When test code has syntax errors, failure_type is 'infrastructure'."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()
        test_code = """
def test_broken(
    # missing closing paren and colon
"""
        result = execute_test_against_correct(
            test_code=test_code, correct_implementation=correct_impl, track="tdd"
        )
        assert result.passed is False
        assert result.failure_type == "infrastructure"

    def test_import_error_detected_as_infrastructure(self, temp_tdd_task: Path) -> None:
        """When test code imports a non-existent module, failure_type is 'infrastructure'."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()
        test_code = """
from nonexistent_module import something

def test_import():
    assert something() == 42
"""
        result = execute_test_against_correct(
            test_code=test_code, correct_implementation=correct_impl, track="tdd"
        )
        assert result.passed is False
        assert result.failure_type == "infrastructure"

    def test_timeout_detected_as_timeout(self, temp_tdd_task: Path) -> None:
        """When test exceeds timeout, failure_type is 'timeout'."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()
        test_code = """
import time

def test_hangs():
    time.sleep(60)
"""
        result = execute_test_against_correct(
            test_code=test_code, correct_implementation=correct_impl, track="tdd"
        )
        assert result.passed is False
        assert result.failure_type == "timeout"

    def test_empty_test_file_is_infrastructure(self, temp_tdd_task: Path) -> None:
        """An empty test file with no test functions is classified as infrastructure."""
        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()
        result = execute_test_against_correct(
            test_code="", correct_implementation=correct_impl, track="tdd"
        )
        assert result.passed is False
        assert result.failure_type == "infrastructure"

    def test_bug_missed_reports_no_failure(self, temp_buggy_task: Path) -> None:
        """When weak tests pass against buggy code (miss the bug), failure_type is 'none'."""
        from green.agent import execute_test_against_buggy

        buggy_impl = (temp_buggy_task / "implementation" / "buggy.py").read_text()
        test_code = """
def test_weak():
    from buggy import example_function
    assert isinstance(example_function(5), int)
"""
        result = execute_test_against_buggy(
            test_code=test_code, buggy_implementation=buggy_impl, track="tdd"
        )
        assert result.passed is True
        assert result.failure_type == "none"

    def test_failure_output_contains_relevant_details(self, temp_buggy_task: Path) -> None:
        """Assertion failures include the failing test name and assertion in output."""
        from green.agent import execute_test_against_buggy

        buggy_impl = (temp_buggy_task / "implementation" / "buggy.py").read_text()
        test_code = """
def test_detects_off_by_one():
    from buggy import example_function
    assert example_function(0) == 0
"""
        result = execute_test_against_buggy(
            test_code=test_code, buggy_implementation=buggy_impl, track="tdd"
        )
        assert result.failure_type == "assertion"
        # pytest -v output should contain the test name
        assert "test_detects_off_by_one" in result.stdout
        # Should contain assertion detail
        assert "assert" in result.stdout.lower()


class TestFailureClassificationSnapshots:
    """Snapshot-based tests for failure_type using inline-snapshot."""

    def test_passing_snapshot(self, temp_tdd_task: Path) -> None:
        """Snapshot: passing tests produce failure_type 'none'."""
        from inline_snapshot import snapshot

        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()
        test_code = """
def test_works():
    from correct import example_function
    assert example_function(5) == 10
"""
        result = execute_test_against_correct(
            test_code=test_code, correct_implementation=correct_impl, track="tdd"
        )
        assert result.failure_type == snapshot("none")
        assert result.passed == snapshot(True)

    def test_assertion_failure_snapshot(self, temp_buggy_task: Path) -> None:
        """Snapshot: assertion failures against buggy code."""
        from inline_snapshot import snapshot

        from green.agent import execute_test_against_buggy

        buggy_impl = (temp_buggy_task / "implementation" / "buggy.py").read_text()
        test_code = """
def test_detects_bug():
    from buggy import example_function
    assert example_function(5) == 10
"""
        result = execute_test_against_buggy(
            test_code=test_code, buggy_implementation=buggy_impl, track="tdd"
        )
        assert result.failure_type == snapshot("assertion")
        assert result.exit_code == snapshot(1)

    def test_syntax_error_snapshot(self, temp_tdd_task: Path) -> None:
        """Snapshot: syntax errors produce infrastructure failure."""
        from inline_snapshot import snapshot

        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()
        test_code = "def test_broken(\n"
        result = execute_test_against_correct(
            test_code=test_code, correct_implementation=correct_impl, track="tdd"
        )
        assert result.failure_type == snapshot("infrastructure")
        assert result.passed == snapshot(False)

    def test_import_error_snapshot(self, temp_tdd_task: Path) -> None:
        """Snapshot: import errors produce infrastructure failure."""
        from inline_snapshot import snapshot

        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()
        test_code = """
from nonexistent import foo

def test_foo():
    assert foo() == 1
"""
        result = execute_test_against_correct(
            test_code=test_code, correct_implementation=correct_impl, track="tdd"
        )
        assert result.failure_type == snapshot("infrastructure")


class TestFailureClassificationProperties:
    """Property-based tests: executor never crashes on arbitrary input."""

    def test_arbitrary_test_code_never_crashes(self, temp_tdd_task: Path) -> None:
        """Any string as test code produces a valid TestExecutionResult."""
        from hypothesis import given, settings
        from hypothesis import strategies as st

        from green.agent import execute_test_against_correct

        correct_impl = (temp_tdd_task / "implementation" / "correct.py").read_text()

        @given(test_code=st.text(max_size=200))
        @settings(max_examples=10, deadline=60000)
        def check(test_code: str) -> None:
            result = execute_test_against_correct(
                test_code=test_code, correct_implementation=correct_impl, track="tdd"
            )
            assert result.failure_type in {"none", "assertion", "infrastructure", "timeout"}
            assert result.passed == (result.exit_code == 0)
            assert result.execution_time >= 0

        check()

    def test_arbitrary_implementation_never_crashes(self, temp_tdd_task: Path) -> None:
        """Any string as implementation produces a valid TestExecutionResult."""
        from hypothesis import given, settings
        from hypothesis import strategies as st

        from green.agent import execute_test_against_correct

        test_code = """
def test_simple():
    from correct import example_function
    assert example_function(5) == 10
"""

        @given(impl=st.text(max_size=200))
        @settings(max_examples=10, deadline=60000)
        def check(impl: str) -> None:
            result = execute_test_against_correct(
                test_code=test_code, correct_implementation=impl, track="tdd"
            )
            assert result.failure_type in {"none", "assertion", "infrastructure", "timeout"}
            assert result.passed == (result.exit_code == 0)
            assert result.execution_time >= 0

        check()
