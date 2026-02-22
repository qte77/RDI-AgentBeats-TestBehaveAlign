# Tools Evaluation for Test-First-Quality-Bench

## Purpose

Evaluate testing tools for the Test-First-Quality-Bench benchmark (both TDD and BDD tracks).

---

## Tools Evaluated

| Tool | Type | Primary Use | Source |
|------|------|-------------|--------|
| **Gherkin** | Specification Language | Structured spec format | [GitHub](https://github.com/cucumber/gherkin) |
| **behave** | BDD Framework | Python BDD test execution | [GitHub](https://github.com/behave/behave) |
| **Hypothesis** | Property-Based Testing | Automated test generation | [Docs](https://hypothesis.readthedocs.io/en/latest/) |
| **pytest-bdd** | BDD Framework | pytest + Gherkin integration | [Docs](https://pytest-bdd.readthedocs.io/en/latest/) |
| **mutmut** | Mutation Testing | Test suite quality measurement | [Docs](https://mutmut.readthedocs.io/en/latest/) |

---

## 1. Gherkin

**Source**: [github.com/cucumber/gherkin](https://github.com/cucumber/gherkin)

### What It Is

Gherkin is a parser and compiler for the Gherkin language - a human-readable, business-friendly syntax for writing executable specifications. It transforms `.feature` files into Abstract Syntax Trees (ASTs) and "Pickles" (simplified structures for test execution).

### Syntax Format

```gherkin
Feature: Email Validation
  As a form developer
  I want to validate email addresses
  So that invalid data is rejected

  Scenario: Valid email with standard format
    Given an email "user@example.com"
    When I validate the email
    Then the result should be True

  Scenario Outline: Invalid emails
    Given an email "<email>"
    When I validate the email
    Then the result should be False

    Examples:
      | email           |
      | invalid         |
      | user@@test.com  |
      | @nodomain.com   |
```

### Usefulness for Test-First-Quality-Bench: 3/3 HIGH

| Benefit | Relevance to Benchmark |
|---------|------------------------|
| **Structured spec format** | Acceptance criteria become directly parseable |
| **Multi-language support** | 12+ language implementations (Python, JS, Go, etc.) |
| **Human-readable** | Specs can be written by non-developers |
| **Machine-parseable** | Enables automated spec coverage calculation |
| **Scenario Outlines** | Built-in parameterized test specification |
| **i18n support** | 60+ languages for international specs |

### Integration Recommendation

**Use Gherkin as the PRIMARY spec format** for Test-First-Quality-Bench tasks:

1. **Spec → Gherkin**: Convert PRD.md acceptance criteria to `.feature` files
2. **Parse Gherkin**: Use Gherkin parser to extract scenarios programmatically
3. **Measure Coverage**: Map generated tests to Gherkin scenarios
4. **Spec Coverage Metric**: `# scenarios covered / # total scenarios`

### Example Integration

```python
# spec_coverage.py
from gherkin.parser import Parser

def extract_scenarios(feature_file: str) -> list[str]:
    """Extract scenario names from Gherkin feature file."""
    parser = Parser()
    feature = parser.parse(feature_file)
    scenarios = []
    for child in feature['feature']['children']:
        if 'scenario' in child:
            scenarios.append(child['scenario']['name'])
    return scenarios

def calculate_spec_coverage(scenarios: list[str], test_names: list[str]) -> float:
    """Calculate what % of Gherkin scenarios are covered by tests."""
    covered = sum(1 for s in scenarios if any(s.lower() in t.lower() for t in test_names))
    return covered / len(scenarios) if scenarios else 0.0
```

---

## 2. behave

**Source**: [github.com/behave/behave](https://github.com/behave/behave)

### What It Is

behave is a BDD framework for Python that executes Gherkin `.feature` files using step definitions written in Python.

### How It Works

```
features/
├── email_validator.feature    # Gherkin specs
└── steps/
    └── email_steps.py         # Python step definitions
```

```python
# steps/email_steps.py
from behave import given, when, then

@given('an email "{email}"')
def step_given_email(context, email):
    context.email = email

@when('I validate the email')
def step_validate(context):
    context.result = validate_email(context.email)

@then('the result should be {expected}')
def step_check_result(context, expected):
    assert context.result == (expected == 'True')
```

### Usefulness for Test-First-Quality-Bench: 2/3 MODERATE

| Benefit | Limitation |
|---------|-----------|
| Native Gherkin execution | Separate from pytest ecosystem |
| Clean step definition syntax | Requires context object for state |
| Good for BDD workflows | Less flexible than pytest-bdd |

### Recommendation

**Use behave as an ALTERNATIVE to pytest-bdd**, not primary:
- Consider if benchmark needs standalone BDD execution
- Useful if agents are expected to generate behave-style tests
- pytest-bdd preferred for pytest integration

---

## 3. Hypothesis

**Source**: [hypothesis.readthedocs.io](https://hypothesis.readthedocs.io/en/latest/), [JOSS Paper](https://joss.theoj.org/papers/10.21105/joss.01891.pdf)

### What It Is

Hypothesis is a property-based testing library for Python. Instead of writing specific test cases, you define properties that should hold for ALL valid inputs, and Hypothesis generates test cases automatically.

### How It Works

```python
from hypothesis import given, strategies as st

@given(st.emails())
def test_valid_email_format(email):
    """Property: All generated emails should be valid."""
    assert validate_email(email) == True

@given(st.text())
def test_invalid_random_strings(text):
    """Property: Random strings are usually not valid emails."""
    # Most random text should fail validation
    if '@' not in text or '.' not in text.split('@')[-1]:
        assert validate_email(text) == False
```

### Key Features

| Feature | Description | Source |
|---------|-------------|--------|
| **Automatic test generation** | Generates diverse inputs from strategies | [Docs](https://hypothesis.readthedocs.io/en/latest/) |
| **Shrinking** | Minimizes failing cases for easier debugging | [Docs](https://hypothesis.readthedocs.io/en/latest/) |
| **Edge case discovery** | Finds boundary conditions automatically | [JOSS Paper](https://joss.theoj.org/papers/10.21105/joss.01891.pdf) |
| **Proven effectiveness** | Found bugs in numpy, astropy, other major libraries | [JOSS Paper](https://joss.theoj.org/papers/10.21105/joss.01891.pdf) |

### Research on Mutation Scores

**Source**: [Property-Based Mutation Testing Research](https://www.researchgate.net/publication/367652489_Property-Based_Mutation_Testing)

- Property-based tests can improve mutation scores by 1-4 percentage points over traditional tests
- Particularly effective at catching arithmetic operator mutations
- Research on "Teralizer" showed property-based test transformation improves fault detection

### Usefulness for Test-First-Quality-Bench: 3/3 HIGH

| Benefit | Relevance to Benchmark |
|---------|------------------------|
| **Generates edge cases** | Tests spec edge cases agents might miss |
| **Higher mutation scores** | Property tests kill more mutants ([source](https://www.researchgate.net/publication/367652489_Property-Based_Mutation_Testing)) |
| **Spec-driven by design** | Properties ARE specifications |
| **Detects overfitting** | Random inputs break implementation-specific assumptions |

### Integration Recommendation

**Use Hypothesis to AUGMENT spec coverage measurement**:

1. **Agent generates tests** → Traditional example-based tests
2. **Evaluate with Hypothesis** → Can the spec be expressed as properties?
3. **Compare mutation scores** → Agent tests vs property tests
4. **Quality indicator** → If property tests kill more mutants, agent tests are weak

### Example: Benchmark Task Enhancement

```python
# Task: Email Validator
# spec.feature defines scenarios
# Agent generates: test_email.py (example-based)
# Benchmark adds: test_email_properties.py (Hypothesis)

from hypothesis import given, strategies as st, assume

# Property 1: Valid emails have exactly one @
@given(st.emails())
def test_valid_emails_accepted(email):
    assert validate_email(email) == True

# Property 2: No @ means invalid
@given(st.text().filter(lambda x: '@' not in x))
def test_no_at_symbol_invalid(text):
    assert validate_email(text) == False

# Property 3: Multiple @ means invalid
@given(st.text(), st.text(), st.text())
def test_multiple_at_invalid(a, b, c):
    email = f"{a}@{b}@{c}"
    assert validate_email(email) == False
```

### Advanced: Property-Based Mutation Testing (PBMT)

**Source**: [TU Wien Research](https://www.tuwien.at/doc/res/wp-content/uploads/2023/05/property-based-mutation-testing.pdf)

PBMT validates test suites against specific requirements (safety properties), not just general fault detection. This aligns with Test-First-Quality-Bench's goal of measuring spec-driven test quality.

---

## 4. pytest-bdd

**Source**: [pytest-bdd.readthedocs.io](https://pytest-bdd.readthedocs.io/en/latest/)

### What It Is

pytest-bdd integrates Gherkin BDD with pytest, allowing `.feature` files to be executed using pytest's infrastructure.

### Key Advantage

> "Unlike many other BDD tools, it does not require a separate runner and benefits from the power and flexibility of pytest."

### How It Works

```python
# test_email.py
from pytest_bdd import scenarios, given, when, then, parsers

scenarios('features/email_validator.feature')

@given(parsers.parse('an email "{email}"'))
def email_input(email):
    return {'email': email}

@when('I validate the email')
def validate(email_input):
    email_input['result'] = validate_email(email_input['email'])

@then(parsers.parse('the result should be {expected}'))
def check_result(email_input, expected):
    assert email_input['result'] == (expected == 'True')
```

### Features

| Feature | Description |
|---------|-------------|
| **pytest integration** | Uses pytest fixtures, markers, plugins |
| **Dependency injection** | Step functions receive fixtures as parameters |
| **Multiple parsers** | String, parse, regex, custom |
| **Scenario Outlines** | Parametrized tests from Gherkin tables |
| **Auto-discovery** | `@scenarios()` finds all feature files |

### Usefulness for Test-First-Quality-Bench: 3/3 HIGH

| Benefit | Relevance to Benchmark |
|---------|------------------------|
| **pytest ecosystem** | Works with mutmut, coverage, fixtures |
| **Fixture reuse** | Unit test fixtures work in BDD steps |
| **No separate runner** | Single `pytest` command runs everything |
| **Standard output** | pytest-style results, JUnit XML, etc. |

### Integration Recommendation

**Use pytest-bdd as the PRIMARY test execution framework**:

1. **Specs in Gherkin** → `.feature` files
2. **Agent generates** → Step definitions (Python functions)
3. **Execute with pytest** → `pytest --bdd`
4. **Mutation testing** → `mutmut run` (pytest integration)
5. **Coverage** → pytest-cov plugin

### Example Workflow

```bash
# 1. Task structure
tasks/python/easy/task_001_email_validator/
├── spec/
│   └── email_validator.feature    # Gherkin spec (given to agent)
├── implementation/
│   └── correct.py                 # Hidden implementation
└── generated/
    └── test_steps.py              # Agent generates this

# 2. Agent receives
# - email_validator.feature
# - Function signature: def validate_email(email: str) -> bool

# 3. Agent generates test_steps.py with step definitions

# 4. Benchmark runs
pytest generated/test_steps.py --bdd
mutmut run --paths-to-mutate=implementation/correct.py
```

---

## 5. mutmut

**Source**: [mutmut.readthedocs.io](https://mutmut.readthedocs.io/en/latest/), [GitHub](https://github.com/boxed/mutmut), [PyPI](https://pypi.org/project/mutmut/)

### What It Is

mutmut is a mutation testing system for Python 3 designed for ease of use. It systematically modifies source code (introduces "mutants") to verify that your test suite can detect the changes. If tests pass despite a mutation, the test suite has a gap.

**Version**: 3.4.0 (Nov 2025) | **License**: BSD-3-Clause | **Maintainer**: Anders Hovmöller

### Why mutmut Was Created

From the [author's blog post](https://kodare.net/2016/12/01/mutmut-a-python-mutation-testing-system.html):

> "I decided that I absolutely wanted a feature both Cosmic Ray and mutpy lacked: being able to apply a mutation on a source file and not screw up the entire file."

Unlike competitors that use Python's built-in AST (which doesn't preserve formatting), mutmut uses specialized libraries to round-trip code without altering source files.

### Key Features

| Feature | Description |
|---------|-------------|
| **Persistent State** | Remembers completed work for incremental testing |
| **Smart Test Selection** | Automatically identifies relevant tests to execute |
| **Interactive UI** | Terminal-based browsing interface for results |
| **Parallel Execution** | Fast, concurrent mutation testing |
| **Easy Application** | Apply discovered mutants to disk with simple commands |
| **Tool Agnostic** | Works with pytest, unittest, nose—any runner with exit codes |

### Mutation Operators

mutmut implements subtle code modifications:

| Mutation | Example |
|----------|---------|
| Integer increment | `0` → `1`, `5` → `6` |
| Comparison operators | `<` → `<=`, `==` → `!=` |
| Control flow | `break` ↔ `continue` |
| Boolean literals | `True` ↔ `False` |
| Arithmetic operators | `+` → `-`, `*` → `/` |

### Installation & Basic Usage

```bash
# Install
pip install mutmut

# Run mutation testing (auto-detects tests/ folder)
mutmut run

# Browse results interactively
mutmut browse

# Apply a specific mutant to disk
mutmut apply 42

# Run on specific module
mutmut run "my_module*"
```

### System Requirements

- **Python**: >=3.10
- **Fork Support**: Linux/Mac or Windows Subsystem for Linux (WSL)
- **Optional**: Rust toolchain for libcst dependency on some architectures

### Configuration (pyproject.toml)

```toml
[tool.mutmut]
paths_to_mutate = "src/"
tests_dir = "tests/"
runner = "python -m pytest -x --assert=plain"
do_not_mutate = ["**/migrations/*", "**/test_*"]
mutate_only_covered_lines = true
max_stack_depth = 12
```

| Option | Description |
|--------|-------------|
| `paths_to_mutate` | Source directories to test |
| `tests_dir` | Test directory location |
| `runner` | Test command to execute |
| `do_not_mutate` | Exclude files using wildcard patterns |
| `mutate_only_covered_lines` | Enable coverage.py line-level filtering |
| `max_stack_depth` | Limit test-to-function call chain depth |

### Line Whitelisting

Exclude specific lines from mutation:

```python
some_code_here()  # pragma: no mutate
```

### Pytest Integration

mutmut integrates seamlessly with pytest:

```bash
# Run with pytest
mutmut run --runner="pytest -x --tb=no -q"

# Use with pytest-cov for coverage-based filtering
mutmut run --use-coverage

# Parallel execution
mutmut run --runner="pytest -x -n auto"
```

### Interpreting Results

```
Mutants:
  - killed: 45 (tests caught the mutation)
  - survived: 3 (tests missed the mutation - GAP!)
  - suspicious: 1 (test crashed unexpectedly)
  - timeout: 2 (mutation caused infinite loop)

Mutation Score = killed / (killed + survived) = 45/48 = 93.75%
```

### Real-World Value

From the author's experience testing company libraries:

> "Testing on company libraries revealed gaps in test suites despite 100% coverage, including untested edge cases and dead code, demonstrating mutation testing's value beyond traditional coverage metrics."

### Usefulness for Test-First-Quality-Bench: 3/3 CRITICAL

| Benefit | Relevance to Benchmark |
|---------|------------------------|
| **Mutation Score** | Primary metric for test quality beyond coverage |
| **Identifies weak tests** | Tests that pass but don't assert behavior |
| **Finds untested edge cases** | Edge cases missed despite high coverage |
| **Detects dead code** | Code that can be removed without test failure |
| **Incremental testing** | Fast iteration during benchmark development |
| **pytest integration** | Works with pytest-bdd and Hypothesis tests |

### Integration Recommendation

**Use mutmut as the PRIMARY test quality metric** for Test-First-Quality-Bench:

1. **Agent generates tests** → Step definitions for Gherkin specs
2. **Run tests** → `pytest --bdd` to verify tests pass
3. **Mutation testing** → `mutmut run` to measure test quality
4. **Calculate mutation score** → `killed / (killed + survived)`
5. **Compare scores** → Agent tests vs human baseline

### Example Workflow

```bash
# 1. Agent generates tests
# generated/test_steps.py

# 2. Run mutation testing against implementation
mutmut run \
  --paths-to-mutate=implementation/correct.py \
  --runner="pytest generated/test_steps.py -x"

# 3. Get results
mutmut results

# 4. Calculate score
# Mutation Score = killed / total_mutants
```

### Comparison with Other Mutation Tools

| Tool | Ease of Use | Incremental | pytest Integration | Source Preservation |
|------|-------------|-------------|-------------------|---------------------|
| **mutmut** | 3/3 | ✅ | 3/3 | ✅ |
| Cosmic Ray | 2/3 | ✅ | 3/3 | ❌ |
| mutpy | 3/3 | ❌ | 2/3 | ❌ |

---

## Comparative Analysis

### For Test-First-Quality-Bench Spec Format

| Tool | Spec Format | Parseability | Agent Familiarity | Recommendation |
|------|-------------|--------------|-------------------|----------------|
| **Gherkin** | Structured BDD | 3/3 | 3/3 | **PRIMARY** |
| PRD.md (current) | Markdown | 2/3 | 3/3 | Keep as source |
| JSON | Structured | 3/3 | 2/3 | For internal use |

### For Test Execution

| Tool | pytest Integration | Mutation Testing | BDD Support | Recommendation |
|------|-------------------|------------------|-------------|----------------|
| **pytest-bdd** | Native | 3/3 | 3/3 | **PRIMARY** |
| behave | Separate | 2/3 | 3/3 | Alternative |
| Plain pytest | Native | 3/3 | 1/3 | Fallback |

### For Test Quality Enhancement

| Tool | Edge Case Discovery | Mutation Score Impact | Spec Alignment | Recommendation |
|------|---------------------|----------------------|----------------|----------------|
| **Hypothesis** | 3/3 | +1-4% ([source](https://www.researchgate.net/publication/367652489_Property-Based_Mutation_Testing)) | 3/3 | **AUGMENT** |
| Manual examples | 1/3 | Baseline | 2/3 | Agent output |

### For Mutation Testing

| Tool | Ease of Use | Incremental | pytest Integration | Recommendation |
|------|-------------|-------------|-------------------|----------------|
| **mutmut** | 3/3 | ✅ | 3/3 | **PRIMARY** |
| Cosmic Ray | 2/3 | ✅ | 3/3 | Alternative |
| mutpy | 3/3 | ❌ | 2/3 | Legacy |

---

## Recommended Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ SPEC LAYER                                                  │
├─────────────────────────────────────────────────────────────┤
│ PRD.md (ralph-loop) → Gherkin .feature files                │
│ - Human-readable requirements                               │
│ - Machine-parseable scenarios                               │
│ - Spec coverage = scenarios covered / total scenarios       │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ AGENT OUTPUT                                                │
├─────────────────────────────────────────────────────────────┤
│ Agent generates: pytest-bdd step definitions                │
│ - Maps @given/@when/@then to Gherkin steps                  │
│ - Uses pytest fixtures for setup                            │
│ - Optionally: Hypothesis properties for edge cases          │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ EVALUATION LAYER                                            │
├─────────────────────────────────────────────────────────────┤
│ pytest-bdd: Execute BDD tests                               │
│ mutmut: Mutation testing (PRIMARY quality metric)           │
│   → Mutation Score = killed / (killed + survived)           │
│ Hypothesis: Property-based quality check (optional)         │
│ Gherkin parser: Spec coverage calculation                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Updated Task Structure

```
task/
├── docs/
│   ├── UserStory.md              # Ralph-loop input
│   ├── PRD.md                    # Ralph-loop output
│   └── prd.json                  # Structured stories
├── spec/
│   ├── spec.md                   # Agent-visible (derived)
│   └── spec.feature              # Gherkin scenarios (PRIMARY)
├── implementation/               # HIDDEN from agent
│   ├── correct.py
│   ├── buggy_v1.py
│   ├── buggy_v2.py
│   └── alternative.py
├── baselines/
│   ├── human_steps.py            # Human pytest-bdd steps
│   └── human_properties.py       # Human Hypothesis tests (optional)
└── metadata.json
```

---

## Implementation Checklist

### Phase 1: Core Integration
- [ ] Add Gherkin parser to harness (`pip install gherkin-official`)
- [ ] Create PRD.md → Gherkin converter
- [ ] Implement Gherkin-based spec coverage calculation
- [ ] Add pytest-bdd to evaluation dependencies
- [ ] Add mutmut to evaluation dependencies (`pip install mutmut`)

### Phase 2: Agent Evaluation
- [ ] Update agent prompt to request pytest-bdd step definitions
- [ ] Validate agent output can be executed by pytest-bdd
- [ ] Measure spec coverage via Gherkin scenario mapping
- [ ] Run mutmut against agent-generated tests
- [ ] Calculate mutation score as primary quality metric

### Phase 3: Quality Enhancement (Optional)
- [ ] Add Hypothesis baseline tests for comparison
- [ ] Measure mutation score delta: agent tests vs property tests
- [ ] Use delta as quality indicator
- [ ] Compare agent mutation scores vs human baseline mutation scores

---

## Sources

### Tools
- [Gherkin Parser](https://github.com/cucumber/gherkin) - Multi-language Gherkin implementation
- [behave](https://github.com/behave/behave) - Python BDD framework
- [Hypothesis](https://hypothesis.readthedocs.io/en/latest/) - Property-based testing for Python
- [pytest-bdd](https://pytest-bdd.readthedocs.io/en/latest/) - pytest + Gherkin integration
- [mutmut Docs](https://mutmut.readthedocs.io/en/latest/) - Mutation testing documentation
  - [mutmut Blog Post](https://kodare.net/2016/12/01/mutmut-a-python-mutation-testing-system.html) - Author's design rationale

### Research
- [Hypothesis: A new approach to property-based testing](https://joss.theoj.org/papers/10.21105/joss.01891.pdf) - JOSS Paper
- [Property-Based Mutation Testing](https://www.researchgate.net/publication/367652489_Property-Based_Mutation_Testing) - ResearchGate
- [Property-Based Mutation Testing (TU Wien)](https://www.tuwien.at/doc/res/wp-content/uploads/2023/05/property-based-mutation-testing.pdf) - Academic research
- [Mutation Testing Theory](https://mutationtesting.uni.lu/theory.php) - University of Luxembourg
