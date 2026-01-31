# TDD Track: Unit Test Generation

> For metrics, evaluation flow, and task list see [Test-First-Quality-Bench-Overview.md](Test-First-Quality-Bench-Overview.md)

---

## Spec Format

Agent receives **function signature + docstring only** (no implementation):

```python
def has_close_elements(numbers: List[float], threshold: float) -> bool:
    """
    Check if in given list of numbers, are any two numbers closer to each
    other than given threshold.

    Args:
        numbers: List of floating point numbers
        threshold: Maximum distance between two numbers to be considered close

    Returns:
        True if any two numbers are closer than threshold, False otherwise

    Examples:
        >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
        False
        >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
        True
    """
    pass
```

---

## Expected Test Output

Agent generates **pytest unit tests**:

```python
import pytest
from implementation import has_close_elements

def test_no_close_elements():
    assert has_close_elements([1.0, 2.0, 3.0], 0.5) == False

def test_close_elements_exist():
    assert has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3) == True

def test_empty_list():
    assert has_close_elements([], 0.5) == False

def test_single_element():
    assert has_close_elements([1.0], 0.5) == False
```

---

## Task Structure

```
tasks/tdd/python/task_001_has_close_elements/
├── spec.py                     # Docstring + signature (VISIBLE)
├── implementation/             # HIDDEN from agent
│   ├── correct.py
│   ├── buggy_v1.py
│   └── alternative.py
├── baselines/
│   └── evalplus_tests.py       # Ground truth
└── metadata.json
```

---

## Spec Coverage: Docstring Parsing

```python
"""TDD Track: Docstring-based spec coverage."""
import ast
import re

def parse_docstring_requirements(spec_file: str) -> list[str]:
    """Extract testable requirements from spec.py docstring."""
    with open(spec_file) as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            docstring = ast.get_docstring(node)
            if docstring:
                return extract_requirements(docstring)
    return []

def extract_requirements(docstring: str) -> list[str]:
    """Parse docstring into discrete requirements."""
    requirements = []
    # Extract examples
    examples = re.findall(r'>>>\s+\w+\([^)]+\)\n\s+\S+', docstring)
    requirements.extend(examples)
    return requirements
```

---

## Data Source

**EvalPlus**: 164 HumanEval problems with 80× expanded test suites.

- Extract docstrings → `spec.py`
- Extract canonical solutions → `implementation/correct.py`
- Extract expanded tests → `baselines/evalplus_tests.py`

---

## References

- [EvalPlus](https://github.com/evalplus/evalplus)
- [HumanEval](https://github.com/openai/human-eval)
- [pytest](https://docs.pytest.org/)
