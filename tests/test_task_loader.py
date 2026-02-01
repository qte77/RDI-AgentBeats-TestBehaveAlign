"""Tests for task directory loading and spec parsing (STORY-005).

Following TDD RED phase - these tests MUST fail initially.
Tests cover loading task directories, parsing spec files (TDD/BDD),
loading implementations, and validating task metadata.
"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def temp_tdd_task(tmp_path: Path) -> Path:
    """Create a temporary TDD task directory structure."""
    task_dir = tmp_path / "data" / "tasks" / "tdd" / "python" / "task_001_example_function"
    task_dir.mkdir(parents=True, exist_ok=True)

    # Create spec.py with function signature and docstring
    spec_py = task_dir / "spec.py"
    spec_py.write_text('''def example_function(x: int) -> int:
    """Example function for testing.

    >>> example_function(5)
    10
    >>> example_function(0)
    0
    """
''')

    # Create metadata.json
    metadata_json = task_dir / "metadata.json"
    metadata_json.write_text(json.dumps({
        "task_id": "task_001_example_function",
        "function_name": "example_function",
        "track": "tdd",
        "source": "test"
    }))

    # Create implementation directory with correct.py and buggy.py
    impl_dir = task_dir / "implementation"
    impl_dir.mkdir(parents=True, exist_ok=True)

    correct_py = impl_dir / "correct.py"
    correct_py.write_text('''def example_function(x: int) -> int:
    """Example function for testing.

    >>> example_function(5)
    10
    >>> example_function(0)
    0
    """
    return x * 2
''')

    buggy_py = impl_dir / "buggy.py"
    buggy_py.write_text('''def example_function(x: int) -> int:
    """Example function for testing.

    >>> example_function(5)
    10
    >>> example_function(0)
    0
    """
    return x + 2  # Bug: should be x * 2
''')

    return task_dir


@pytest.fixture
def temp_bdd_task(tmp_path: Path) -> Path:
    """Create a temporary BDD task directory structure."""
    task_dir = tmp_path / "data" / "tasks" / "bdd" / "python" / "task_001_example_function"
    task_dir.mkdir(parents=True, exist_ok=True)

    # Create spec.feature with Gherkin scenarios
    spec_feature = task_dir / "spec.feature"
    spec_feature.write_text('''Feature: Example function
  Test the example_function behavior

  Scenario: Multiply by two
    Given a number 5
    When we call example_function
    Then the result should be 10

  Scenario: Zero input
    Given a number 0
    When we call example_function
    Then the result should be 0
''')

    # Create metadata.json
    metadata_json = task_dir / "metadata.json"
    metadata_json.write_text(json.dumps({
        "task_id": "task_001_example_function",
        "function_name": "example_function",
        "track": "bdd",
        "source": "test"
    }))

    # Create implementation directory with symlinks (BDD reuses TDD implementations)
    impl_dir = task_dir / "implementation"
    impl_dir.mkdir(parents=True, exist_ok=True)

    correct_py = impl_dir / "correct.py"
    correct_py.write_text('''def example_function(x: int) -> int:
    """Example function for testing."""
    return x * 2
''')

    buggy_py = impl_dir / "buggy.py"
    buggy_py.write_text('''def example_function(x: int) -> int:
    """Example function for testing."""
    return x + 2  # Bug: should be x * 2
''')

    return task_dir


class TestTaskDirectoryLoading:
    """Test suite for reading task directory structure."""

    def test_read_tdd_task_directory(self, temp_tdd_task: Path) -> None:
        """Read task directory structure (TDD track)."""
        from green.agent import load_task

        task = load_task(temp_tdd_task, track="tdd")

        assert task is not None
        assert task.task_id == "task_001_example_function"
        assert task.track == "tdd"

    def test_read_bdd_task_directory(self, temp_bdd_task: Path) -> None:
        """Read task directory structure (BDD track)."""
        from green.agent import load_task

        task = load_task(temp_bdd_task, track="bdd")

        assert task is not None
        assert task.task_id == "task_001_example_function"
        assert task.track == "bdd"

    def test_task_directory_path_structure(self, temp_tdd_task: Path) -> None:
        """Path: data/tasks/{track}/python/{task_id}/."""
        from green.agent import load_task

        task = load_task(temp_tdd_task, track="tdd")

        # Verify path structure matches expected pattern
        assert "data/tasks/tdd/python" in str(temp_tdd_task)
        assert task.task_id in str(temp_tdd_task)


class TestSpecParsing:
    """Test suite for parsing spec.py (TDD) and spec.feature (BDD)."""

    def test_parse_spec_py_tdd(self, temp_tdd_task: Path) -> None:
        """Parse spec.py (TDD) containing function signature and docstring."""
        from green.agent import load_task

        task = load_task(temp_tdd_task, track="tdd")

        assert task.spec is not None
        assert "def example_function" in task.spec
        assert "Example function for testing" in task.spec
        # Should use Python AST for extraction
        assert ">>>" in task.spec  # Docstring examples preserved

    def test_parse_spec_feature_bdd(self, temp_bdd_task: Path) -> None:
        """Parse spec.feature (BDD) containing Gherkin scenarios."""
        from green.agent import load_task

        task = load_task(temp_bdd_task, track="bdd")

        assert task.spec is not None
        assert "Feature: Example function" in task.spec
        assert "Scenario:" in task.spec
        assert "Given" in task.spec and "When" in task.spec and "Then" in task.spec


class TestImplementationLoading:
    """Test suite for loading correct.py and buggy.py from implementation/ directory."""

    def test_load_correct_implementation(self, temp_tdd_task: Path) -> None:
        """Load correct.py from implementation/ directory."""
        from green.agent import load_task

        task = load_task(temp_tdd_task, track="tdd")

        assert task.correct_implementation is not None
        assert "return x * 2" in task.correct_implementation
        assert "def example_function" in task.correct_implementation

    def test_load_buggy_implementation(self, temp_tdd_task: Path) -> None:
        """Load buggy.py from implementation/ directory."""
        from green.agent import load_task

        task = load_task(temp_tdd_task, track="tdd")

        assert task.buggy_implementation is not None
        assert "return x + 2" in task.buggy_implementation
        assert "Bug:" in task.buggy_implementation  # Bug comment present


class TestTaskMetadataValidation:
    """Test suite for validating task metadata with Pydantic models."""

    def test_validate_task_metadata(self, temp_tdd_task: Path) -> None:
        """Validate task metadata (task_id, track, function_name)."""
        from green.agent import load_task

        task = load_task(temp_tdd_task, track="tdd")

        # Use Pydantic models for validation
        assert task.task_id == "task_001_example_function"
        assert task.function_name == "example_function"
        assert task.track == "tdd"

    def test_validate_tdd_track(self, temp_tdd_task: Path) -> None:
        """Track determined by scenario.toml config - TDD."""
        from green.agent import load_task

        task = load_task(temp_tdd_task, track="tdd")

        assert task.track == "tdd"

    def test_validate_bdd_track(self, temp_bdd_task: Path) -> None:
        """Track determined by scenario.toml config - BDD."""
        from green.agent import load_task

        task = load_task(temp_bdd_task, track="bdd")

        assert task.track == "bdd"


class TestErrorHandling:
    """Test suite for handling missing files gracefully with clear errors."""

    def test_missing_spec_py(self, tmp_path: Path) -> None:
        """Handle missing spec.py file gracefully with clear error."""
        from green.agent import TaskLoadError, load_task

        task_dir = tmp_path / "task_001_missing_spec"
        task_dir.mkdir(parents=True, exist_ok=True)

        # Create metadata but no spec.py
        metadata_json = task_dir / "metadata.json"
        metadata_json.write_text(json.dumps({
            "task_id": "task_001_missing_spec",
            "function_name": "example",
            "track": "tdd"
        }))

        with pytest.raises(TaskLoadError, match="spec.py"):
            load_task(task_dir, track="tdd")

    def test_missing_metadata_json(self, tmp_path: Path) -> None:
        """Handle missing metadata.json file gracefully with clear error."""
        from green.agent import TaskLoadError, load_task

        task_dir = tmp_path / "task_001_missing_metadata"
        task_dir.mkdir(parents=True, exist_ok=True)

        # Create spec.py but no metadata.json
        spec_py = task_dir / "spec.py"
        spec_py.write_text('def example(): pass')

        with pytest.raises(TaskLoadError, match="metadata.json"):
            load_task(task_dir, track="tdd")

    def test_missing_correct_implementation(self, tmp_path: Path) -> None:
        """Handle missing correct.py file gracefully with clear error."""
        from green.agent import TaskLoadError, load_task

        task_dir = tmp_path / "task_001_missing_correct"
        task_dir.mkdir(parents=True, exist_ok=True)

        # Create spec.py and metadata but no implementations
        spec_py = task_dir / "spec.py"
        spec_py.write_text('def example(): pass')

        metadata_json = task_dir / "metadata.json"
        metadata_json.write_text(json.dumps({
            "task_id": "task_001_missing_correct",
            "function_name": "example",
            "track": "tdd"
        }))

        impl_dir = task_dir / "implementation"
        impl_dir.mkdir(parents=True, exist_ok=True)

        with pytest.raises(TaskLoadError, match="correct.py"):
            load_task(task_dir, track="tdd")

    def test_missing_buggy_implementation(self, tmp_path: Path) -> None:
        """Handle missing buggy.py file gracefully with clear error."""
        from green.agent import TaskLoadError, load_task

        task_dir = tmp_path / "task_001_missing_buggy"
        task_dir.mkdir(parents=True, exist_ok=True)

        # Create spec.py, metadata, and correct.py but no buggy.py
        spec_py = task_dir / "spec.py"
        spec_py.write_text('def example(): pass')

        metadata_json = task_dir / "metadata.json"
        metadata_json.write_text(json.dumps({
            "task_id": "task_001_missing_buggy",
            "function_name": "example",
            "track": "tdd"
        }))

        impl_dir = task_dir / "implementation"
        impl_dir.mkdir(parents=True, exist_ok=True)

        correct_py = impl_dir / "correct.py"
        correct_py.write_text('def example(): return 42')

        with pytest.raises(TaskLoadError, match="buggy.py"):
            load_task(task_dir, track="tdd")


class TestCrossPlatformPaths:
    """Test suite for cross-platform path handling using pathlib."""

    def test_use_pathlib_for_paths(self, temp_tdd_task: Path) -> None:
        """Use pathlib for cross-platform path handling."""
        from green.agent import load_task

        # Path handling should work on all platforms
        task = load_task(temp_tdd_task, track="tdd")

        # Verify that pathlib Paths are being used internally
        assert isinstance(temp_tdd_task, Path)
        assert task is not None
