"""Generate BDD Gherkin feature files from TDD docstring examples.

This script transforms TDD spec.py files into BDD spec.feature files:
- Parses >>> format docstring examples
- Generates Gherkin scenarios with Given/When/Then steps
- Creates BDD task structure with symlinked implementations
"""

import ast
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def parse_docstring_examples(spec_file: Path) -> list[dict[str, str]]:
    """Parse >>> format docstring examples from spec.py.

    Args:
        spec_file: Path to spec.py file

    Returns:
        List of examples with 'call' and 'expected' keys
    """
    content = spec_file.read_text()

    # Regex pattern to match >>> examples and their expected output
    # Matches: >>> function_call(args)
    # Followed by: expected_result
    pattern = r">>> (.+?)\n\s*(.+?)(?=\n\s*(?:>>>|\"\"\")|$)"

    matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)

    examples = []
    for call, expected in matches:
        examples.append({"call": call.strip(), "expected": expected.strip()})

    return examples


def extract_function_name(task_dir: Path) -> str:
    """Extract function name from spec.py or metadata.json.

    Args:
        task_dir: Path to task directory

    Returns:
        Function name
    """
    # Try metadata.json first
    metadata_file = task_dir / "metadata.json"
    if metadata_file.exists():
        metadata = json.loads(metadata_file.read_text())
        if "function_name" in metadata:
            return metadata["function_name"]

    # Fallback: parse spec.py using AST
    spec_file = task_dir / "spec.py"
    if spec_file.exists():
        content = spec_file.read_text()
        tree = ast.parse(content)

        # Find first function definition
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                return node.name

    # Last resort: extract from directory name
    # e.g., task_001_has_close_elements -> has_close_elements
    parts = task_dir.name.split("_", 2)
    if len(parts) >= 3:
        return parts[2]

    raise ValueError(f"Could not extract function name from {task_dir}")


def extract_docstring(spec_file: Path) -> str:
    """Extract docstring from spec.py function.

    Args:
        spec_file: Path to spec.py file

    Returns:
        Docstring text
    """
    content = spec_file.read_text()
    tree = ast.parse(content)

    # Find first function definition with docstring
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            docstring = ast.get_docstring(node)
            if docstring:
                return docstring

    return ""


def generate_gherkin_content(
    function_name: str, docstring: str, examples: list[dict[str, str]]
) -> str:
    """Generate Gherkin feature file content from parsed examples.

    Args:
        function_name: Name of the function
        docstring: Function docstring
        examples: List of parsed examples

    Returns:
        Gherkin feature file content
    """
    # Extract first line of docstring as feature description
    description_lines = docstring.split("\n")
    feature_desc = description_lines[0].strip() if description_lines else function_name

    lines = [f"Feature: {function_name}", f"  {feature_desc}", ""]

    # Generate scenarios from examples
    for idx, example in enumerate(examples, start=1):
        call = example["call"]
        expected = example["expected"]

        # Parse function call to extract arguments
        # e.g., has_close_elements([1.0, 2.0, 3.0], 0.5)
        # Extract: numbers=[1.0, 2.0, 3.0], threshold=0.5
        match = re.match(rf"{function_name}\((.*)\)", call)
        args_str = match.group(1) if match else ""

        lines.extend(
            [
                f"  Scenario: Example {idx}",
                f"    Given the function {function_name}",
                f"    When called with {args_str}",
                f"    Then the result should be {expected}",
                "",
            ]
        )

    return "\n".join(lines)


def generate_bdd_task(tdd_task_dir: Path, bdd_root: Path) -> None:
    """Generate BDD task from a single TDD task.

    Args:
        tdd_task_dir: Path to TDD task directory
        bdd_root: Root directory for BDD tasks (e.g., data/tasks/bdd/python)
    """
    # Extract task information
    task_id = tdd_task_dir.name
    function_name = extract_function_name(tdd_task_dir)

    # Create BDD task directory
    bdd_task_dir = bdd_root / task_id
    bdd_task_dir.mkdir(parents=True, exist_ok=True)

    # Parse TDD spec.py
    spec_file = tdd_task_dir / "spec.py"
    examples = parse_docstring_examples(spec_file)
    docstring = extract_docstring(spec_file)

    # Generate Gherkin spec.feature
    gherkin_content = generate_gherkin_content(function_name, docstring, examples)
    feature_file = bdd_task_dir / "spec.feature"
    feature_file.write_text(gherkin_content)

    logger.debug("Generated spec.feature for %s", task_id)

    # Create symlink to TDD implementation directory
    tdd_impl_dir = tdd_task_dir / "implementation"
    bdd_impl_link = bdd_task_dir / "implementation"

    # Create relative symlink
    # Calculate relative path from bdd_task_dir to tdd_impl_dir
    rel_path = os.path.relpath(tdd_impl_dir, bdd_task_dir)

    if bdd_impl_link.exists():
        bdd_impl_link.unlink()

    bdd_impl_link.symlink_to(rel_path)

    logger.debug("Created symlink for implementation: %s -> %s", bdd_impl_link, rel_path)

    # Generate BDD metadata.json
    tdd_metadata_file = tdd_task_dir / "metadata.json"
    tdd_metadata = {}
    if tdd_metadata_file.exists():
        tdd_metadata = json.loads(tdd_metadata_file.read_text())

    bdd_metadata = {
        "task_id": task_id,
        "function_name": function_name,
        "track": "bdd",
        "tdd_source": str(tdd_task_dir),
    }

    # Preserve source if it exists in TDD metadata
    if "source" in tdd_metadata:
        bdd_metadata["source"] = tdd_metadata["source"]

    metadata_file = bdd_task_dir / "metadata.json"
    metadata_file.write_text(json.dumps(bdd_metadata, indent=2))

    logger.debug("Wrote metadata.json for %s", task_id)


def generate_bdd_from_tdd(tdd_root: Path, bdd_root: Path) -> None:
    """Generate BDD tasks from all TDD tasks.

    Args:
        tdd_root: Root directory for TDD tasks (e.g., data/tasks/tdd/python)
        bdd_root: Root directory for BDD tasks (e.g., data/tasks/bdd/python)
    """
    logger.info("Generating BDD tasks from %s to %s", tdd_root, bdd_root)

    # Find all TDD task directories
    task_dirs = sorted([d for d in tdd_root.iterdir() if d.is_dir() and d.name.startswith("task_")])

    if not task_dirs:
        logger.warning("No TDD task directories found in %s", tdd_root)
        return

    generated_count = 0

    for tdd_task_dir in task_dirs:
        try:
            generate_bdd_task(tdd_task_dir, bdd_root)
            generated_count += 1
            logger.info("Generated BDD task for %s", tdd_task_dir.name)
        except (FileNotFoundError, ValueError) as e:
            logger.error("Failed to generate BDD task for %s: %s", tdd_task_dir.name, e)
            continue

    logger.info("Successfully generated %d BDD tasks", generated_count)


def main() -> None:
    """Main entry point for BDD generation."""
    # Configure logging for CLI usage
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Default: process all TDD tasks
    tdd_root = Path("data/tasks/tdd/python")
    bdd_root = Path("data/tasks/bdd/python")

    if not tdd_root.exists():
        logger.error("TDD directory not found: %s", tdd_root)
        logger.error("Run download_evalplus.py first to download tasks")
        return

    logger.info("Starting BDD generation")
    generate_bdd_from_tdd(tdd_root, bdd_root)
    logger.info("BDD generation complete")


if __name__ == "__main__":
    main()
