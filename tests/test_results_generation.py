"""Tests for AgentBeats results.json generation (STORY-013).

Following TDD RED phase - these tests MUST fail initially.
Tests cover generating output/results.json in AgentBeats format.

Schema:
{
  "participants": {"agent": "purple-agent-uuid"},
  "results": [{
    "score": 0.75,
    "pass_rate": 0.65,
    "task_rewards": {
      "mutation_score": 0.55,
      "fault_detection_rate": 0.80,
      "track": "tdd",
      "task_count": 5
    },
    "detail": {
      "task_details": [...]
    }
  }]
}
"""

import json
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError


class TestTaskDetailModel:
    """Test suite for TaskDetail Pydantic model."""

    def test_task_detail_model_creation(self) -> None:
        """TaskDetail model can be created with required fields."""
        from green.models import TaskDetail

        detail = TaskDetail(
            task_id="task_001_example",
            mutation_score=0.8,
            fault_detection_rate=0.6,
            composite_score=0.72,
            passed_correct=True,
            failed_buggy=True,
        )

        assert detail.task_id == "task_001_example"
        assert detail.mutation_score == 0.8
        assert detail.fault_detection_rate == 0.6
        assert detail.composite_score == 0.72
        assert detail.passed_correct is True
        assert detail.failed_buggy is True

    def test_task_detail_is_frozen(self) -> None:
        """TaskDetail model is immutable after creation."""
        from green.models import TaskDetail

        detail = TaskDetail(
            task_id="task_001",
            mutation_score=0.5,
            fault_detection_rate=0.5,
            composite_score=0.5,
            passed_correct=True,
            failed_buggy=True,
        )

        with pytest.raises(Exception):
            detail.mutation_score = 0.9  # type: ignore[misc]

    def test_task_detail_score_out_of_range_raises(self) -> None:
        """TaskDetail rejects scores outside [0.0, 1.0]."""
        from green.models import TaskDetail

        with pytest.raises(ValidationError):
            TaskDetail(
                task_id="task_001",
                mutation_score=1.5,
                fault_detection_rate=0.5,
                composite_score=0.5,
                passed_correct=True,
                failed_buggy=True,
            )


class TestTaskRewardsModel:
    """Test suite for TaskRewards Pydantic model."""

    def test_task_rewards_model_creation(self) -> None:
        """TaskRewards model can be created with required fields."""
        from green.models import TaskRewards

        rewards = TaskRewards(
            mutation_score=0.55,
            fault_detection_rate=0.80,
            track="tdd",
            task_count=5,
        )

        assert rewards.mutation_score == 0.55
        assert rewards.fault_detection_rate == 0.80
        assert rewards.track == "tdd"
        assert rewards.task_count == 5

    def test_task_rewards_bdd_track_accepted(self) -> None:
        """TaskRewards accepts 'bdd' as track value."""
        from green.models import TaskRewards

        rewards = TaskRewards(
            mutation_score=0.5,
            fault_detection_rate=0.5,
            track="bdd",
            task_count=3,
        )

        assert rewards.track == "bdd"

    def test_task_rewards_invalid_track_raises(self) -> None:
        """TaskRewards rejects invalid track values."""
        from green.models import TaskRewards

        with pytest.raises(ValidationError):
            TaskRewards(
                mutation_score=0.5,
                fault_detection_rate=0.5,
                track="invalid",  # type: ignore[arg-type]
                task_count=3,
            )

    def test_task_rewards_is_frozen(self) -> None:
        """TaskRewards model is immutable after creation."""
        from green.models import TaskRewards

        rewards = TaskRewards(
            mutation_score=0.5,
            fault_detection_rate=0.5,
            track="tdd",
            task_count=5,
        )

        with pytest.raises(Exception):
            rewards.task_count = 10  # type: ignore[misc]


class TestResultDetailModel:
    """Test suite for ResultDetail Pydantic model."""

    def test_result_detail_model_creation(self) -> None:
        """ResultDetail model can be created with task_details list."""
        from green.models import ResultDetail, TaskDetail

        task_detail = TaskDetail(
            task_id="task_001",
            mutation_score=0.8,
            fault_detection_rate=0.6,
            composite_score=0.72,
            passed_correct=True,
            failed_buggy=True,
        )
        detail = ResultDetail(task_details=[task_detail])

        assert len(detail.task_details) == 1
        assert detail.task_details[0].task_id == "task_001"

    def test_result_detail_empty_list_accepted(self) -> None:
        """ResultDetail accepts empty task_details list."""
        from green.models import ResultDetail

        detail = ResultDetail(task_details=[])

        assert detail.task_details == []


class TestEvalResultModel:
    """Test suite for EvalResult Pydantic model."""

    def test_eval_result_model_creation(self) -> None:
        """EvalResult model can be created with required fields."""
        from green.models import EvalResult, ResultDetail, TaskRewards

        rewards = TaskRewards(
            mutation_score=0.55,
            fault_detection_rate=0.80,
            track="tdd",
            task_count=5,
        )
        detail = ResultDetail(task_details=[])
        result = EvalResult(
            score=0.75,
            pass_rate=0.65,
            task_rewards=rewards,
            detail=detail,
        )

        assert result.score == 0.75
        assert result.pass_rate == 0.65
        assert result.task_rewards.track == "tdd"

    def test_eval_result_score_out_of_range_raises(self) -> None:
        """EvalResult rejects score outside [0.0, 1.0]."""
        from green.models import EvalResult, ResultDetail, TaskRewards

        rewards = TaskRewards(
            mutation_score=0.5, fault_detection_rate=0.5, track="tdd", task_count=5
        )
        detail = ResultDetail(task_details=[])

        with pytest.raises(ValidationError):
            EvalResult(score=1.5, pass_rate=0.5, task_rewards=rewards, detail=detail)

    def test_eval_result_is_frozen(self) -> None:
        """EvalResult model is immutable after creation."""
        from green.models import EvalResult, ResultDetail, TaskRewards

        rewards = TaskRewards(
            mutation_score=0.5, fault_detection_rate=0.5, track="tdd", task_count=5
        )
        detail = ResultDetail(task_details=[])
        result = EvalResult(score=0.5, pass_rate=0.5, task_rewards=rewards, detail=detail)

        with pytest.raises(Exception):
            result.score = 0.9  # type: ignore[misc]


class TestAgentBeatsOutputModel:
    """Test suite for AgentBeatsOutput Pydantic model."""

    def test_agentbeats_output_model_creation(self) -> None:
        """AgentBeatsOutput model can be created with participants and results."""
        from green.models import AgentBeatsOutput, EvalResult, ResultDetail, TaskRewards

        rewards = TaskRewards(
            mutation_score=0.55,
            fault_detection_rate=0.80,
            track="tdd",
            task_count=5,
        )
        detail = ResultDetail(task_details=[])
        result = EvalResult(score=0.75, pass_rate=0.65, task_rewards=rewards, detail=detail)
        output = AgentBeatsOutput(
            participants={"agent": "019b4d08-d84c-7a00-b2ec-4905ef7afc96"},
            results=[result],
        )

        assert output.participants["agent"] == "019b4d08-d84c-7a00-b2ec-4905ef7afc96"
        assert len(output.results) == 1
        assert output.results[0].score == 0.75

    def test_agentbeats_output_serializes_to_valid_json(self) -> None:
        """AgentBeatsOutput serializes to valid JSON via model_dump_json()."""
        from green.models import AgentBeatsOutput, EvalResult, ResultDetail, TaskRewards

        rewards = TaskRewards(
            mutation_score=0.55,
            fault_detection_rate=0.80,
            track="tdd",
            task_count=5,
        )
        detail = ResultDetail(task_details=[])
        result = EvalResult(score=0.75, pass_rate=0.65, task_rewards=rewards, detail=detail)
        output = AgentBeatsOutput(
            participants={"agent": "test-uuid"},
            results=[result],
        )

        json_str = output.model_dump_json()
        parsed = json.loads(json_str)

        assert "participants" in parsed
        assert "results" in parsed
        assert parsed["participants"]["agent"] == "test-uuid"
        assert parsed["results"][0]["score"] == 0.75
        assert parsed["results"][0]["pass_rate"] == 0.65
        assert parsed["results"][0]["task_rewards"]["track"] == "tdd"
        assert "detail" in parsed["results"][0]

    def test_agentbeats_output_json_schema_structure(self) -> None:
        """AgentBeatsOutput JSON matches expected AgentBeats schema structure."""
        from green.models import AgentBeatsOutput, EvalResult, ResultDetail, TaskRewards

        rewards = TaskRewards(
            mutation_score=0.55,
            fault_detection_rate=0.80,
            track="tdd",
            task_count=5,
        )
        detail = ResultDetail(task_details=[])
        result = EvalResult(score=0.75, pass_rate=0.65, task_rewards=rewards, detail=detail)
        output = AgentBeatsOutput(
            participants={"agent": "purple-agent-uuid"},
            results=[result],
        )

        data = json.loads(output.model_dump_json())
        task_rewards = data["results"][0]["task_rewards"]

        assert "mutation_score" in task_rewards
        assert "fault_detection_rate" in task_rewards
        assert "track" in task_rewards
        assert "task_count" in task_rewards
        assert "task_details" in data["results"][0]["detail"]


class TestGenerateAgentBeatsResults:
    """Test suite for generate_agentbeats_results function."""

    def test_generate_results_returns_agentbeats_output(self) -> None:
        """generate_agentbeats_results returns an AgentBeatsOutput instance."""
        from green.agent import generate_agentbeats_results
        from green.models import AgentBeatsOutput, CompositeScore, TaskDetail

        task_details = [
            TaskDetail(
                task_id="task_001",
                mutation_score=0.8,
                fault_detection_rate=0.6,
                composite_score=0.72,
                passed_correct=True,
                failed_buggy=True,
            )
        ]
        composite = CompositeScore(mutation_score=0.8, fault_detection_rate=0.6, score=0.72)

        result = generate_agentbeats_results(
            participant_id="test-uuid",
            task_details=task_details,
            composite=composite,
            pass_rate=0.65,
            track="tdd",
        )

        assert isinstance(result, AgentBeatsOutput)

    def test_generate_results_sets_participant_id(self) -> None:
        """generate_agentbeats_results sets participant ID correctly."""
        from green.agent import generate_agentbeats_results
        from green.models import CompositeScore, TaskDetail

        task_details = [
            TaskDetail(
                task_id="task_001",
                mutation_score=0.8,
                fault_detection_rate=0.6,
                composite_score=0.72,
                passed_correct=True,
                failed_buggy=True,
            )
        ]
        composite = CompositeScore(mutation_score=0.8, fault_detection_rate=0.6, score=0.72)

        result = generate_agentbeats_results(
            participant_id="purple-agent-uuid-001",
            task_details=task_details,
            composite=composite,
            pass_rate=0.65,
            track="tdd",
        )

        assert result.participants["agent"] == "purple-agent-uuid-001"

    def test_generate_results_populates_task_rewards(self) -> None:
        """generate_agentbeats_results populates task_rewards from composite score."""
        from green.agent import generate_agentbeats_results
        from green.models import CompositeScore, TaskDetail

        task_details = [
            TaskDetail(
                task_id="task_001",
                mutation_score=0.8,
                fault_detection_rate=0.6,
                composite_score=0.72,
                passed_correct=True,
                failed_buggy=True,
            ),
            TaskDetail(
                task_id="task_002",
                mutation_score=0.6,
                fault_detection_rate=0.5,
                composite_score=0.56,
                passed_correct=True,
                failed_buggy=False,
            ),
        ]
        composite = CompositeScore(mutation_score=0.7, fault_detection_rate=0.55, score=0.64)

        result = generate_agentbeats_results(
            participant_id="test-uuid",
            task_details=task_details,
            composite=composite,
            pass_rate=0.5,
            track="tdd",
        )

        rewards = result.results[0].task_rewards
        assert rewards.mutation_score == 0.7
        assert rewards.fault_detection_rate == 0.55
        assert rewards.track == "tdd"
        assert rewards.task_count == 2

    def test_generate_results_includes_task_details(self) -> None:
        """generate_agentbeats_results includes task-level details in output."""
        from green.agent import generate_agentbeats_results
        from green.models import CompositeScore, TaskDetail

        task_details = [
            TaskDetail(
                task_id="task_001",
                mutation_score=0.8,
                fault_detection_rate=0.6,
                composite_score=0.72,
                passed_correct=True,
                failed_buggy=True,
            )
        ]
        composite = CompositeScore(mutation_score=0.8, fault_detection_rate=0.6, score=0.72)

        result = generate_agentbeats_results(
            participant_id="test-uuid",
            task_details=task_details,
            composite=composite,
            pass_rate=1.0,
            track="tdd",
        )

        assert len(result.results[0].detail.task_details) == 1
        assert result.results[0].detail.task_details[0].task_id == "task_001"

    def test_generate_results_sets_composite_score(self) -> None:
        """generate_agentbeats_results sets score from composite."""
        from green.agent import generate_agentbeats_results
        from green.models import CompositeScore, TaskDetail

        task_details = [
            TaskDetail(
                task_id="task_001",
                mutation_score=0.8,
                fault_detection_rate=0.6,
                composite_score=0.72,
                passed_correct=True,
                failed_buggy=True,
            )
        ]
        composite = CompositeScore(mutation_score=0.8, fault_detection_rate=0.6, score=0.72)

        result = generate_agentbeats_results(
            participant_id="test-uuid",
            task_details=task_details,
            composite=composite,
            pass_rate=0.65,
            track="tdd",
        )

        assert result.results[0].score == 0.72
        assert result.results[0].pass_rate == 0.65


class TestWriteResultsJson:
    """Test suite for write_results_json function."""

    def test_write_results_json_creates_file(self) -> None:
        """write_results_json creates results.json in the output directory."""
        from green.agent import generate_agentbeats_results, write_results_json
        from green.models import CompositeScore, TaskDetail

        task_details = [
            TaskDetail(
                task_id="task_001",
                mutation_score=0.8,
                fault_detection_rate=0.6,
                composite_score=0.72,
                passed_correct=True,
                failed_buggy=True,
            )
        ]
        composite = CompositeScore(mutation_score=0.8, fault_detection_rate=0.6, score=0.72)
        output = generate_agentbeats_results(
            participant_id="test-uuid",
            task_details=task_details,
            composite=composite,
            pass_rate=1.0,
            track="tdd",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            result_path = write_results_json(output, output_dir)

            assert result_path.exists()
            assert result_path.name == "results.json"

    def test_write_results_json_creates_output_dir_if_missing(self) -> None:
        """write_results_json creates output directory if it does not exist."""
        from green.agent import generate_agentbeats_results, write_results_json
        from green.models import CompositeScore, TaskDetail

        task_details = [
            TaskDetail(
                task_id="task_001",
                mutation_score=0.8,
                fault_detection_rate=0.6,
                composite_score=0.72,
                passed_correct=True,
                failed_buggy=True,
            )
        ]
        composite = CompositeScore(mutation_score=0.8, fault_detection_rate=0.6, score=0.72)
        output = generate_agentbeats_results(
            participant_id="test-uuid",
            task_details=task_details,
            composite=composite,
            pass_rate=1.0,
            track="tdd",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir) / "nonexistent" / "output"
            result_path = write_results_json(output, output_dir)

            assert result_path.exists()
            assert output_dir.exists()

    def test_write_results_json_writes_valid_json(self) -> None:
        """write_results_json writes valid JSON content."""
        from green.agent import generate_agentbeats_results, write_results_json
        from green.models import CompositeScore, TaskDetail

        task_details = [
            TaskDetail(
                task_id="task_001",
                mutation_score=0.8,
                fault_detection_rate=0.6,
                composite_score=0.72,
                passed_correct=True,
                failed_buggy=True,
            )
        ]
        composite = CompositeScore(mutation_score=0.8, fault_detection_rate=0.6, score=0.72)
        output = generate_agentbeats_results(
            participant_id="test-uuid",
            task_details=task_details,
            composite=composite,
            pass_rate=1.0,
            track="tdd",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            result_path = write_results_json(output, output_dir)

            content = result_path.read_text()
            parsed = json.loads(content)

            assert "participants" in parsed
            assert "results" in parsed
            assert parsed["participants"]["agent"] == "test-uuid"

    def test_write_results_json_returns_path(self) -> None:
        """write_results_json returns the path to the written file."""
        from green.agent import generate_agentbeats_results, write_results_json
        from green.models import CompositeScore, TaskDetail

        task_details = [
            TaskDetail(
                task_id="task_001",
                mutation_score=0.8,
                fault_detection_rate=0.6,
                composite_score=0.72,
                passed_correct=True,
                failed_buggy=True,
            )
        ]
        composite = CompositeScore(mutation_score=0.8, fault_detection_rate=0.6, score=0.72)
        output = generate_agentbeats_results(
            participant_id="test-uuid",
            task_details=task_details,
            composite=composite,
            pass_rate=1.0,
            track="tdd",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            result_path = write_results_json(output, output_dir)

            assert isinstance(result_path, Path)
            assert result_path == output_dir / "results.json"
