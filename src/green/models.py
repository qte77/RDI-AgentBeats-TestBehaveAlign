"""Pydantic models for Green Agent task data.

Models for task specifications, implementations, and metadata validation.
"""

from typing import Literal

from pydantic import BaseModel, Field


class Task(BaseModel):
    """Task specification and implementation data.

    Represents a single evaluation task with spec, implementations, and metadata.
    Immutable after creation (frozen=True).
    """

    model_config = {"frozen": True}

    task_id: str = Field(..., description="Task identifier (e.g., task_001_example_function)")
    function_name: str = Field(..., description="Name of the function being tested")
    track: Literal["tdd", "bdd"] = Field(..., description="Evaluation track: tdd or bdd")
    spec: str = Field(..., description="Specification (spec.py for TDD or spec.feature for BDD)")
    correct_implementation: str = Field(..., description="Correct implementation from correct.py")
    buggy_implementation: str = Field(..., description="Buggy implementation from buggy.py")


class MutationResult(BaseModel):
    """Result of mutation testing against a correct implementation.

    Captures counts of killed and survived mutants, total mutants,
    mutation score, and optional error message.
    Immutable after creation (frozen=True).
    """

    model_config = {"frozen": True}

    killed: int = Field(0, description="Number of mutants killed by tests")
    survived: int = Field(0, description="Number of mutants that survived tests")
    total: int = Field(0, description="Total number of mutants generated")
    mutation_score: float = Field(0.0, description="Mutation score: killed / total")
    error: str | None = Field(None, description="Error message if mutation testing failed")


class CompositeScore(BaseModel):
    """Weighted composite score combining mutation and fault detection metrics.

    Formula: score = (0.60 * mutation_score) + (0.40 * fault_detection_rate)
    Immutable after creation (frozen=True).
    """

    model_config = {"frozen": True}

    mutation_score: float = Field(0.0, ge=0.0, le=1.0, description="Mutation score in [0.0, 1.0]")
    fault_detection_rate: float = Field(
        0.0, ge=0.0, le=1.0, description="Fault detection rate in [0.0, 1.0]"
    )
    score: float = Field(0.0, ge=0.0, le=1.0, description="Weighted composite score in [0.0, 1.0]")


# FIXME: class name triggers PytestCollectionWarning (Test* pattern) — rename or add collect_ignore
class TestExecutionResult(BaseModel):
    """Result of test execution against an implementation.

    Captures exit code, output streams, execution time, and pass/fail status.
    Immutable after creation (frozen=True).
    """

    model_config = {"frozen": True}

    exit_code: int = Field(..., description="Test execution exit code (0 = success)")
    stdout: str = Field(..., description="Standard output from test execution")
    stderr: str = Field(..., description="Standard error from test execution")
    execution_time: float = Field(..., description="Execution time in seconds")
    passed: bool = Field(..., description="True if tests passed (exit code 0), False otherwise")
    failure_type: Literal["none", "assertion", "infrastructure", "timeout"] = Field(
        "none",
        description="Failure type: assertion, infrastructure, timeout, or none",
    )
