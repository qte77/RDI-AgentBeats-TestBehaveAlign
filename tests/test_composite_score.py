"""Tests for composite score calculation (STORY-012).

Following TDD RED phase - these tests MUST fail initially.
Tests cover calculating weighted composite score to rank test quality.

Formula: score = (0.60 * mutation_score) + (0.40 * fault_detection_rate)
"""

import pytest
from pydantic import ValidationError


class TestCompositeScoreModel:
    """Test suite for CompositeScore Pydantic model."""

    def test_composite_score_model_creation(self) -> None:
        """CompositeScore model can be created with valid fields."""
        from green.models import CompositeScore

        result = CompositeScore(mutation_score=0.8, fault_detection_rate=0.6, score=0.72)

        assert result.mutation_score == 0.8
        assert result.fault_detection_rate == 0.6
        assert result.score == 0.72

    def test_composite_score_model_defaults_to_zero(self) -> None:
        """CompositeScore model defaults all fields to 0.0."""
        from green.models import CompositeScore

        result = CompositeScore()

        assert result.mutation_score == 0.0
        assert result.fault_detection_rate == 0.0
        assert result.score == 0.0

    def test_composite_score_model_is_frozen(self) -> None:
        """CompositeScore model is immutable after creation."""
        from green.models import CompositeScore

        result = CompositeScore(mutation_score=0.5, fault_detection_rate=0.5, score=0.5)

        with pytest.raises(Exception):
            result.score = 0.9  # type: ignore[misc]

    def test_composite_score_mutation_score_out_of_range_raises(self) -> None:
        """CompositeScore rejects mutation_score outside [0.0, 1.0]."""
        from green.models import CompositeScore

        with pytest.raises(ValidationError):
            CompositeScore(mutation_score=1.5, fault_detection_rate=0.5, score=0.5)

    def test_composite_score_fault_detection_rate_out_of_range_raises(self) -> None:
        """CompositeScore rejects fault_detection_rate outside [0.0, 1.0]."""
        from green.models import CompositeScore

        with pytest.raises(ValidationError):
            CompositeScore(mutation_score=0.5, fault_detection_rate=-0.1, score=0.5)

    def test_composite_score_score_out_of_range_raises(self) -> None:
        """CompositeScore rejects score outside [0.0, 1.0]."""
        from green.models import CompositeScore

        with pytest.raises(ValidationError):
            CompositeScore(mutation_score=0.5, fault_detection_rate=0.5, score=1.1)

    def test_composite_score_boundary_values_accepted(self) -> None:
        """CompositeScore accepts boundary values 0.0 and 1.0."""
        from green.models import CompositeScore

        low = CompositeScore(mutation_score=0.0, fault_detection_rate=0.0, score=0.0)
        high = CompositeScore(mutation_score=1.0, fault_detection_rate=1.0, score=1.0)

        assert low.score == 0.0
        assert high.score == 1.0


class TestCompositeScoreCalculation:
    """Test suite for calculate_composite_score function."""

    def test_perfect_scores_give_1_0(self) -> None:
        """Perfect mutation and fault detection scores produce composite score of 1.0."""
        from green.agent import calculate_composite_score

        result = calculate_composite_score(mutation_score=1.0, fault_detection_rate=1.0)

        assert result.score == 1.0

    def test_zero_scores_give_0_0(self) -> None:
        """Zero mutation and fault detection scores produce composite score of 0.0."""
        from green.agent import calculate_composite_score

        result = calculate_composite_score(mutation_score=0.0, fault_detection_rate=0.0)

        assert result.score == 0.0

    def test_formula_weighted_calculation(self) -> None:
        """Composite score uses formula: 0.60 * mutation + 0.40 * fault_detection."""
        from green.agent import calculate_composite_score

        # 0.60 * 0.8 + 0.40 * 0.5 = 0.48 + 0.20 = 0.68
        result = calculate_composite_score(mutation_score=0.8, fault_detection_rate=0.5)

        assert result.score == 0.68

    def test_formula_mutation_weight_is_0_60(self) -> None:
        """Mutation score has weight 0.60."""
        from green.agent import calculate_composite_score

        # 0.60 * 1.0 + 0.40 * 0.0 = 0.60
        result = calculate_composite_score(mutation_score=1.0, fault_detection_rate=0.0)

        assert result.score == 0.60

    def test_formula_fault_detection_weight_is_0_40(self) -> None:
        """Fault detection rate has weight 0.40."""
        from green.agent import calculate_composite_score

        # 0.60 * 0.0 + 0.40 * 1.0 = 0.40
        result = calculate_composite_score(mutation_score=0.0, fault_detection_rate=1.0)

        assert result.score == 0.40

    def test_score_rounded_to_2_decimal_places(self) -> None:
        """Final score is rounded to 2 decimal places."""
        from green.agent import calculate_composite_score

        # 0.60 * 0.333 + 0.40 * 0.333 = 0.1998 + 0.1332 = 0.333 -> rounds to 0.33
        result = calculate_composite_score(mutation_score=0.333, fault_detection_rate=0.333)

        assert result.score == round((0.60 * 0.333) + (0.40 * 0.333), 2)

    def test_result_includes_component_scores(self) -> None:
        """Result includes both component scores alongside final score."""
        from green.agent import calculate_composite_score

        result = calculate_composite_score(mutation_score=0.7, fault_detection_rate=0.9)

        assert result.mutation_score == 0.7
        assert result.fault_detection_rate == 0.9

    def test_returns_composite_score_model(self) -> None:
        """calculate_composite_score returns a CompositeScore instance."""
        from green.agent import calculate_composite_score
        from green.models import CompositeScore

        result = calculate_composite_score(mutation_score=0.5, fault_detection_rate=0.5)

        assert isinstance(result, CompositeScore)


class TestCompositeScoreEdgeCases:
    """Test suite for edge cases in composite score calculation."""

    def test_missing_mutation_score_defaults_to_zero(self) -> None:
        """Missing mutation_score defaults to 0.0."""
        from green.agent import calculate_composite_score

        # 0.60 * 0.0 + 0.40 * 1.0 = 0.40
        result = calculate_composite_score(fault_detection_rate=1.0)

        assert result.mutation_score == 0.0
        assert result.score == 0.40

    def test_missing_fault_detection_rate_defaults_to_zero(self) -> None:
        """Missing fault_detection_rate defaults to 0.0."""
        from green.agent import calculate_composite_score

        # 0.60 * 1.0 + 0.40 * 0.0 = 0.60
        result = calculate_composite_score(mutation_score=1.0)

        assert result.fault_detection_rate == 0.0
        assert result.score == 0.60

    def test_no_arguments_defaults_all_to_zero(self) -> None:
        """No arguments produces all-zero composite score."""
        from green.agent import calculate_composite_score

        result = calculate_composite_score()

        assert result.mutation_score == 0.0
        assert result.fault_detection_rate == 0.0
        assert result.score == 0.0


class TestCompositeScoreSnapshots:
    """Snapshot-based tests for composite score calculation."""

    def test_perfect_score_snapshot(self) -> None:
        """Snapshot: perfect inputs yield 1.0."""
        from inline_snapshot import snapshot

        from green.agent import calculate_composite_score

        result = calculate_composite_score(mutation_score=1.0, fault_detection_rate=1.0)
        assert result.score == snapshot(1.0)

    def test_zero_score_snapshot(self) -> None:
        """Snapshot: zero inputs yield 0.0."""
        from inline_snapshot import snapshot

        from green.agent import calculate_composite_score

        result = calculate_composite_score(mutation_score=0.0, fault_detection_rate=0.0)
        assert result.score == snapshot(0.0)

    def test_typical_score_snapshot(self) -> None:
        """Snapshot: typical inputs (0.8 mutation, 0.6 fault) yield 0.72."""
        from inline_snapshot import snapshot

        from green.agent import calculate_composite_score

        # 0.60 * 0.8 + 0.40 * 0.6 = 0.48 + 0.24 = 0.72
        result = calculate_composite_score(mutation_score=0.8, fault_detection_rate=0.6)
        assert result.score == snapshot(0.72)

    def test_mutation_only_score_snapshot(self) -> None:
        """Snapshot: mutation score only yields 0.60."""
        from inline_snapshot import snapshot

        from green.agent import calculate_composite_score

        result = calculate_composite_score(mutation_score=1.0, fault_detection_rate=0.0)
        assert result.score == snapshot(0.6)


class TestCompositeScoreProperties:
    """Property-based tests for composite score calculation."""

    def test_score_always_in_valid_range(self) -> None:
        """Composite score is always in [0.0, 1.0] for valid inputs."""
        from hypothesis import given, settings
        from hypothesis import strategies as st

        from green.agent import calculate_composite_score

        @given(
            mutation=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
            fault=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        )
        @settings(max_examples=100)
        def check(mutation: float, fault: float) -> None:
            result = calculate_composite_score(
                mutation_score=mutation, fault_detection_rate=fault
            )
            assert 0.0 <= result.score <= 1.0

        check()

    def test_score_monotone_in_mutation(self) -> None:
        """Higher mutation score never decreases composite score (fault fixed)."""
        from hypothesis import given, settings
        from hypothesis import strategies as st

        from green.agent import calculate_composite_score

        @given(
            low=st.floats(min_value=0.0, max_value=0.9, allow_nan=False),
            high=st.floats(min_value=0.1, max_value=1.0, allow_nan=False),
            fault=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        )
        @settings(max_examples=50)
        def check(low: float, high: float, fault: float) -> None:
            if low > high:
                low, high = high, low
            r_low = calculate_composite_score(mutation_score=low, fault_detection_rate=fault)
            r_high = calculate_composite_score(mutation_score=high, fault_detection_rate=fault)
            assert r_low.score <= r_high.score

        check()

    def test_score_monotone_in_fault_detection(self) -> None:
        """Higher fault detection rate never decreases composite score (mutation fixed)."""
        from hypothesis import given, settings
        from hypothesis import strategies as st

        from green.agent import calculate_composite_score

        @given(
            low=st.floats(min_value=0.0, max_value=0.9, allow_nan=False),
            high=st.floats(min_value=0.1, max_value=1.0, allow_nan=False),
            mutation=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        )
        @settings(max_examples=50)
        def check(low: float, high: float, mutation: float) -> None:
            if low > high:
                low, high = high, low
            r_low = calculate_composite_score(
                mutation_score=mutation, fault_detection_rate=low
            )
            r_high = calculate_composite_score(
                mutation_score=mutation, fault_detection_rate=high
            )
            assert r_low.score <= r_high.score

        check()
