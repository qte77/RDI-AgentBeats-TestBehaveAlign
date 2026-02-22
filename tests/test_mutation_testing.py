"""Tests for mutation testing integration (STORY-011).

Following TDD RED phase - these tests MUST fail initially.
Tests cover running mutmut mutation testing to measure test thoroughness.
"""

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Sample code fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def simple_implementation() -> str:
    """Simple correct implementation for mutation testing."""
    return (
        "def add(a: int, b: int) -> int:\n"
        "    return a + b\n"
    )


@pytest.fixture
def simple_test_code() -> str:
    """Simple test code that tests the add function."""
    return (
        "from correct import add\n"
        "\n"
        "def test_add_positive():\n"
        "    assert add(1, 2) == 3\n"
        "\n"
        "def test_add_zero():\n"
        "    assert add(0, 0) == 0\n"
        "\n"
        "def test_add_negative():\n"
        "    assert add(-1, 1) == 0\n"
    )


@pytest.fixture
def mutmut_all_killed_output() -> str:
    """Simulated mutmut output when all mutants are killed."""
    return "4/4 mutants killed\n"


@pytest.fixture
def mutmut_partial_output() -> str:
    """Simulated mutmut output when some mutants survived."""
    return "3/4 mutants killed\n"


@pytest.fixture
def mutmut_none_killed_output() -> str:
    """Simulated mutmut output when no mutants are killed."""
    return "0/4 mutants killed\n"


# ---------------------------------------------------------------------------
# Tests for MutationResult model
# ---------------------------------------------------------------------------


class TestMutationResultModel:
    """Test suite for MutationResult Pydantic model."""

    def test_mutation_result_has_required_fields(self) -> None:
        """MutationResult model has killed, survived, total, mutation_score fields."""
        from green.models import MutationResult

        result = MutationResult(killed=3, survived=1, total=4, mutation_score=0.75)

        assert result.killed == 3
        assert result.survived == 1
        assert result.total == 4
        assert result.mutation_score == 0.75

    def test_mutation_result_error_field_optional(self) -> None:
        """MutationResult error field is optional (None by default)."""
        from green.models import MutationResult

        result = MutationResult(killed=0, survived=0, total=0, mutation_score=0.0)

        assert result.error is None

    def test_mutation_result_error_field_can_be_set(self) -> None:
        """MutationResult error field can hold an error message."""
        from green.models import MutationResult

        result = MutationResult(
            killed=0, survived=0, total=0, mutation_score=0.0, error="mutmut unavailable"
        )

        assert result.error == "mutmut unavailable"

    def test_mutation_result_is_immutable(self) -> None:
        """MutationResult is immutable (frozen Pydantic model)."""
        from green.models import MutationResult

        result = MutationResult(killed=2, survived=2, total=4, mutation_score=0.5)

        with pytest.raises(Exception):
            result.killed = 3  # type: ignore[misc]

    def test_mutation_score_is_float(self) -> None:
        """MutationResult mutation_score is a float."""
        from green.models import MutationResult

        result = MutationResult(killed=1, survived=3, total=4, mutation_score=0.25)

        assert isinstance(result.mutation_score, float)

    def test_mutation_result_defaults(self) -> None:
        """MutationResult can be created with all-zero defaults."""
        from green.models import MutationResult

        result = MutationResult(killed=0, survived=0, total=0, mutation_score=0.0)

        assert result.killed == 0
        assert result.survived == 0
        assert result.total == 0
        assert result.mutation_score == 0.0
        assert result.error is None


# ---------------------------------------------------------------------------
# Tests for run_mutation_testing function
# ---------------------------------------------------------------------------


class TestRunMutationTesting:
    """Test suite for run_mutation_testing function."""

    def test_returns_mutation_result_type(
        self, simple_test_code: str, simple_implementation: str
    ) -> None:
        """run_mutation_testing returns a MutationResult instance."""
        from green.agent import run_mutation_testing
        from green.models import MutationResult

        mock_run = MagicMock()
        mock_run.return_value.stdout = "4/4 mutants killed\n"
        mock_run.return_value.stderr = ""
        mock_run.return_value.returncode = 0

        with patch("green.agent.subprocess.run", mock_run):
            result = run_mutation_testing(simple_test_code, simple_implementation, "tdd")

        assert isinstance(result, MutationResult)

    def test_all_killed_gives_score_one(
        self, simple_test_code: str, simple_implementation: str
    ) -> None:
        """All mutants killed produces mutation_score = 1.0."""
        from green.agent import run_mutation_testing

        mock_run = MagicMock()
        mock_run.return_value.stdout = "4/4 mutants killed\n"
        mock_run.return_value.stderr = ""
        mock_run.return_value.returncode = 0

        with patch("green.agent.subprocess.run", mock_run):
            result = run_mutation_testing(simple_test_code, simple_implementation, "tdd")

        assert result.mutation_score == 1.0
        assert result.killed == 4
        assert result.total == 4

    def test_none_killed_gives_score_zero(
        self, simple_test_code: str, simple_implementation: str
    ) -> None:
        """No mutants killed produces mutation_score = 0.0."""
        from green.agent import run_mutation_testing

        mock_run = MagicMock()
        mock_run.return_value.stdout = "0/4 mutants killed\n"
        mock_run.return_value.stderr = ""
        mock_run.return_value.returncode = 1

        with patch("green.agent.subprocess.run", mock_run):
            result = run_mutation_testing(simple_test_code, simple_implementation, "tdd")

        assert result.mutation_score == 0.0
        assert result.killed == 0
        assert result.total == 4

    def test_partial_kill_gives_correct_score(
        self, simple_test_code: str, simple_implementation: str
    ) -> None:
        """Partial kill (3/4) produces mutation_score = 0.75."""
        from green.agent import run_mutation_testing

        mock_run = MagicMock()
        mock_run.return_value.stdout = "3/4 mutants killed\n"
        mock_run.return_value.stderr = ""
        mock_run.return_value.returncode = 1

        with patch("green.agent.subprocess.run", mock_run):
            result = run_mutation_testing(simple_test_code, simple_implementation, "tdd")

        assert result.mutation_score == pytest.approx(0.75)
        assert result.killed == 3
        assert result.survived == 1
        assert result.total == 4

    def test_handles_mutmut_unavailable(
        self, simple_test_code: str, simple_implementation: str
    ) -> None:
        """Returns zero score with error when mutmut is unavailable."""
        from green.agent import run_mutation_testing

        with patch.dict("sys.modules", {"mutmut": None}):
            result = run_mutation_testing(simple_test_code, simple_implementation, "tdd")

        assert result.mutation_score == 0.0
        assert result.total == 0
        assert result.error is not None
        assert "unavailable" in result.error.lower() or "mutmut" in result.error.lower()

    def test_handles_subprocess_timeout(
        self, simple_test_code: str, simple_implementation: str
    ) -> None:
        """Returns error result when subprocess times out."""
        import subprocess

        from green.agent import run_mutation_testing

        with patch("green.agent.subprocess.run", side_effect=subprocess.TimeoutExpired("mutmut", 600)):
            result = run_mutation_testing(simple_test_code, simple_implementation, "tdd")

        assert result.mutation_score == 0.0
        assert result.error is not None

    def test_handles_subprocess_error(
        self, simple_test_code: str, simple_implementation: str
    ) -> None:
        """Returns error result when subprocess raises an exception."""
        from green.agent import run_mutation_testing

        with patch("green.agent.subprocess.run", side_effect=OSError("mutmut not found")):
            result = run_mutation_testing(simple_test_code, simple_implementation, "tdd")

        assert result.mutation_score == 0.0
        assert result.error is not None

    def test_zero_total_gives_zero_score(
        self, simple_test_code: str, simple_implementation: str
    ) -> None:
        """Zero total mutants produces mutation_score = 0.0 (no division by zero)."""
        from green.agent import run_mutation_testing

        mock_run = MagicMock()
        mock_run.return_value.stdout = "0/0 mutants killed\n"
        mock_run.return_value.stderr = ""
        mock_run.return_value.returncode = 0

        with patch("green.agent.subprocess.run", mock_run):
            result = run_mutation_testing(simple_test_code, simple_implementation, "tdd")

        assert result.mutation_score == 0.0
        assert result.total == 0

    def test_accepts_bdd_track(
        self, simple_test_code: str, simple_implementation: str
    ) -> None:
        """run_mutation_testing accepts bdd track without error."""
        from green.agent import run_mutation_testing

        mock_run = MagicMock()
        mock_run.return_value.stdout = "2/2 mutants killed\n"
        mock_run.return_value.stderr = ""
        mock_run.return_value.returncode = 0

        with patch("green.agent.subprocess.run", mock_run):
            result = run_mutation_testing(simple_test_code, simple_implementation, "bdd")

        assert result.total == 2


# ---------------------------------------------------------------------------
# Tests for _parse_mutmut_output helper
# ---------------------------------------------------------------------------


class TestParseMutmutOutput:
    """Test suite for parsing mutmut output strings."""

    def test_parse_x_of_y_killed_format(self) -> None:
        """Parses 'X/Y mutants killed' format correctly."""
        from green.agent import _parse_mutmut_output

        killed, survived, total = _parse_mutmut_output("3/4 mutants killed\n")

        assert killed == 3
        assert survived == 1
        assert total == 4

    def test_parse_all_killed(self) -> None:
        """Parses output where all mutants are killed."""
        from green.agent import _parse_mutmut_output

        killed, survived, total = _parse_mutmut_output("4/4 mutants killed")

        assert killed == 4
        assert survived == 0
        assert total == 4

    def test_parse_zero_killed(self) -> None:
        """Parses output where no mutants are killed."""
        from green.agent import _parse_mutmut_output

        killed, survived, total = _parse_mutmut_output("0/4 mutants killed")

        assert killed == 0
        assert survived == 4
        assert total == 4

    def test_parse_empty_output(self) -> None:
        """Returns zeros for empty or unparseable output."""
        from green.agent import _parse_mutmut_output

        killed, survived, total = _parse_mutmut_output("")

        assert killed == 0
        assert survived == 0
        assert total == 0

    def test_parse_singular_mutant(self) -> None:
        """Parses 'X/Y mutant killed' (singular) format."""
        from green.agent import _parse_mutmut_output

        killed, survived, total = _parse_mutmut_output("1/1 mutant killed")

        assert killed == 1
        assert total == 1

    def test_parse_killed_survived_format(self) -> None:
        """Parses 'Killed: X\\nSurvived: Y' format as fallback."""
        from green.agent import _parse_mutmut_output

        output = "Killed: 3\nSurvived: 1\n"
        killed, survived, total = _parse_mutmut_output(output)

        assert killed == 3
        assert survived == 1
        assert total == 4


# ---------------------------------------------------------------------------
# Snapshot tests
# ---------------------------------------------------------------------------


class TestMutationTestingSnapshots:
    """Snapshot-based tests for mutation testing scoring."""

    def test_all_killed_snapshot(
        self, simple_test_code: str, simple_implementation: str
    ) -> None:
        """Snapshot: all mutants killed returns score 1.0."""
        from inline_snapshot import snapshot

        from green.agent import run_mutation_testing

        mock_run = MagicMock()
        mock_run.return_value.stdout = "4/4 mutants killed\n"
        mock_run.return_value.stderr = ""
        mock_run.return_value.returncode = 0

        with patch("green.agent.subprocess.run", mock_run):
            result = run_mutation_testing(simple_test_code, simple_implementation, "tdd")

        assert result.mutation_score == snapshot(1.0)
        assert result.killed == snapshot(4)
        assert result.total == snapshot(4)

    def test_partial_kill_snapshot(
        self, simple_test_code: str, simple_implementation: str
    ) -> None:
        """Snapshot: 3/4 mutants killed returns score 0.75."""
        from inline_snapshot import snapshot

        from green.agent import run_mutation_testing

        mock_run = MagicMock()
        mock_run.return_value.stdout = "3/4 mutants killed\n"
        mock_run.return_value.stderr = ""
        mock_run.return_value.returncode = 1

        with patch("green.agent.subprocess.run", mock_run):
            result = run_mutation_testing(simple_test_code, simple_implementation, "tdd")

        assert result.mutation_score == snapshot(0.75)

    def test_unavailable_snapshot(
        self, simple_test_code: str, simple_implementation: str
    ) -> None:
        """Snapshot: mutmut unavailable returns score 0.0 with error."""
        from inline_snapshot import snapshot

        from green.agent import run_mutation_testing

        with patch.dict("sys.modules", {"mutmut": None}):
            result = run_mutation_testing(simple_test_code, simple_implementation, "tdd")

        assert result.mutation_score == snapshot(0.0)
        assert result.total == snapshot(0)


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------


class TestMutationTestingProperties:
    """Property-based tests for mutation testing."""

    def test_mutation_score_always_in_range(self) -> None:
        """Mutation score is always in [0.0, 1.0]."""
        from hypothesis import given, settings
        from hypothesis import strategies as st

        from green.agent import run_mutation_testing

        @given(
            killed=st.integers(min_value=0, max_value=100),
            total=st.integers(min_value=0, max_value=100),
        )
        @settings(max_examples=50)
        def check(killed: int, total: int) -> None:
            if killed > total:
                return  # skip invalid inputs
            mock_run = MagicMock()
            mock_run.return_value.stdout = f"{killed}/{total} mutants killed\n"
            mock_run.return_value.stderr = ""
            mock_run.return_value.returncode = 0 if killed == total else 1

            with patch("green.agent.subprocess.run", mock_run):
                result = run_mutation_testing("# test", "# impl", "tdd")

            assert 0.0 <= result.mutation_score <= 1.0

        check()

    def test_killed_never_exceeds_total(self) -> None:
        """killed count never exceeds total count in MutationResult."""
        from hypothesis import given, settings
        from hypothesis import strategies as st

        from green.agent import run_mutation_testing

        @given(
            killed=st.integers(min_value=0, max_value=20),
            total=st.integers(min_value=0, max_value=20),
        )
        @settings(max_examples=30)
        def check(killed: int, total: int) -> None:
            if killed > total:
                return
            mock_run = MagicMock()
            mock_run.return_value.stdout = f"{killed}/{total} mutants killed\n"
            mock_run.return_value.stderr = ""
            mock_run.return_value.returncode = 0

            with patch("green.agent.subprocess.run", mock_run):
                result = run_mutation_testing("# test", "# impl", "tdd")

            assert result.killed <= result.total

        check()

    def test_score_equals_killed_over_total(self) -> None:
        """mutation_score == killed / total for non-zero total."""
        from hypothesis import given, settings
        from hypothesis import strategies as st

        from green.agent import run_mutation_testing

        @given(
            killed=st.integers(min_value=0, max_value=20),
            extra=st.integers(min_value=0, max_value=20),
        )
        @settings(max_examples=30)
        def check(killed: int, extra: int) -> None:
            total = killed + extra
            if total == 0:
                return
            mock_run = MagicMock()
            mock_run.return_value.stdout = f"{killed}/{total} mutants killed\n"
            mock_run.return_value.stderr = ""
            mock_run.return_value.returncode = 0

            with patch("green.agent.subprocess.run", mock_run):
                result = run_mutation_testing("# test", "# impl", "tdd")

            assert abs(result.mutation_score - killed / total) < 1e-9

        check()
