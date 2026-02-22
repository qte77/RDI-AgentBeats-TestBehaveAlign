"""Tests for BDD Gherkin generation from TDD docstring examples.

Following TDD RED phase - these tests MUST fail initially.
"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def temp_tdd_task_dir(tmp_path: Path) -> Path:
    """Create temporary TDD task directory with spec.py for testing."""
    task_dir = tmp_path / "tdd" / "python" / "task_001_has_close_elements"
    impl_dir = task_dir / "implementation"
    impl_dir.mkdir(parents=True, exist_ok=True)

    # Create spec.py with docstring examples in >>> format
    spec_content = '''from typing import List


def has_close_elements(numbers: List[float], threshold: float) -> bool:
    """Check if in given list of numbers, are any two numbers closer to each other than
    given threshold.
    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
    False
    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
    True
    """
'''

    spec_file = task_dir / "spec.py"
    spec_file.write_text(spec_content)

    # Create correct.py
    correct_content = (
        spec_content
        + """    for idx, elem in enumerate(numbers):
        for idx2, elem2 in enumerate(numbers):
            if idx != idx2:
                distance = abs(elem - elem2)
                if distance < threshold:
                    return True

    return False
"""
    )

    correct_file = impl_dir / "correct.py"
    correct_file.write_text(correct_content)

    # Create metadata.json
    metadata = {
        "task_id": "task_001_has_close_elements",
        "function_name": "has_close_elements",
        "track": "tdd",
        "source": "evalplus",
    }
    metadata_file = task_dir / "metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2))

    return task_dir


class TestGenerateBDD:
    """Test suite for BDD Gherkin generation from TDD docstrings."""

    def test_parse_docstring_examples(self, temp_tdd_task_dir: Path) -> None:
        """Parse >>> format docstring examples from spec.py."""
        from green.data_prep.generate_bdd import parse_docstring_examples

        spec_file = temp_tdd_task_dir / "spec.py"
        examples = parse_docstring_examples(spec_file)

        # Should extract both examples from the docstring
        assert len(examples) >= 2, "Should parse at least 2 examples from docstring"

        # First example
        assert "has_close_elements([1.0, 2.0, 3.0], 0.5)" in examples[0]["call"]
        assert examples[0]["expected"] == "False"

        # Second example
        assert "has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)" in examples[1]["call"]
        assert examples[1]["expected"] == "True"

    def test_generate_gherkin_feature_file(self, temp_tdd_task_dir: Path) -> None:
        """Generate Gherkin spec.feature file from TDD spec."""
        from green.data_prep.generate_bdd import generate_bdd_task

        bdd_root = temp_tdd_task_dir.parent.parent / "bdd" / "python"
        generate_bdd_task(temp_tdd_task_dir, bdd_root)

        # Check that spec.feature was created
        bdd_task_dir = bdd_root / "task_001_has_close_elements"
        feature_file = bdd_task_dir / "spec.feature"

        assert feature_file.exists(), "spec.feature should be created"

    def test_gherkin_has_feature_description(self, temp_tdd_task_dir: Path) -> None:
        """Generated Gherkin has Feature description from docstring."""
        from green.data_prep.generate_bdd import generate_bdd_task

        bdd_root = temp_tdd_task_dir.parent.parent / "bdd" / "python"
        generate_bdd_task(temp_tdd_task_dir, bdd_root)

        bdd_task_dir = bdd_root / "task_001_has_close_elements"
        feature_file = bdd_task_dir / "spec.feature"
        content = feature_file.read_text()

        # Should have Feature keyword and description
        assert "Feature:" in content, "Should contain Feature keyword"
        assert "has_close_elements" in content, "Should reference function name"

    def test_gherkin_has_scenarios_from_examples(self, temp_tdd_task_dir: Path) -> None:
        """Generated Gherkin has Scenarios from docstring examples."""
        from green.data_prep.generate_bdd import generate_bdd_task

        bdd_root = temp_tdd_task_dir.parent.parent / "bdd" / "python"
        generate_bdd_task(temp_tdd_task_dir, bdd_root)

        bdd_task_dir = bdd_root / "task_001_has_close_elements"
        feature_file = bdd_task_dir / "spec.feature"
        content = feature_file.read_text()

        # Should have at least 2 scenarios (one per example)
        assert content.count("Scenario:") >= 2, "Should have at least 2 scenarios"

    def test_gherkin_has_given_when_then_steps(self, temp_tdd_task_dir: Path) -> None:
        """Generated Gherkin has Given/When/Then steps for each example."""
        from green.data_prep.generate_bdd import generate_bdd_task

        bdd_root = temp_tdd_task_dir.parent.parent / "bdd" / "python"
        generate_bdd_task(temp_tdd_task_dir, bdd_root)

        bdd_task_dir = bdd_root / "task_001_has_close_elements"
        feature_file = bdd_task_dir / "spec.feature"
        content = feature_file.read_text()

        # Should contain Given/When/Then keywords
        assert "Given" in content, "Should contain Given steps"
        assert "When" in content, "Should contain When steps"
        assert "Then" in content, "Should contain Then steps"

    def test_create_bdd_task_structure(self, temp_tdd_task_dir: Path) -> None:
        """Create BDD task structure in data/tasks/bdd/python/task_*/."""
        from green.data_prep.generate_bdd import generate_bdd_task

        bdd_root = temp_tdd_task_dir.parent.parent / "bdd" / "python"
        generate_bdd_task(temp_tdd_task_dir, bdd_root)

        # Check directory structure
        bdd_task_dir = bdd_root / "task_001_has_close_elements"
        assert bdd_task_dir.exists(), "BDD task directory should be created"
        assert bdd_task_dir.is_dir(), "Should be a directory"

    def test_symlink_implementation_directory(self, temp_tdd_task_dir: Path) -> None:
        """Symlink implementation/ directory to reuse TDD implementations."""
        from green.data_prep.generate_bdd import generate_bdd_task

        bdd_root = temp_tdd_task_dir.parent.parent / "bdd" / "python"
        generate_bdd_task(temp_tdd_task_dir, bdd_root)

        bdd_task_dir = bdd_root / "task_001_has_close_elements"
        impl_link = bdd_task_dir / "implementation"

        assert impl_link.exists(), "implementation/ should exist"
        assert impl_link.is_symlink(), "implementation/ should be a symlink"

        # Verify it points to TDD implementation
        tdd_impl = temp_tdd_task_dir / "implementation"
        assert impl_link.resolve() == tdd_impl.resolve(), "Should symlink to TDD implementation"

    def test_generate_bdd_metadata_json(self, temp_tdd_task_dir: Path) -> None:
        """Generate BDD metadata.json with track='bdd' and tdd_source reference."""
        from green.data_prep.generate_bdd import generate_bdd_task

        bdd_root = temp_tdd_task_dir.parent.parent / "bdd" / "python"
        generate_bdd_task(temp_tdd_task_dir, bdd_root)

        bdd_task_dir = bdd_root / "task_001_has_close_elements"
        metadata_file = bdd_task_dir / "metadata.json"

        assert metadata_file.exists(), "metadata.json should be created"

        metadata = json.loads(metadata_file.read_text())
        assert metadata["track"] == "bdd", "Track should be 'bdd'"
        assert "tdd_source" in metadata, "Should reference TDD source"
        assert metadata["task_id"] == "task_001_has_close_elements"
        assert metadata["function_name"] == "has_close_elements"

    def test_extract_function_name_from_spec(self, temp_tdd_task_dir: Path) -> None:
        """Extract function name from spec.py or metadata.json."""
        from green.data_prep.generate_bdd import extract_function_name

        # Should extract from spec.py using AST or regex
        function_name = extract_function_name(temp_tdd_task_dir)
        assert function_name == "has_close_elements"

    def test_generate_bdd_for_all_tasks(self, tmp_path: Path) -> None:
        """Process all TDD tasks and generate BDD equivalents."""
        from green.data_prep.generate_bdd import generate_bdd_from_tdd

        # Create minimal TDD structure with 2 tasks
        tdd_root = tmp_path / "tdd" / "python"

        for i in range(1, 3):
            task_dir = tdd_root / f"task_{i:03d}_test_func"
            task_dir.mkdir(parents=True, exist_ok=True)

            spec_content = f'''def test_func():
    """Test function {i}.
    >>> test_func()
    True
    """
'''
            (task_dir / "spec.py").write_text(spec_content)

            impl_dir = task_dir / "implementation"
            impl_dir.mkdir(exist_ok=True)
            (impl_dir / "correct.py").write_text(spec_content + "    return True\n")

            metadata = {
                "task_id": f"task_{i:03d}_test_func",
                "function_name": "test_func",
                "track": "tdd",
            }
            (task_dir / "metadata.json").write_text(json.dumps(metadata))

        # Generate BDD tasks
        bdd_root = tmp_path / "bdd" / "python"
        generate_bdd_from_tdd(tdd_root, bdd_root)

        # Should create 2 BDD task directories
        bdd_tasks = list(bdd_root.glob("task_*"))
        assert len(bdd_tasks) == 2, "Should create BDD task for each TDD task"
