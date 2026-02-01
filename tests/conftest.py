"""Pytest configuration and shared fixtures."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_evalplus():
    """Auto-mock evalplus import for all tests."""
    mock_data = {
        "HumanEval/0": {
            "task_id": "HumanEval/0",
            "entry_point": "has_close_elements",
            "prompt": '''from typing import List


def has_close_elements(numbers: List[float], threshold: float) -> bool:
    """Check if in given list of numbers, are any two numbers closer to each other than
    given threshold.
    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
    False
    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
    True
    """
''',
            "canonical_solution": """    for idx, elem in enumerate(numbers):
        for idx2, elem2 in enumerate(numbers):
            if idx != idx2:
                distance = abs(elem - elem2)
                if distance < threshold:
                    return True

    return False
""",
        },
        "HumanEval/1": {
            "task_id": "HumanEval/1",
            "entry_point": "separate_paren_groups",
            "prompt": '''from typing import List


def separate_paren_groups(paren_string: str) -> List[str]:
    """Input to this function is a string containing multiple groups of nested parentheses.
    Your goal is to separate those group into separate strings and return the list of those.
    Separate groups are balanced (each open brace is properly closed) and not nested within each other
    Ignore any spaces in the input string.
    >>> separate_paren_groups('( ) (( )) (( )( ))')
    ['()', '(())', '(()())']
    """
''',
            "canonical_solution": """    result = []
    current_string = []
    current_depth = 0

    for c in paren_string:
        if c == '(':
            current_depth += 1
            current_string.append(c)
        elif c == ')':
            current_depth -= 1
            current_string.append(c)

            if current_depth == 0:
                result.append(''.join(current_string))
                current_string.clear()

    return result
""",
        },
        "HumanEval/2": {
            "task_id": "HumanEval/2",
            "entry_point": "truncate_number",
            "prompt": '''

def truncate_number(number: float) -> float:
    """Given a positive floating point number, it can be decomposed into
    and integer part (largest integer smaller than given number) and decimals
    (leftover part always smaller than 1).

    Return the decimal part of the number.
    >>> truncate_number(3.5)
    0.5
    """
''',
            "canonical_solution": """    return number % 1.0
""",
        },
        "HumanEval/3": {
            "task_id": "HumanEval/3",
            "entry_point": "below_zero",
            "prompt": '''from typing import List


def below_zero(operations: List[int]) -> bool:
    """You're given a list of deposit and withdrawal operations on a bank account that starts with
    zero balance. Your task is to detect if at any point the balance of account fallls below zero,
    and at that point function should return True. Otherwise it should return False.
    >>> below_zero([1, 2, 3])
    False
    >>> below_zero([1, 2, -4, 5])
    True
    """
''',
            "canonical_solution": """    balance = 0

    for op in operations:
        balance += op
        if balance < 0:
            return True

    return False
""",
        },
        "HumanEval/4": {
            "task_id": "HumanEval/4",
            "entry_point": "mean_absolute_deviation",
            "prompt": '''from typing import List


def mean_absolute_deviation(numbers: List[float]) -> float:
    """For a given list of input numbers, calculate Mean Absolute Deviation
    around the mean of this dataset.
    Mean Absolute Deviation is the average absolute difference between each
    element and a centerpoint (mean in this case):
    MAD = average | x - x_mean |
    >>> mean_absolute_deviation([1.0, 2.0, 3.0, 4.0])
    1.0
    """
''',
            "canonical_solution": """    mean = sum(numbers) / len(numbers)
    return sum(abs(x - mean) for x in numbers) / len(numbers)
""",
        },
    }

    # Mock the evalplus module
    with patch.dict("sys.modules", {"evalplus": MagicMock(), "evalplus.data": MagicMock()}):
        import sys

        sys.modules["evalplus.data"].get_human_eval_plus = MagicMock(return_value=mock_data)
        yield mock_data
