"""Tests for BDD track dispatch in test execution (STORY-017).

RED phase - these tests MUST fail initially.
Tests verify that _execute_test_in_isolation accepts track param,
and that BDD track invokes pytest with pytest-bdd plugin loaded.
"""

import inspect
import subprocess
from typing import Any

import pytest

from green.models import TestExecutionResult


@pytest.fixture
def passing_tdd_test() -> str:
    """Minimal TDD test code that passes."""
    return """
def test_add():
    from correct import add
    assert add(1, 2) == 3
"""


@pytest.fixture
def correct_add_impl() -> str:
    """Correct add implementation."""
    return "def add(a: int, b: int) -> int:\n    return a + b\n"


class TestInternalFunctionSignature:
    """Verify _execute_test_in_isolation accepts track parameter."""

    def test_internal_function_has_track_parameter(self) -> None:
        """_execute_test_in_isolation must accept a track parameter."""
        import green.agent as agent_module

        fn = getattr(agent_module, "_execute_test_in_isolation")
        sig = inspect.signature(fn)
        assert "track" in sig.parameters, (
            "_execute_test_in_isolation must accept 'track' parameter"
        )

    def test_track_parameter_has_correct_annotation(self) -> None:
        """track parameter should exist in _execute_test_in_isolation."""
        import green.agent as agent_module

        fn = getattr(agent_module, "_execute_test_in_isolation")
        sig = inspect.signature(fn)
        assert "track" in sig.parameters


class TestTrackPassthrough:
    """Verify public wrappers pass track to _execute_test_in_isolation."""

    def test_execute_against_correct_passes_track(
        self, monkeypatch: pytest.MonkeyPatch, passing_tdd_test: str, correct_add_impl: str
    ) -> None:
        """execute_test_against_correct must pass track to internal function."""
        import green.agent as agent_module

        captured: list[dict[str, Any]] = []

        def mock_execute(
            _test_code: str,
            _implementation: str,
            _impl_filename: str,
            track: str,
        ) -> TestExecutionResult:
            captured.append({"track": track})
            return TestExecutionResult(
                exit_code=0,
                stdout="",
                stderr="",
                execution_time=0.1,
                passed=True,
                failure_type="none",
            )

        monkeypatch.setattr(agent_module, "_execute_test_in_isolation", mock_execute)

        agent_module.execute_test_against_correct(
            test_code=passing_tdd_test, correct_implementation=correct_add_impl, track="bdd"
        )

        assert len(captured) == 1
        assert captured[0]["track"] == "bdd"

    def test_execute_against_buggy_passes_track(
        self, monkeypatch: pytest.MonkeyPatch, passing_tdd_test: str, correct_add_impl: str
    ) -> None:
        """execute_test_against_buggy must pass track to internal function."""
        import green.agent as agent_module

        captured: list[dict[str, Any]] = []

        def mock_execute(
            _test_code: str,
            _implementation: str,
            _impl_filename: str,
            track: str,
        ) -> TestExecutionResult:
            captured.append({"track": track})
            return TestExecutionResult(
                exit_code=1,
                stdout="",
                stderr="",
                execution_time=0.1,
                passed=False,
                failure_type="assertion",
            )

        monkeypatch.setattr(agent_module, "_execute_test_in_isolation", mock_execute)

        agent_module.execute_test_against_buggy(
            test_code=passing_tdd_test, buggy_implementation=correct_add_impl, track="tdd"
        )

        assert len(captured) == 1
        assert captured[0]["track"] == "tdd"


class TestBDDPluginLoading:
    """Verify BDD track loads pytest-bdd plugin in subprocess command."""

    def test_bdd_track_uses_pytest_bdd_flag(
        self,
        monkeypatch: pytest.MonkeyPatch,
        passing_tdd_test: str,
        correct_add_impl: str,
    ) -> None:
        """When track='bdd', subprocess call must include -p pytest_bdd."""
        import green.agent as agent_module

        commands: list[list[str]] = []

        def mock_run(
            cmd: list[str], **_kwargs: Any
        ) -> subprocess.CompletedProcess[str]:
            commands.append(list(cmd))
            return subprocess.CompletedProcess(
                args=cmd, returncode=0, stdout="1 passed", stderr=""
            )

        monkeypatch.setattr(subprocess, "run", mock_run)

        agent_module.execute_test_against_correct(
            test_code=passing_tdd_test, correct_implementation=correct_add_impl, track="bdd"
        )

        assert len(commands) == 1, "Expected exactly one subprocess call"
        cmd = commands[0]
        assert "-p" in cmd, "BDD track must pass -p flag to pytest"
        p_idx = cmd.index("-p")
        assert cmd[p_idx + 1] == "pytest_bdd", (
            "BDD track must load pytest_bdd plugin via -p pytest_bdd"
        )

    def test_tdd_track_does_not_use_pytest_bdd_flag(
        self,
        monkeypatch: pytest.MonkeyPatch,
        passing_tdd_test: str,
        correct_add_impl: str,
    ) -> None:
        """When track='tdd', subprocess command must NOT include -p pytest_bdd."""
        import green.agent as agent_module

        commands: list[list[str]] = []

        def mock_run(
            cmd: list[str], **_kwargs: Any
        ) -> subprocess.CompletedProcess[str]:
            commands.append(list(cmd))
            return subprocess.CompletedProcess(
                args=cmd, returncode=0, stdout="1 passed", stderr=""
            )

        monkeypatch.setattr(subprocess, "run", mock_run)

        agent_module.execute_test_against_correct(
            test_code=passing_tdd_test, correct_implementation=correct_add_impl, track="tdd"
        )

        assert len(commands) == 1
        cmd = commands[0]
        assert "pytest_bdd" not in cmd, "TDD track must not load pytest_bdd plugin"


class TestBDDResultStructure:
    """Verify BDD track captures same result structure as TDD."""

    def test_bdd_result_has_exit_code(self, correct_add_impl: str) -> None:
        """BDD execution result must have exit_code field."""
        from green.agent import execute_test_against_correct

        bdd_test = """
def test_bdd_stub():
    from correct import add
    assert add(1, 2) == 3
"""
        result = execute_test_against_correct(
            test_code=bdd_test, correct_implementation=correct_add_impl, track="bdd"
        )
        assert hasattr(result, "exit_code")

    def test_bdd_result_has_stdout(self, correct_add_impl: str) -> None:
        """BDD execution result must have stdout field."""
        from green.agent import execute_test_against_correct

        bdd_test = """
def test_bdd_stub():
    from correct import add
    assert add(1, 2) == 3
"""
        result = execute_test_against_correct(
            test_code=bdd_test, correct_implementation=correct_add_impl, track="bdd"
        )
        assert hasattr(result, "stdout")
        assert isinstance(result.stdout, str)

    def test_bdd_result_has_stderr(self, correct_add_impl: str) -> None:
        """BDD execution result must have stderr field."""
        from green.agent import execute_test_against_correct

        bdd_test = """
def test_bdd_stub():
    from correct import add
    assert add(1, 2) == 3
"""
        result = execute_test_against_correct(
            test_code=bdd_test, correct_implementation=correct_add_impl, track="bdd"
        )
        assert hasattr(result, "stderr")
        assert isinstance(result.stderr, str)

    def test_bdd_result_has_execution_time(self, correct_add_impl: str) -> None:
        """BDD execution result must have execution_time field."""
        from green.agent import execute_test_against_correct

        bdd_test = """
def test_bdd_stub():
    from correct import add
    assert add(1, 2) == 3
"""
        result = execute_test_against_correct(
            test_code=bdd_test, correct_implementation=correct_add_impl, track="bdd"
        )
        assert hasattr(result, "execution_time")
        assert isinstance(result.execution_time, float)
        assert result.execution_time >= 0


class TestNoFixmeComments:
    """Verify FIXME comments are removed from agent.py."""

    def test_no_fixme_at_line_230(self) -> None:
        """No FIXME comment should exist at agent.py line ~230."""
        from pathlib import Path

        agent_path = Path("src/green/agent.py")
        lines = agent_path.read_text().splitlines()
        for i, line in enumerate(lines, start=1):
            if "FIXME" in line and "track param unused" in line:
                pytest.fail(
                    f"FIXME comment still present at line {i}: {line.strip()}"
                )

    def test_no_fixme_track_unused_in_agent(self) -> None:
        """No 'FIXME: track param unused' should remain in agent.py."""
        from pathlib import Path

        agent_path = Path("src/green/agent.py")
        content = agent_path.read_text()
        assert "FIXME: track param unused" not in content, (
            "FIXME 'track param unused' comments must be removed from agent.py"
        )
