"""Tests for variant generation script (buggy.py and alternative.py).

Following TDD RED phase - these tests MUST fail initially.
"""

import shutil
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


@pytest.fixture
def cleanup_temp_dir(temp_task_dir: Path):
    """Cleanup after tests."""
    yield temp_task_dir
    if temp_task_dir.exists():
        shutil.rmtree(temp_task_dir)


class TestGenerateVariants:
    """Test suite for variant generation (buggy.py and alternative.py)."""

    def test_generate_buggy_creates_buggy_file(
        self, temp_task_dir: Path, cleanup_temp_dir: Path
    ) -> None:
        """Generate buggy.py in implementation directory."""
        from scripts.data_prep.generate_variants import generate_buggy

        generate_buggy(temp_task_dir)

        buggy_file = temp_task_dir / "implementation" / "buggy.py"
        assert buggy_file.exists(), "buggy.py should be created"

    def test_generate_buggy_reads_correct_py(
        self, temp_task_dir: Path, cleanup_temp_dir: Path
    ) -> None:
        """Generate reads correct.py from task directory."""
        from scripts.data_prep.generate_variants import generate_buggy

        # Should not crash when correct.py exists
        generate_buggy(temp_task_dir)

        buggy_file = temp_task_dir / "implementation" / "buggy.py"
        assert buggy_file.exists()

    def test_generate_buggy_injects_known_defect(
        self, temp_task_dir: Path, cleanup_temp_dir: Path
    ) -> None:
        """Generated buggy.py contains injected defect based on BUG_PATTERNS."""
        from scripts.data_prep.generate_variants import generate_buggy

        generate_buggy(temp_task_dir)

        buggy_file = temp_task_dir / "implementation" / "buggy.py"
        buggy_content = buggy_file.read_text()
        correct_content = (temp_task_dir / "implementation" / "correct.py").read_text()

        # Buggy content should differ from correct content
        assert buggy_content != correct_content, "buggy.py should differ from correct.py"

    def test_generate_buggy_uses_bug_patterns_dict(
        self, temp_task_dir: Path, cleanup_temp_dir: Path
    ) -> None:
        """BUG_PATTERNS dict maps task_id to injection rules."""
        from scripts.data_prep.generate_variants import BUG_PATTERNS

        # BUG_PATTERNS should be a dict
        assert isinstance(BUG_PATTERNS, dict), "BUG_PATTERNS should be a dictionary"

        # Should contain at least one pattern
        assert len(BUG_PATTERNS) > 0, "BUG_PATTERNS should have at least one entry"

    def test_generate_buggy_uses_string_replacement(
        self, temp_task_dir: Path, cleanup_temp_dir: Path
    ) -> None:
        """Bug injection uses string replacement (simple substitution)."""
        from scripts.data_prep.generate_variants import generate_buggy

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

    def test_generate_buggy_validates_code_differs(
        self, temp_task_dir: Path, cleanup_temp_dir: Path
    ) -> None:
        """Validation ensures buggy code differs from correct code."""
        from scripts.data_prep.generate_variants import generate_buggy

        generate_buggy(temp_task_dir)

        correct_content = (temp_task_dir / "implementation" / "correct.py").read_text()
        buggy_content = (temp_task_dir / "implementation" / "buggy.py").read_text()

        # Must be different
        assert correct_content != buggy_content, "Buggy code must differ from correct code"

    def test_generate_buggy_handles_task_id_extraction(
        self, temp_task_dir: Path, cleanup_temp_dir: Path
    ) -> None:
        """Extract task_id from directory name (e.g., task_001_has_close_elements -> task_001)."""
        from scripts.data_prep.generate_variants import generate_buggy

        # Directory name is task_001_has_close_elements
        # Should extract task_001 or use full name as key
        generate_buggy(temp_task_dir)

        buggy_file = temp_task_dir / "implementation" / "buggy.py"
        assert buggy_file.exists()

    def test_bug_patterns_structure(self) -> None:
        """BUG_PATTERNS has expected structure with old/new replacement pairs."""
        from scripts.data_prep.generate_variants import BUG_PATTERNS

        # Check structure - should be dict mapping task_id to replacement rules
        assert isinstance(BUG_PATTERNS, dict)

        # Each entry should define how to inject a bug
        # Format could be: {"task_001_has_close_elements": {"old": "...", "new": "..."}}
        if len(BUG_PATTERNS) > 0:
            first_key = list(BUG_PATTERNS.keys())[0]
            pattern = BUG_PATTERNS[first_key]
            # Pattern should specify replacement
            assert isinstance(pattern, dict), "Pattern should be a dict with replacement rules"

    def test_generate_variants_main_function(self, tmp_path: Path) -> None:
        """Main function processes all tasks in data directory."""
        from scripts.data_prep.generate_variants import generate_variants

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

    def test_generate_buggy_preserves_syntax(
        self, temp_task_dir: Path, cleanup_temp_dir: Path
    ) -> None:
        """Generated buggy.py should be syntactically valid Python."""
        import ast

        from scripts.data_prep.generate_variants import generate_buggy

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
        from scripts.data_prep.generate_variants import BUG_PATTERNS

        # Should have a pattern for the first task
        task_id = "task_001_has_close_elements"
        assert task_id in BUG_PATTERNS or any(
            "task_001" in key for key in BUG_PATTERNS.keys()
        ), f"BUG_PATTERNS should include pattern for {task_id}"
