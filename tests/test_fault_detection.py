"""Tests for fault detection score calculation (STORY-010).

Following TDD RED phase - these tests MUST fail initially.
Tests cover calculating fault detection rate to measure test effectiveness.
"""

import pytest

from green.models import TestExecutionResult


@pytest.fixture
def passed_correct_result() -> TestExecutionResult:
    """Test result showing tests passed against correct implementation."""
    return TestExecutionResult(
        exit_code=0,
        stdout="test passed",
        stderr="",
        execution_time=0.5,
        passed=True,
    )


@pytest.fixture
def failed_correct_result() -> TestExecutionResult:
    """Test result showing tests failed against correct implementation."""
    return TestExecutionResult(
        exit_code=1,
        stdout="test failed",
        stderr="AssertionError",
        execution_time=0.3,
        passed=False,
    )


@pytest.fixture
def failed_buggy_result() -> TestExecutionResult:
    """Test result showing tests failed against buggy implementation (bug detected)."""
    return TestExecutionResult(
        exit_code=1,
        stdout="test failed",
        stderr="AssertionError: bug detected",
        execution_time=0.4,
        passed=False,
    )


@pytest.fixture
def passed_buggy_result() -> TestExecutionResult:
    """Test result showing tests passed against buggy implementation (bug missed)."""
    return TestExecutionResult(
        exit_code=0,
        stdout="test passed",
        stderr="",
        execution_time=0.5,
        passed=True,
    )


class TestFaultDetectionScoreCalculation:
    """Test suite for calculating fault detection score per task."""

    def test_fault_detection_perfect_score(
        self, passed_correct_result: TestExecutionResult, failed_buggy_result: TestExecutionResult
    ) -> None:
        """Calculate fault_detection = 1.0 when tests pass correct AND fail buggy."""
        from green.agent import calculate_fault_detection_score

        # Perfect scenario: tests pass on correct, fail on buggy
        score = calculate_fault_detection_score(
            correct_result=passed_correct_result, buggy_result=failed_buggy_result
        )

        assert score == 1.0

    def test_fault_detection_zero_score_missed_bug(
        self, passed_correct_result: TestExecutionResult, passed_buggy_result: TestExecutionResult
    ) -> None:
        """Calculate fault_detection = 0.0 when tests pass both correct and buggy (missed bug)."""
        from green.agent import calculate_fault_detection_score

        # Tests passed on both correct and buggy - failed to detect bug
        score = calculate_fault_detection_score(
            correct_result=passed_correct_result, buggy_result=passed_buggy_result
        )

        assert score == 0.0

    def test_fault_detection_zero_score_failed_correct(
        self, failed_correct_result: TestExecutionResult, failed_buggy_result: TestExecutionResult
    ) -> None:
        """Calculate fault_detection = 0.0 when tests fail correct implementation."""
        from green.agent import calculate_fault_detection_score

        # Tests failed on correct - tests themselves are broken
        score = calculate_fault_detection_score(
            correct_result=failed_correct_result, buggy_result=failed_buggy_result
        )

        assert score == 0.0

    def test_fault_detection_zero_score_both_failed_correct_passed_buggy(
        self, failed_correct_result: TestExecutionResult, passed_buggy_result: TestExecutionResult
    ) -> None:
        """Calculate fault_detection = 0.0 when tests fail correct AND pass buggy."""
        from green.agent import calculate_fault_detection_score

        # Edge case: failed correct, passed buggy
        score = calculate_fault_detection_score(
            correct_result=failed_correct_result, buggy_result=passed_buggy_result
        )

        assert score == 0.0


class TestFaultDetectionEdgeCases:
    """Test suite for handling edge cases in fault detection."""

    def test_handle_none_correct_result(self, failed_buggy_result: TestExecutionResult) -> None:
        """Handle edge case where correct_result is None."""
        from green.agent import calculate_fault_detection_score

        # Edge case: missing correct result
        score = calculate_fault_detection_score(
            correct_result=None, buggy_result=failed_buggy_result
        )

        assert score == 0.0

    def test_handle_none_buggy_result(self, passed_correct_result: TestExecutionResult) -> None:
        """Handle edge case where buggy_result is None."""
        from green.agent import calculate_fault_detection_score

        # Edge case: missing buggy result
        score = calculate_fault_detection_score(
            correct_result=passed_correct_result, buggy_result=None
        )

        assert score == 0.0

    def test_handle_both_results_none(self) -> None:
        """Handle edge case where both results are None."""
        from green.agent import calculate_fault_detection_score

        # Edge case: both missing
        score = calculate_fault_detection_score(correct_result=None, buggy_result=None)

        assert score == 0.0


class TestFaultDetectionScoreValidation:
    """Test suite for validating fault detection score using Pydantic."""

    def test_score_is_float(
        self, passed_correct_result: TestExecutionResult, failed_buggy_result: TestExecutionResult
    ) -> None:
        """Fault detection score should be a float."""
        from green.agent import calculate_fault_detection_score

        score = calculate_fault_detection_score(
            correct_result=passed_correct_result, buggy_result=failed_buggy_result
        )

        assert isinstance(score, float)

    def test_score_in_valid_range(
        self, passed_correct_result: TestExecutionResult, failed_buggy_result: TestExecutionResult
    ) -> None:
        """Fault detection score should be in range [0.0, 1.0]."""
        from green.agent import calculate_fault_detection_score

        score = calculate_fault_detection_score(
            correct_result=passed_correct_result, buggy_result=failed_buggy_result
        )

        assert 0.0 <= score <= 1.0


class TestFaultDetectionAggregation:
    """Test suite for aggregating fault detection scores across multiple tasks."""

    def test_aggregate_multiple_perfect_scores(self) -> None:
        """Aggregate fault detection scores with simple averaging - all perfect."""
        from green.agent import aggregate_fault_detection_scores

        scores = [1.0, 1.0, 1.0]
        average = aggregate_fault_detection_scores(scores)

        assert average == 1.0

    def test_aggregate_mixed_scores(self) -> None:
        """Aggregate fault detection scores with simple averaging - mixed scores."""
        from green.agent import aggregate_fault_detection_scores

        scores = [1.0, 0.0, 1.0, 0.0]
        average = aggregate_fault_detection_scores(scores)

        assert average == 0.5

    def test_aggregate_all_zero_scores(self) -> None:
        """Aggregate fault detection scores with simple averaging - all zero."""
        from green.agent import aggregate_fault_detection_scores

        scores = [0.0, 0.0, 0.0]
        average = aggregate_fault_detection_scores(scores)

        assert average == 0.0

    def test_aggregate_empty_scores(self) -> None:
        """Aggregate fault detection scores with empty list - should return 0.0."""
        from green.agent import aggregate_fault_detection_scores

        scores = []
        average = aggregate_fault_detection_scores(scores)

        assert average == 0.0

    def test_aggregate_single_score(self) -> None:
        """Aggregate fault detection scores with single score."""
        from green.agent import aggregate_fault_detection_scores

        scores = [0.75]
        average = aggregate_fault_detection_scores(scores)

        assert average == 0.75


class TestFaultDetectionSnapshots:
    """Snapshot-based tests for fault detection scoring."""

    def test_perfect_detection_snapshot(
        self, passed_correct_result: TestExecutionResult, failed_buggy_result: TestExecutionResult
    ) -> None:
        """Snapshot: perfect detection returns 1.0."""
        from inline_snapshot import snapshot

        from green.agent import calculate_fault_detection_score

        score = calculate_fault_detection_score(
            correct_result=passed_correct_result, buggy_result=failed_buggy_result
        )
        assert score == snapshot(1.0)

    def test_missed_bug_snapshot(
        self, passed_correct_result: TestExecutionResult, passed_buggy_result: TestExecutionResult
    ) -> None:
        """Snapshot: missed bug returns 0.0."""
        from inline_snapshot import snapshot

        from green.agent import calculate_fault_detection_score

        score = calculate_fault_detection_score(
            correct_result=passed_correct_result, buggy_result=passed_buggy_result
        )
        assert score == snapshot(0.0)

    def test_broken_tests_snapshot(
        self, failed_correct_result: TestExecutionResult, failed_buggy_result: TestExecutionResult
    ) -> None:
        """Snapshot: broken tests (failed correct) returns 0.0."""
        from inline_snapshot import snapshot

        from green.agent import calculate_fault_detection_score

        score = calculate_fault_detection_score(
            correct_result=failed_correct_result, buggy_result=failed_buggy_result
        )
        assert score == snapshot(0.0)

    def test_aggregate_snapshot(self) -> None:
        """Snapshot: aggregation of mixed scores."""
        from inline_snapshot import snapshot

        from green.agent import aggregate_fault_detection_scores

        assert aggregate_fault_detection_scores([1.0, 0.0, 1.0]) == snapshot(0.6666666666666666)
        assert aggregate_fault_detection_scores([]) == snapshot(0.0)


class TestFaultDetectionProperties:
    """Property-based tests for fault detection scoring."""

    def test_score_always_binary(self) -> None:
        """Fault detection score is always exactly 0.0 or 1.0."""
        from hypothesis import given, settings
        from hypothesis import strategies as st

        from green.agent import calculate_fault_detection_score

        result_strategy = st.builds(
            TestExecutionResult,
            exit_code=st.integers(min_value=0, max_value=4),
            stdout=st.just(""),
            stderr=st.just(""),
            execution_time=st.floats(min_value=0.0, max_value=10.0),
            passed=st.booleans(),
            failure_type=st.sampled_from(["none", "assertion", "infrastructure", "timeout"]),
        )

        @given(correct=result_strategy, buggy=result_strategy)
        @settings(max_examples=50)
        def check(correct: TestExecutionResult, buggy: TestExecutionResult) -> None:
            score = calculate_fault_detection_score(correct_result=correct, buggy_result=buggy)
            assert score in {0.0, 1.0}

        check()

    def test_aggregate_in_valid_range(self) -> None:
        """Aggregated score is always in [0.0, 1.0] for valid inputs."""
        from hypothesis import given, settings
        from hypothesis import strategies as st

        from green.agent import aggregate_fault_detection_scores

        @given(scores=st.lists(st.sampled_from([0.0, 1.0]), max_size=20))
        @settings(max_examples=50)
        def check(scores: list[float]) -> None:
            result = aggregate_fault_detection_scores(scores)
            assert 0.0 <= result <= 1.0

        check()

    def test_none_results_always_zero(self) -> None:
        """Any None input always produces 0.0."""
        from hypothesis import given, settings
        from hypothesis import strategies as st

        from green.agent import calculate_fault_detection_score

        result_or_none = st.one_of(
            st.none(),
            st.builds(
                TestExecutionResult,
                exit_code=st.integers(min_value=0, max_value=4),
                stdout=st.just(""),
                stderr=st.just(""),
                execution_time=st.floats(min_value=0.0, max_value=10.0),
                passed=st.booleans(),
                failure_type=st.sampled_from(["none", "assertion", "infrastructure", "timeout"]),
            ),
        )

        @given(correct=st.none(), buggy=result_or_none)
        @settings(max_examples=20)
        def check_none_correct(
            correct: TestExecutionResult | None, buggy: TestExecutionResult | None
        ) -> None:
            assert calculate_fault_detection_score(correct_result=correct, buggy_result=buggy) == 0.0

        @given(correct=result_or_none, buggy=st.none())
        @settings(max_examples=20)
        def check_none_buggy(
            correct: TestExecutionResult | None, buggy: TestExecutionResult | None
        ) -> None:
            assert calculate_fault_detection_score(correct_result=correct, buggy_result=buggy) == 0.0

        check_none_correct()
        check_none_buggy()
