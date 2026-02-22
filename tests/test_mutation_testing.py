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
    return "def add(a: int, b: int) -> int:\n    return a + b\n"


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

        timeout_err = subprocess.TimeoutExpired("mutmut", 600)
        with patch("green.agent.subprocess.run", side_effect=timeout_err):
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

    def test_accepts_bdd_track(self, simple_test_code: str, simple_implementation: str) -> None:
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
# Property-based tests
# ---------------------------------------------------------------------------


class TestMutmutConfiguration:
    """Test that mutmut is configured with correct pyproject.toml settings."""

    def test_per_mutant_timeout_in_pyproject_toml(
        self, simple_test_code: str, simple_implementation: str
    ) -> None:
        """pyproject.toml is written with timeout = 10 for per-mutant timeout."""
        import tomllib
        from pathlib import Path
        from unittest.mock import MagicMock, patch

        from green.agent import run_mutation_testing

        captured_toml: list[str] = []

        def capture_run(_cmd: object, **kwargs: object) -> MagicMock:
            cwd = kwargs.get("cwd")
            if cwd:
                toml_path = Path(str(cwd)) / "pyproject.toml"
                if toml_path.exists():
                    captured_toml.append(toml_path.read_text())
            mock = MagicMock()
            mock.returncode = 0
            mock.stdout = "2/2 mutants killed\n"
            mock.stderr = ""
            return mock

        with patch("green.agent.subprocess.run", side_effect=capture_run):
            run_mutation_testing(simple_test_code, simple_implementation, "tdd")

        assert len(captured_toml) > 0
        config = tomllib.loads(captured_toml[0])
        assert config["tool"]["mutmut"]["timeout"] == 10


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
