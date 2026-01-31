# BDD Track: Behavior Test Generation

> For metrics, evaluation flow, and task list see [Test-First-Quality-Bench-Overview.md](Test-First-Quality-Bench-Overview.md)

---

## Spec Format

Agent receives **Gherkin .feature file only** (no implementation):

```gherkin
Feature: Has Close Elements
  As a developer
  I want to check if any two numbers in a list are close
  So that I can detect clustering in data

  Scenario: No close elements in list
    Given a list of numbers [1.0, 2.0, 3.0]
    And a threshold of 0.5
    When I check for close elements
    Then the result should be False

  Scenario: Close elements exist
    Given a list of numbers [1.0, 2.8, 3.0, 4.0, 5.0, 2.0]
    And a threshold of 0.3
    When I check for close elements
    Then the result should be True

  Scenario Outline: Edge cases
    Given a list of numbers <numbers>
    And a threshold of <threshold>
    When I check for close elements
    Then the result should be <expected>

    Examples:
      | numbers    | threshold | expected |
      | [1.0]      | 0.5       | False    |
      | [1.0, 1.0] | 0.0       | False    |
```

---

## Expected Test Output

Agent generates **pytest-bdd step definitions**:

```python
from pytest_bdd import scenarios, given, when, then, parsers
import pytest
import json

scenarios('spec.feature')

@pytest.fixture
def context():
    return {}

@given(parsers.parse('a list of numbers {numbers}'))
def given_numbers(context, numbers):
    context['numbers'] = json.loads(numbers)

@given(parsers.parse('a threshold of {threshold:f}'))
def given_threshold(context, threshold):
    context['threshold'] = threshold

@when('I check for close elements')
def check_close_elements(context):
    from implementation import has_close_elements
    context['result'] = has_close_elements(
        context['numbers'], context['threshold']
    )

@then(parsers.parse('the result should be {expected}'))
def check_result(context, expected):
    assert context['result'] == (expected == 'True')
```

---

## Task Structure

```
tasks/bdd/python/task_001_has_close_elements/
├── spec/
│   └── spec.feature            # Gherkin (VISIBLE)
├── implementation/             # SYMLINK to TDD track
├── baselines/
│   └── human_steps.py          # Ground truth
└── metadata.json
```

**Note**: `implementation/` symlinks to TDD track for same code.

---

## Spec Coverage: Gherkin Parsing

```python
"""BDD Track: Gherkin-based spec coverage."""
from gherkin.parser import Parser

def parse_feature_scenarios(feature_file: str) -> list[str]:
    """Extract scenario names from Gherkin feature file."""
    parser = Parser()
    with open(feature_file) as f:
        feature = parser.parse(f.read())

    scenarios = []
    for child in feature['feature']['children']:
        if 'scenario' in child:
            scenarios.append(child['scenario']['name'])
    return scenarios

def calculate_spec_coverage(scenarios: list, executed: list) -> float:
    """Calculate what % of Gherkin scenarios were executed."""
    covered = sum(1 for s in scenarios if s in executed)
    return covered / len(scenarios) if scenarios else 0.0
```

---

## Data Source

**Derived from EvalPlus** tests → Gherkin scenarios:

```
EvalPlus test:                    Derived Gherkin:
─────────────────                 ─────────────────
def test_no_close():        →     Scenario: No close elements
    assert func([1,2,3], 0.5)       Given a list [1.0, 2.0, 3.0]
        == False                    When I check for close elements
                                    Then the result should be False
```

---

## TDD vs BDD Comparison

| Aspect | TDD | BDD |
|--------|-----|-----|
| Spec format | Docstring | Gherkin |
| Test format | pytest | pytest-bdd |
| Spec parsing | ast module | Gherkin parser |
| Agent familiarity | High | Medium |

---

## References

- [pytest-bdd](https://pytest-bdd.readthedocs.io/)
- [Gherkin](https://github.com/cucumber/gherkin)
- [Cucumber docs](https://cucumber.io/docs/gherkin/)
