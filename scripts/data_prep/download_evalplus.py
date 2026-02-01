"""Download EvalPlus HumanEval tasks for test generation evaluation.

This script downloads HumanEval tasks from the EvalPlus benchmark and structures them
for use in the Green Agent evaluation workflow.
"""

import json
import logging
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def download_tasks(output_dir: Path, task_range: tuple[int, int]) -> None:
    """Download HumanEval tasks from EvalPlus benchmark.

    Args:
        output_dir: Directory to output task data (e.g., data/tasks/tdd/python)
        task_range: Tuple of (start, end) task IDs (e.g., (0, 5) for tasks 0-4)
    """
    try:
        from evalplus.data import get_human_eval_plus
    except ImportError as e:
        logger.error("Failed to import evalplus: %s", e)
        logger.error("Install with: pip install evalplus")
        raise

    logger.info("Downloading HumanEval tasks %d-%d", task_range[0], task_range[1] - 1)

    # Get HumanEval+ dataset
    dataset = get_human_eval_plus()

    # Process each task in range
    start_id, end_id = task_range
    downloaded_count = 0

    for task_id in range(start_id, end_id):
        humaneval_id = f"HumanEval/{task_id}"

        if humaneval_id not in dataset:
            logger.warning("Task %s not found in dataset, skipping", humaneval_id)
            continue

        task_data = dataset[humaneval_id]
        _process_task(output_dir, task_id, task_data)
        downloaded_count += 1
        logger.info("Downloaded task %d/%d: %s", downloaded_count, end_id - start_id, humaneval_id)

    logger.info("Successfully downloaded %d tasks", downloaded_count)


def _process_task(output_dir: Path, task_id: int, task_data: dict[str, Any]) -> None:
    """Process a single HumanEval task and create directory structure.

    Args:
        output_dir: Base output directory
        task_id: Numeric task ID (0-based)
        task_data: Task data from EvalPlus
    """
    # Extract function name from entry_point
    function_name = task_data["entry_point"]

    # Create task directory with naming convention: task_{001..005}_{function_name}
    task_dir_name = f"task_{task_id + 1:03d}_{function_name}"
    task_dir = output_dir / task_dir_name
    task_dir.mkdir(parents=True, exist_ok=True)

    logger.debug("Processing task %s -> %s", task_id, task_dir)

    # Extract and write spec.py (function signature + docstring)
    _write_spec_file(task_dir, task_data)

    # Extract and write correct implementation
    _write_correct_implementation(task_dir, task_data)

    # Write metadata
    _write_metadata(task_dir, task_id, function_name)


def _write_spec_file(task_dir: Path, task_data: dict[str, Any]) -> None:
    """Write spec.py containing function signature and docstring.

    Args:
        task_dir: Task directory path
        task_data: Task data from EvalPlus
    """
    spec_file = task_dir / "spec.py"

    # The 'prompt' field contains the function signature and docstring
    spec_content = task_data["prompt"]

    spec_file.write_text(spec_content)
    logger.debug("Wrote spec.py for %s", task_dir.name)


def _write_correct_implementation(task_dir: Path, task_data: dict[str, Any]) -> None:
    """Write implementation/correct.py containing canonical solution.

    Args:
        task_dir: Task directory path
        task_data: Task data from EvalPlus
    """
    impl_dir = task_dir / "implementation"
    impl_dir.mkdir(parents=True, exist_ok=True)

    correct_file = impl_dir / "correct.py"

    # The 'canonical_solution' contains the implementation
    # Combine with prompt to get full working code
    prompt = task_data["prompt"]
    solution = task_data["canonical_solution"]

    # Full implementation = prompt (signature + docstring) + canonical_solution (body)
    full_implementation = prompt + solution

    correct_file.write_text(full_implementation)
    logger.debug("Wrote correct.py for %s", task_dir.name)


def _write_metadata(task_dir: Path, task_id: int, function_name: str) -> None:
    """Write metadata.json with task information.

    Args:
        task_dir: Task directory path
        task_id: Numeric task ID (0-based from HumanEval)
        function_name: Name of the function
    """
    metadata_file = task_dir / "metadata.json"

    metadata = {
        "task_id": f"task_{task_id + 1:03d}_{function_name}",
        "function_name": function_name,
        "track": "tdd",
        "source": "evalplus",
    }

    metadata_file.write_text(json.dumps(metadata, indent=2))
    logger.debug("Wrote metadata.json for %s", task_dir.name)


def main() -> None:
    """Main entry point for downloading EvalPlus tasks."""
    # Default: download first 5 tasks to data/tasks/tdd/python
    output_dir = Path("data/tasks/tdd/python")
    task_range = (0, 5)  # HumanEval tasks 0-4

    logger.info("Starting EvalPlus HumanEval task download")
    download_tasks(output_dir, task_range)
    logger.info("Download complete")


if __name__ == "__main__":
    main()
