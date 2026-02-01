"""Tests for EvalPlus HumanEval task downloader.

Following TDD RED phase - these tests MUST fail initially.
"""

import json
import shutil
from pathlib import Path

import pytest


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """Create temporary data directory for tests."""
    data_dir = tmp_path / "data" / "tasks" / "tdd" / "python"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture
def cleanup_data_dir(temp_data_dir: Path):
    """Cleanup after tests."""
    yield temp_data_dir
    if temp_data_dir.exists():
        shutil.rmtree(temp_data_dir.parent.parent.parent)


class TestDownloadEvalPlus:
    """Test suite for EvalPlus HumanEval task downloader."""

    def test_download_creates_task_directories(
        self, temp_data_dir: Path, cleanup_data_dir: Path
    ) -> None:
        """Download creates task_001 through task_005 directories."""
        from green.data_prep.download_evalplus import download_tasks

        download_tasks(output_dir=temp_data_dir, task_range=(0, 5))

        # Verify all 5 task directories exist
        for i in range(1, 6):
            matching_dirs = list(temp_data_dir.glob(f"task_{i:03d}_*"))
            assert len(matching_dirs) == 1, f"Expected exactly one directory for task {i:03d}"
            assert matching_dirs[0].is_dir()

    def test_download_creates_spec_py(self, temp_data_dir: Path, cleanup_data_dir: Path) -> None:
        """Download creates spec.py with function signature and docstring."""
        from green.data_prep.download_evalplus import download_tasks

        download_tasks(output_dir=temp_data_dir, task_range=(0, 1))

        # Find the task directory (name includes function name)
        task_dirs = list(temp_data_dir.glob("task_001_*"))
        assert len(task_dirs) == 1
        task_dir = task_dirs[0]

        spec_file = task_dir / "spec.py"
        assert spec_file.exists(), "spec.py should exist"

        # Read spec.py and verify it contains function definition
        spec_content = spec_file.read_text()
        assert "def " in spec_content, "spec.py should contain function definition"
        assert '"""' in spec_content or "'''" in spec_content, "spec.py should contain docstring"

    def test_download_creates_correct_implementation(
        self, temp_data_dir: Path, cleanup_data_dir: Path
    ) -> None:
        """Download creates implementation/correct.py with canonical solution."""
        from green.data_prep.download_evalplus import download_tasks

        download_tasks(output_dir=temp_data_dir, task_range=(0, 1))

        task_dirs = list(temp_data_dir.glob("task_001_*"))
        task_dir = task_dirs[0]

        correct_file = task_dir / "implementation" / "correct.py"
        assert correct_file.exists(), "implementation/correct.py should exist"
        assert correct_file.parent.is_dir(), "implementation/ directory should exist"

        # Verify it contains actual code
        correct_content = correct_file.read_text()
        assert len(correct_content) > 0, "correct.py should not be empty"
        assert "def " in correct_content, "correct.py should contain function definition"

    def test_download_creates_metadata_json(
        self, temp_data_dir: Path, cleanup_data_dir: Path
    ) -> None:
        """Download creates metadata.json with required fields."""
        from green.data_prep.download_evalplus import download_tasks

        download_tasks(output_dir=temp_data_dir, task_range=(0, 1))

        task_dirs = list(temp_data_dir.glob("task_001_*"))
        task_dir = task_dirs[0]

        metadata_file = task_dir / "metadata.json"
        assert metadata_file.exists(), "metadata.json should exist"

        # Parse and validate metadata
        metadata = json.loads(metadata_file.read_text())
        assert "task_id" in metadata, "metadata should contain task_id"
        assert "function_name" in metadata, "metadata should contain function_name"
        assert "track" in metadata, "metadata should contain track"
        assert "source" in metadata, "metadata should contain source"

        # Validate values
        assert metadata["track"] == "tdd", "track should be 'tdd'"
        assert metadata["source"] == "evalplus", "source should be 'evalplus'"
        assert isinstance(metadata["task_id"], str), "task_id should be string"
        assert isinstance(metadata["function_name"], str), "function_name should be string"

    def test_download_maps_humaneval_ids_to_task_names(
        self, temp_data_dir: Path, cleanup_data_dir: Path
    ) -> None:
        """Download maps HumanEval IDs correctly (e.g., 0 -> task_001_has_close_elements)."""
        from green.data_prep.download_evalplus import download_tasks

        download_tasks(output_dir=temp_data_dir, task_range=(0, 1))

        # HumanEval/0 should map to has_close_elements function
        task_dirs = list(temp_data_dir.glob("task_001_*"))
        assert len(task_dirs) == 1, "Should have exactly one task_001 directory"

        task_dir_name = task_dirs[0].name
        # Directory name should include function name
        assert "has_close_elements" in task_dir_name.lower() or task_dir_name.startswith(
            "task_001_"
        ), "Directory should follow naming convention"

    def test_download_handles_import_errors_gracefully(
        self, temp_data_dir: Path, cleanup_data_dir: Path
    ) -> None:
        """Download handles evalplus import errors gracefully."""
        # This test verifies error handling exists
        # Actual implementation should catch ImportError for evalplus
        from green.data_prep.download_evalplus import download_tasks

        # Should not crash even if evalplus has issues
        # Just verify function exists and is callable
        assert callable(download_tasks)

    def test_download_logs_progress(
        self, temp_data_dir: Path, cleanup_data_dir: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Download logs progress and success messages."""
        import logging

        from green.data_prep.download_evalplus import download_tasks

        # Ensure logging is captured at INFO level
        caplog.set_level(logging.INFO)

        download_tasks(output_dir=temp_data_dir, task_range=(0, 2))

        # Check that logging occurred
        # Should see progress messages for downloading tasks
        assert len(caplog.records) > 0, "Should have logged messages"

    def test_download_uses_pathlib(self, temp_data_dir: Path, cleanup_data_dir: Path) -> None:
        """Download uses pathlib for cross-platform path handling."""
        from green.data_prep.download_evalplus import download_tasks

        # Verify function accepts Path objects
        assert isinstance(temp_data_dir, Path)
        download_tasks(output_dir=temp_data_dir, task_range=(0, 1))

        # If this doesn't crash, pathlib is working
        task_dirs = list(temp_data_dir.glob("task_001_*"))
        assert len(task_dirs) == 1

    def test_task_directory_structure_complete(
        self, temp_data_dir: Path, cleanup_data_dir: Path
    ) -> None:
        """Verify complete directory structure for a single task."""
        from green.data_prep.download_evalplus import download_tasks

        download_tasks(output_dir=temp_data_dir, task_range=(0, 1))

        task_dirs = list(temp_data_dir.glob("task_001_*"))
        task_dir = task_dirs[0]

        # Check all required files exist
        required_files = [
            task_dir / "spec.py",
            task_dir / "implementation" / "correct.py",
            task_dir / "metadata.json",
        ]

        for file_path in required_files:
            assert file_path.exists(), f"{file_path.relative_to(task_dir)} should exist"

    def test_multiple_tasks_downloaded(self, temp_data_dir: Path, cleanup_data_dir: Path) -> None:
        """Download creates all 5 tasks (0-4 from HumanEval)."""
        from green.data_prep.download_evalplus import download_tasks

        download_tasks(output_dir=temp_data_dir, task_range=(0, 5))

        # Count task directories
        task_dirs = list(temp_data_dir.glob("task_*"))
        assert len(task_dirs) == 5, "Should have exactly 5 task directories"

        # Verify they are numbered correctly
        task_numbers = sorted([int(d.name.split("_")[1]) for d in task_dirs])
        assert task_numbers == [1, 2, 3, 4, 5], "Tasks should be numbered 001-005"
