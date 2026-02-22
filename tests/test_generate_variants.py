"""Tests for variant generation script (buggy.py and alternative.py).

Following TDD RED phase - these tests MUST fail initially.
"""

from pathlib import Path

import pytest


@pytest.fixture
def temp_task_dir(tmp_path: Path) -> Path:
    """Create temporary task directory with correct.py for testing."""
    task_dir = tmp_path / "task_001_has_close_elements"
    impl_dir = task_dir / "implementation"
    impl_dir.mkdir(parents=True, exist_ok=True)

    # Create a sample correct.py
    correct_content = '''from typing import List


def has_close_elements(numbers: List[float], threshold: float) -> bool:
    """Check if in given list of numbers, are any two numbers closer to each other than
    given threshold.
    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
    False
    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
    True
    """
    for idx, elem in enumerate(numbers):
        for idx2, elem2 in enumerate(numbers):
            if idx != idx2:
                distance = abs(elem - elem2)
                if distance < threshold:
                    return True

    return False
'''

    correct_file = impl_dir / "correct.py"
    correct_file.write_text(correct_content)

    return task_dir


class TestGenerateVariants:
    """Test suite for variant generation (buggy.py and alternative.py)."""

    def test_generate_buggy_creates_buggy_file(self, temp_task_dir: Path) -> None:
        """Generate buggy.py in implementation directory."""
        from green.data_prep.generate_variants import generate_buggy

        generate_buggy(temp_task_dir)

        buggy_file = temp_task_dir / "implementation" / "buggy.py"
        assert buggy_file.exists(), "buggy.py should be created"

    def test_generate_buggy_injects_known_defect(self, temp_task_dir: Path) -> None:
        """Generated buggy.py contains injected defect based on BUG_PATTERNS."""
        from green.data_prep.generate_variants import generate_buggy

        generate_buggy(temp_task_dir)

        buggy_file = temp_task_dir / "implementation" / "buggy.py"
        buggy_content = buggy_file.read_text()
        correct_content = (temp_task_dir / "implementation" / "correct.py").read_text()

        # Buggy content should differ from correct content
        assert buggy_content != correct_content, "buggy.py should differ from correct.py"

    def test_generate_buggy_uses_string_replacement(self, temp_task_dir: Path) -> None:
        """Bug injection uses string replacement (simple substitution)."""
        from green.data_prep.generate_variants import generate_buggy

        # Create a known correct.py with specific content
        correct_file = temp_task_dir / "implementation" / "correct.py"
        correct_content = correct_file.read_text()

        generate_buggy(temp_task_dir)

        buggy_file = temp_task_dir / "implementation" / "buggy.py"
        buggy_content = buggy_file.read_text()

        # Verify that buggy content is different (string replacement occurred)
        assert buggy_content != correct_content
        # Verify structure is preserved (imports, function definition)
        assert "def has_close_elements" in buggy_content
        assert "from typing import List" in buggy_content

    def test_generate_buggy_validates_code_differs(self, temp_task_dir: Path) -> None:
        """Validation ensures buggy code differs from correct code."""
        from green.data_prep.generate_variants import generate_buggy

        generate_buggy(temp_task_dir)

        correct_content = (temp_task_dir / "implementation" / "correct.py").read_text()
        buggy_content = (temp_task_dir / "implementation" / "buggy.py").read_text()

        # Must be different
        assert correct_content != buggy_content, "Buggy code must differ from correct code"

    def test_generate_variants_main_function(self, tmp_path: Path) -> None:
        """Main function processes all tasks in data directory."""
        from green.data_prep.generate_variants import generate_variants

        # Create a minimal task structure
        data_dir = tmp_path / "data" / "tasks" / "tdd" / "python"
        task_dir = data_dir / "task_001_test"
        impl_dir = task_dir / "implementation"
        impl_dir.mkdir(parents=True, exist_ok=True)

        # Create correct.py
        correct_file = impl_dir / "correct.py"
        correct_file.write_text("def test():\n    return 42\n")

        # Run generate_variants on the data directory
        generate_variants(data_dir)

        # Should create buggy.py
        buggy_file = impl_dir / "buggy.py"
        assert buggy_file.exists()

    def test_generate_buggy_preserves_syntax(self, temp_task_dir: Path) -> None:
        """Generated buggy.py should be syntactically valid Python."""
        import ast

        from green.data_prep.generate_variants import generate_buggy

        generate_buggy(temp_task_dir)

        buggy_file = temp_task_dir / "implementation" / "buggy.py"
        buggy_content = buggy_file.read_text()

        # Should be valid Python syntax
        try:
            ast.parse(buggy_content)
        except SyntaxError:
            pytest.fail("buggy.py should be syntactically valid Python")

    def test_bug_patterns_covers_task_001(self) -> None:
        """BUG_PATTERNS includes pattern for task_001_has_close_elements."""
        from green.data_prep.generate_variants import BUG_PATTERNS

        # Should have a pattern for the first task
        task_id = "task_001_has_close_elements"
        assert task_id in BUG_PATTERNS or any("task_001" in key for key in BUG_PATTERNS.keys()), (
            f"BUG_PATTERNS should include pattern for {task_id}"
        )

    @pytest.mark.parametrize(
        "task_id",
        [
            "task_001_has_close_elements",
            "task_002_separate_paren_groups",
            "task_003_truncate_number",
            "task_004_below_zero",
            "task_005_intersperse",
        ],
    )
    def test_bug_patterns_covers_all_tasks(self, task_id: str) -> None:
        """BUG_PATTERNS includes valid patterns for all 5 tasks (001-005)."""
        from green.data_prep.generate_variants import BUG_PATTERNS

        assert task_id in BUG_PATTERNS, f"BUG_PATTERNS should include pattern for {task_id}"
        assert "old" in BUG_PATTERNS[task_id], f"Pattern for {task_id} should have 'old' key"
        assert "new" in BUG_PATTERNS[task_id], f"Pattern for {task_id} should have 'new' key"

    def test_generate_buggy_raises_value_error_when_pattern_not_found(
        self, tmp_path: Path
    ) -> None:
        """generate_buggy raises ValueError when bug pattern is absent from correct.py."""
        from green.data_prep.generate_variants import generate_buggy

        # Task name matches BUG_PATTERNS key but correct.py lacks the expected old pattern
        task_dir = tmp_path / "task_001_has_close_elements"
        impl_dir = task_dir / "implementation"
        impl_dir.mkdir(parents=True, exist_ok=True)

        # Write correct.py WITHOUT "if idx != idx2:" so replacement is a no-op
        correct_content = "def has_close_elements(numbers, threshold):\n    return False\n"
        (impl_dir / "correct.py").write_text(correct_content)

        with pytest.raises(ValueError, match="Bug injection failed"):
            generate_buggy(task_dir)
