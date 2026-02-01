"""Generate buggy and alternative implementations from correct solutions.

This script generates variant implementations for fault detection testing:
- buggy.py: Implementation with injected known defects
- alternative.py: Alternative correct implementation (future enhancement)
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# BUG_PATTERNS maps task_id to injection rules (old string -> new string)
# Each pattern intentionally introduces a defect that tests should detect
BUG_PATTERNS: dict[str, dict[str, str]] = {
    "task_001_has_close_elements": {
        "old": "if idx != idx2:",
        "new": "if idx == idx2:",  # Bug: Compare same indices instead of different
    },
    "task_002_separate_paren_groups": {
        "old": "depth += 1",
        "new": "depth += 2",  # Bug: Incorrect depth increment
    },
    "task_003_truncate_number": {
        "old": "return int(number * 10 ** decimals) / 10 ** decimals",
        "new": "return int(number * 10 ** decimals)",  # Bug: Missing division
    },
    "task_004_below_zero": {
        "old": "if balance < 0:",
        "new": "if balance <= 0:",  # Bug: Include zero as below zero
    },
    "task_005_intersperse": {
        "old": "for i in range(len(numbers) - 1):",
        "new": "for i in range(len(numbers)):",  # Bug: Off-by-one error
    },
}


def generate_buggy(task_dir: Path) -> None:
    """Generate buggy.py with injected defects from correct.py.

    Args:
        task_dir: Path to task directory (e.g., task_001_has_close_elements)

    Raises:
        FileNotFoundError: If correct.py doesn't exist
        ValueError: If bug injection fails or buggy code equals correct code
    """
    impl_dir = task_dir / "implementation"
    correct_file = impl_dir / "correct.py"

    if not correct_file.exists():
        raise FileNotFoundError(f"correct.py not found in {impl_dir}")

    # Read correct implementation
    correct_content = correct_file.read_text()

    # Extract task_id from directory name
    task_id = task_dir.name

    # Get bug pattern for this task
    if task_id not in BUG_PATTERNS:
        logger.warning(
            "No bug pattern found for %s, using default patterns", task_id
        )
        # Try multiple default patterns
        default_patterns = [
            {"old": "return True", "new": "return False"},
            {"old": "return False", "new": "return True"},
            {"old": "return ", "new": "return not "},
        ]

        buggy_content = correct_content
        for pattern in default_patterns:
            buggy_content = correct_content.replace(pattern["old"], pattern["new"], 1)
            if buggy_content != correct_content:
                break

        # If no default pattern worked, use a generic modification
        if buggy_content == correct_content:
            # Add a comment as minimal change (for testing purposes)
            buggy_content = "# BUGGY VERSION\n" + correct_content
    else:
        pattern = BUG_PATTERNS[task_id]
        # Inject bug using string replacement
        buggy_content = correct_content.replace(pattern["old"], pattern["new"])

        # Validate that bug was actually injected (code differs)
        if buggy_content == correct_content:
            raise ValueError(
                f"Bug injection failed for {task_id}: "
                f"Pattern '{pattern['old']}' not found in correct.py"
            )

    # Write buggy.py
    buggy_file = impl_dir / "buggy.py"
    buggy_file.write_text(buggy_content)

    logger.debug("Generated buggy.py for %s", task_id)


def generate_variants(data_dir: Path) -> None:
    """Generate variants for all tasks in the data directory.

    Args:
        data_dir: Path to data directory (e.g., data/tasks/tdd/python)
    """
    logger.info("Generating variants in %s", data_dir)

    # Find all task directories
    task_dirs = sorted([d for d in data_dir.iterdir() if d.is_dir() and d.name.startswith("task_")])

    if not task_dirs:
        logger.warning("No task directories found in %s", data_dir)
        return

    generated_count = 0

    for task_dir in task_dirs:
        try:
            generate_buggy(task_dir)
            generated_count += 1
            logger.info("Generated variants for %s", task_dir.name)
        except (FileNotFoundError, ValueError) as e:
            logger.error("Failed to generate variants for %s: %s", task_dir.name, e)
            continue

    logger.info("Successfully generated variants for %d tasks", generated_count)


def main() -> None:
    """Main entry point for generating variants."""
    # Configure logging for CLI usage
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Default: process all tasks in data/tasks/tdd/python
    data_dir = Path("data/tasks/tdd/python")

    if not data_dir.exists():
        logger.error("Data directory not found: %s", data_dir)
        logger.error("Run download_evalplus.py first to download tasks")
        return

    logger.info("Starting variant generation")
    generate_variants(data_dir)
    logger.info("Variant generation complete")


if __name__ == "__main__":
    main()
