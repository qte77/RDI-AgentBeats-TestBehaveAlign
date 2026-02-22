"""Tests for A2A AgentExecutor implementation.

Following TDD RED phase - these tests MUST fail initially.
Tests cover executor integration with A2A SDK and evaluation orchestration.
"""

import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestGreenAgentExecutor:
    """Test suite for Green Agent executor."""

    def test_executor_inherits_from_agent_executor(
        self, temp_scenario_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Executor should inherit from a2a.server.AgentExecutor."""
        from green.executor import GreenAgentExecutor

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Create executor instance
        executor = GreenAgentExecutor(temp_scenario_file)

        # Verify executor has required A2A methods
        assert hasattr(executor, "execute")
        assert callable(executor.execute)

    def test_executor_loads_settings_from_scenario(
        self, temp_scenario_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Executor should load settings from scenario.toml."""
        from green.executor import GreenAgentExecutor

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Create executor instance
        executor = GreenAgentExecutor(temp_scenario_file)

        # Verify settings are loaded
        assert hasattr(executor, "settings")
        assert executor.settings.track == "tdd"
        assert executor.settings.task_count == 5

    def test_executor_has_cancel_method(
        self, temp_scenario_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Executor should implement cancel method for task cancellation."""
        from green.executor import GreenAgentExecutor

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Create executor instance
        executor = GreenAgentExecutor(temp_scenario_file)

        # Verify cancel method exists
        assert hasattr(executor, "cancel")
        assert callable(executor.cancel)

    def test_executor_validates_scenario_file_exists(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Executor should validate that scenario file exists."""
        from green.executor import GreenAgentExecutor

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Try to create executor with non-existent file
        non_existent_file = tmp_path / "does_not_exist.toml"

        # Should raise error for missing file
        with pytest.raises((FileNotFoundError, ValueError)):
            GreenAgentExecutor(non_existent_file)


def _make_context(task_id: str = "task-123", context_id: str = "ctx-456") -> MagicMock:
    """Create a mock RequestContext with task_id and context_id."""
    context = MagicMock()
    context.task_id = task_id
    context.context_id = context_id
    context.get_user_input.return_value = "test-participant-id"
    return context


def _make_event_queue() -> MagicMock:
    """Create a mock EventQueue that records enqueued events."""
    queue = MagicMock()
    queue.enqueue_event = AsyncMock()
    return queue


def _make_mock_task() -> MagicMock:
    """Create a mock Task object."""
    task = MagicMock()
    task.task_id = "task_001"
    task.spec = "def add(a, b): ..."
    task.correct_implementation = "def add(a, b): return a + b"
    task.buggy_implementation = "def add(a, b): return a - b"
    return task


def _make_test_execution_result(passed: bool) -> MagicMock:
    """Create a mock TestExecutionResult."""
    result = MagicMock()
    result.passed = passed
    result.exit_code = 0 if passed else 1
    result.stdout = ""
    result.stderr = ""
    result.execution_time = 0.1
    return result


def _make_mutation_result(score: float = 0.8) -> MagicMock:
    """Create a mock MutationResult."""
    result = MagicMock()
    result.mutation_score = score
    result.killed = 8
    result.survived = 2
    result.total = 10
    result.error = None
    return result


class TestExecuteMethod:
    """Test suite for execute() method behavior."""

    async def test_execute_calls_messenger_close_in_finally(
        self, temp_scenario_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """execute() must call messenger.close() in a finally block."""
        from green.executor import GreenAgentExecutor

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        executor = GreenAgentExecutor(temp_scenario_file)
        context = _make_context()
        event_queue = _make_event_queue()

        mock_messenger = MagicMock()
        mock_messenger.generate_tests = AsyncMock(return_value="def test_add(): pass")
        mock_messenger.close = AsyncMock()

        with (
            patch("green.executor.PurpleAgentMessenger", return_value=mock_messenger),
            patch("green.executor.load_task", return_value=_make_mock_task()),
            patch(
                "green.executor.execute_test_against_correct",
                return_value=_make_test_execution_result(True),
            ),
            patch(
                "green.executor.execute_test_against_buggy",
                return_value=_make_test_execution_result(False),
            ),
            patch(
                "green.executor.run_mutation_testing",
                return_value=_make_mutation_result(),
            ),
        ):
            await executor.execute(context, event_queue)

        mock_messenger.close.assert_awaited_once()

    async def test_execute_calls_messenger_close_even_on_error(
        self, temp_scenario_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """execute() must call messenger.close() even when an error occurs."""
        from green.executor import GreenAgentExecutor

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        executor = GreenAgentExecutor(temp_scenario_file)
        context = _make_context()
        event_queue = _make_event_queue()

        mock_messenger = MagicMock()
        mock_messenger.close = AsyncMock()

        with (
            patch("green.executor.PurpleAgentMessenger", return_value=mock_messenger),
            patch("green.executor.load_task", side_effect=RuntimeError("task load failed")),
        ):
            await executor.execute(context, event_queue)

        mock_messenger.close.assert_awaited_once()

    async def test_execute_enqueues_artifact_on_success(
        self, temp_scenario_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """execute() should enqueue a result artifact when evaluation succeeds."""
        from a2a.types import TaskArtifactUpdateEvent, TaskStatusUpdateEvent

        from green.executor import GreenAgentExecutor

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        executor = GreenAgentExecutor(temp_scenario_file)
        context = _make_context()
        event_queue = _make_event_queue()

        mock_messenger = MagicMock()
        mock_messenger.generate_tests = AsyncMock(return_value="def test_add(): pass")
        mock_messenger.close = AsyncMock()

        with (
            patch("green.executor.PurpleAgentMessenger", return_value=mock_messenger),
            patch("green.executor.load_task", return_value=_make_mock_task()),
            patch(
                "green.executor.execute_test_against_correct",
                return_value=_make_test_execution_result(True),
            ),
            patch(
                "green.executor.execute_test_against_buggy",
                return_value=_make_test_execution_result(False),
            ),
            patch(
                "green.executor.run_mutation_testing",
                return_value=_make_mutation_result(),
            ),
        ):
            await executor.execute(context, event_queue)

        # Should have enqueued at least one artifact event and one status event
        calls = event_queue.enqueue_event.call_args_list
        assert len(calls) >= 2

        event_types = [type(call.args[0]) for call in calls]
        assert TaskArtifactUpdateEvent in event_types
        assert TaskStatusUpdateEvent in event_types

    async def test_execute_enqueues_failed_status_on_error(
        self, temp_scenario_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """execute() should enqueue a failed status event when a top-level error occurs."""
        from a2a.types import TaskState, TaskStatusUpdateEvent

        from green.executor import GreenAgentExecutor

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        executor = GreenAgentExecutor(temp_scenario_file)
        context = _make_context()
        event_queue = _make_event_queue()

        mock_messenger = MagicMock()
        mock_messenger.close = AsyncMock()

        # Trigger a top-level error (outside per-task loop) via generate_agentbeats_results
        with (
            patch("green.executor.PurpleAgentMessenger", return_value=mock_messenger),
            patch("green.executor.load_task", return_value=_make_mock_task()),
            patch(
                "green.executor.execute_test_against_correct",
                return_value=_make_test_execution_result(True),
            ),
            patch(
                "green.executor.execute_test_against_buggy",
                return_value=_make_test_execution_result(False),
            ),
            patch(
                "green.executor.run_mutation_testing",
                return_value=_make_mutation_result(),
            ),
            patch(
                "green.executor.generate_agentbeats_results",
                side_effect=RuntimeError("results generation failed"),
            ),
        ):
            mock_messenger.generate_tests = AsyncMock(return_value="def test_add(): pass")
            await executor.execute(context, event_queue)

        calls = event_queue.enqueue_event.call_args_list
        status_events = [
            call.args[0] for call in calls if isinstance(call.args[0], TaskStatusUpdateEvent)
        ]
        assert len(status_events) >= 1
        assert any(e.status.state == TaskState.failed for e in status_events)

    async def test_execute_generates_trace_id(
        self, temp_scenario_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """execute() should generate a UUID trace_id per evaluation."""
        from green.executor import GreenAgentExecutor

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        executor = GreenAgentExecutor(temp_scenario_file)
        context = _make_context()
        event_queue = _make_event_queue()

        mock_messenger = MagicMock()
        mock_messenger.generate_tests = AsyncMock(return_value="def test_add(): pass")
        mock_messenger.close = AsyncMock()

        captured_trace_ids: list[str] = []
        original_uuid4 = uuid.uuid4

        def mock_uuid4() -> uuid.UUID:
            result = original_uuid4()
            captured_trace_ids.append(str(result))
            return result

        with (
            patch("green.executor.PurpleAgentMessenger", return_value=mock_messenger),
            patch("green.executor.load_task", return_value=_make_mock_task()),
            patch(
                "green.executor.execute_test_against_correct",
                return_value=_make_test_execution_result(True),
            ),
            patch(
                "green.executor.execute_test_against_buggy",
                return_value=_make_test_execution_result(False),
            ),
            patch(
                "green.executor.run_mutation_testing",
                return_value=_make_mutation_result(),
            ),
            patch("green.executor.uuid.uuid4", side_effect=mock_uuid4),
        ):
            await executor.execute(context, event_queue)

        # A trace_id should have been generated
        assert len(captured_trace_ids) >= 1
        # The trace_id should be a valid UUID4
        for tid in captured_trace_ids:
            parsed = uuid.UUID(tid)
            assert parsed.version == 4

    async def test_execute_includes_latency_in_artifact(
        self, temp_scenario_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """execute() should record latency and include it in the result artifact."""
        from a2a.types import TaskArtifactUpdateEvent

        from green.executor import GreenAgentExecutor

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        executor = GreenAgentExecutor(temp_scenario_file)
        context = _make_context()
        event_queue = _make_event_queue()

        mock_messenger = MagicMock()
        mock_messenger.generate_tests = AsyncMock(return_value="def test_add(): pass")
        mock_messenger.close = AsyncMock()

        with (
            patch("green.executor.PurpleAgentMessenger", return_value=mock_messenger),
            patch("green.executor.load_task", return_value=_make_mock_task()),
            patch(
                "green.executor.execute_test_against_correct",
                return_value=_make_test_execution_result(True),
            ),
            patch(
                "green.executor.execute_test_against_buggy",
                return_value=_make_test_execution_result(False),
            ),
            patch(
                "green.executor.run_mutation_testing",
                return_value=_make_mutation_result(),
            ),
        ):
            await executor.execute(context, event_queue)

        # Find the artifact event
        calls = event_queue.enqueue_event.call_args_list
        artifact_events = [
            call.args[0] for call in calls if isinstance(call.args[0], TaskArtifactUpdateEvent)
        ]
        assert len(artifact_events) >= 1

        artifact = artifact_events[0].artifact
        # Artifact should contain data with latency field
        from a2a.types import DataPart

        for part in artifact.parts:
            if isinstance(part.root, DataPart):
                data = part.root.data
                assert "latency" in data
                assert isinstance(data["latency"], float)
                assert data["latency"] >= 0
                break
        else:
            pytest.fail("No DataPart found in artifact")

    async def test_execute_delegates_to_agent_pipeline(
        self, temp_scenario_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """execute() should call agent pipeline functions for each task."""
        from green.executor import GreenAgentExecutor

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        executor = GreenAgentExecutor(temp_scenario_file)
        context = _make_context()
        event_queue = _make_event_queue()

        mock_messenger = MagicMock()
        mock_messenger.generate_tests = AsyncMock(return_value="def test_add(): pass")
        mock_messenger.close = AsyncMock()

        with (
            patch("green.executor.PurpleAgentMessenger", return_value=mock_messenger),
            patch("green.executor.load_task", return_value=_make_mock_task()) as mock_load,
            patch(
                "green.executor.execute_test_against_correct",
                return_value=_make_test_execution_result(True),
            ) as mock_correct,
            patch(
                "green.executor.execute_test_against_buggy",
                return_value=_make_test_execution_result(False),
            ) as mock_buggy,
            patch(
                "green.executor.run_mutation_testing",
                return_value=_make_mutation_result(),
            ) as mock_mutation,
        ):
            await executor.execute(context, event_queue)

        # Should have called pipeline for each task (settings.task_count = 5)
        assert mock_load.call_count == 5
        assert mock_correct.call_count == 5
        assert mock_buggy.call_count == 5
        assert mock_mutation.call_count == 5
        assert mock_messenger.generate_tests.await_count == 5
