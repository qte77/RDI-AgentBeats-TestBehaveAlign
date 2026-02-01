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
