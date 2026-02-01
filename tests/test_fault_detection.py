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
