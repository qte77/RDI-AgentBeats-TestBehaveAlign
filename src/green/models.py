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
