# Purple Agent User Stories

## Epic: Baseline Test Generation from Specifications

As a **test subject (assessee agent)**, I need the Purple Agent to generate quality tests from specifications so that the Green Agent can evaluate my test generation capabilities.

---

## Story 1: Serve A2A Discovery Endpoint

**As a** Purple Agent
**I want to** serve the A2A agent-card endpoint
**So that** Green Agent can discover my capabilities

### Acceptance Criteria:
- [ ] Serve on port 9010
- [ ] GET /.well-known/agent-card.json returns metadata
- [ ] Include name, version, capabilities
- [ ] Include supported tracks (TDD, BDD)
- [ ] Follow A2A protocol specification

### Response Schema:
```json
{
  "name": "testbehavealign-purple",
  "version": "0.1.0",
  "capabilities": ["test-generation"],
  "tracks": ["tdd", "bdd"]
}
```

---

## Story 2: Receive Test Generation Requests

**As a** Purple Agent
**I want to** receive test generation requests via A2A
**So that** I can process specifications and generate tests

### Acceptance Criteria:
- [ ] POST /generate-tests endpoint
- [ ] Parse request JSON: `{spec: str, track: "tdd"|"bdd"}`
- [ ] Validate track is supported
- [ ] Validate spec is non-empty
- [ ] Return 400 on invalid input
- [ ] Return 500 on generation errors

### Endpoint:
- `POST /generate-tests`
- Input: `{spec: str, track: "tdd"|"bdd"}`
- Output: `{tests: str}`

---

## Story 3: Generate TDD Tests from Docstrings

**As a** Purple Agent
**I want to** generate pytest tests from Python docstrings
**So that** I can evaluate TDD test generation quality

### Acceptance Criteria:
- [ ] Parse function signature from spec.py
- [ ] Extract docstring examples (>>> examples)
- [ ] Generate pytest test functions
- [ ] Cover edge cases mentioned in docstring
- [ ] Follow pytest naming conventions
- [ ] Return valid Python code (no syntax errors)

### Input Example:
```python
def has_close_elements(numbers: List[float], threshold: float) -> bool:
    """Check if any two numbers are closer than threshold.

    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
    False
    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
    True
    """
```

### Output Example:
```python
import pytest
from solution import has_close_elements

def test_has_close_elements_no_close():
    assert has_close_elements([1.0, 2.0, 3.0], 0.5) == False

def test_has_close_elements_with_close():
    assert has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3) == True

def test_has_close_elements_empty():
    assert has_close_elements([], 0.1) == False
```

---

## Story 4: Generate BDD Tests from Gherkin

**As a** Purple Agent
**I want to** generate pytest-bdd step definitions from Gherkin features
**So that** I can evaluate BDD test generation quality

### Acceptance Criteria:
- [ ] Parse Gherkin feature file
- [ ] Extract Given/When/Then steps
- [ ] Generate pytest-bdd step definitions
- [ ] Implement step logic
- [ ] Follow pytest-bdd conventions
- [ ] Return valid Python code

### Input Example:
```gherkin
Feature: Close Elements Detection
  Scenario: No elements are close
    Given a list of numbers [1.0, 2.0, 3.0]
    And a threshold of 0.5
    When I check for close elements
    Then the result should be False
```

### Output Example (illustrative):
```python
from pytest_bdd import scenarios, given, when, then, parsers
import json
from solution import has_close_elements

scenarios('spec.feature')

@given(parsers.parse('a list of numbers {numbers}'))
def numbers_list(numbers):
    return json.loads(numbers)  # Safe parsing instead of eval

@given(parsers.parse('a threshold of {threshold:f}'))
def threshold_value(threshold):
    return threshold

@when('I check for close elements')
def check_close(numbers_list, threshold_value):
    return has_close_elements(numbers_list, threshold_value)

@then(parsers.parse('the result should be {expected}'))
def check_result(check_close, expected):
    assert check_close == (expected == 'True')
```

---

## Story 5: Call LLM for Test Generation

**As a** Purple Agent
**I want to** use OpenAI API to generate test code
**So that** I can leverage LLM capabilities

### Acceptance Criteria:
- [ ] Load OPENAI_API_KEY from environment
- [ ] Construct prompt based on track (TDD or BDD)
- [ ] Call OpenAI API (gpt-4 or gpt-3.5-turbo)
- [ ] Parse code from LLM response
- [ ] Handle API errors (rate limits, timeouts)
- [ ] Retry failed requests (up to 3 times)
- [ ] Log token usage

### Prompt Template (TDD):
```
Generate pytest tests for the following Python function.

Specification:
{spec}

Requirements:
- Use pytest framework
- Cover all docstring examples
- Add edge cases (empty input, boundary values)
- Follow pytest naming conventions
- Return only the test code, no explanations

Output:
```

### Prompt Template (BDD):
```
Generate pytest-bdd step definitions for the following Gherkin feature.

Feature:
{spec}

Requirements:
- Use pytest-bdd framework
- Implement all Given/When/Then steps
- Import function from solution.py
- Return only the step definitions, no explanations

Output:
```

---

## Story 6: Validate Generated Test Code

**As a** Purple Agent
**I want to** validate generated test code before returning
**So that** I ensure syntactically correct output

### Acceptance Criteria:
- [ ] Parse generated code with ast.parse()
- [ ] Check for syntax errors
- [ ] Verify required imports (pytest, pytest-bdd)
- [ ] Verify test function definitions exist
- [ ] Return error if validation fails
- [ ] Log validation failures

### Validation Checks:
```python
import ast

def validate_test_code(code: str, track: str) -> bool:
    # 1. Parse syntax
    try:
        ast.parse(code)
    except SyntaxError:
        return False

    # 2. Check imports
    if track == "tdd":
        if "import pytest" not in code:
            return False
    elif track == "bdd":
        if "from pytest_bdd" not in code:
            return False

    # 3. Check test functions
    if track == "tdd":
        if not any(line.startswith("def test_") for line in code.split("\n")):
            return False

    return True
```

---

## Story 7: Handle Track Switching

**As a** Purple Agent
**I want to** support both TDD and BDD modes
**So that** I can generate appropriate tests per track

### Acceptance Criteria:
- [ ] Read track from request payload
- [ ] Branch logic: TDD → pytest, BDD → pytest-bdd
- [ ] Use different prompts per track
- [ ] Return error if track unsupported
- [ ] Include track in response metadata

### Logic:
```python
def generate_tests(spec: str, track: str) -> str:
    if track == "tdd":
        return generate_pytest(spec)  # LLM call
    elif track == "bdd":
        return generate_pytest_bdd(spec)  # LLM call
    else:
        raise ValueError(f"Unsupported track: {track}")
```

---

## Story 8: Return Test Code to Green Agent

**As a** Purple Agent
**I want to** return generated test code in A2A format
**So that** Green Agent can execute tests

### Acceptance Criteria:
- [ ] Return JSON response: `{tests: str}`
- [ ] Include metadata: generation_time, token_count
- [ ] Set Content-Type: application/json
- [ ] Return 200 on success
- [ ] Return 500 on generation failure

### Response Schema:
```json
{
  "tests": "import pytest\n\ndef test_example():\n    assert True",
  "metadata": {
    "generation_time": 2.5,
    "token_count": 150,
    "track": "tdd"
  }
}
```

---

## Story 9: Log All Requests

**As a** Purple Agent
**I want to** log all incoming requests and responses
**So that** I can debug test generation issues

### Acceptance Criteria:
- [ ] Log request: timestamp, spec_length, track
- [ ] Log response: success, test_length, generation_time
- [ ] Log errors: stack trace, error message
- [ ] Use structured logging (JSON)
- [ ] Include correlation ID per request

### Log Format:
```json
{
  "timestamp": "2026-01-31T12:00:00Z",
  "level": "INFO",
  "request_id": "abc123",
  "track": "tdd",
  "spec_length": 250,
  "generation_time": 2.3,
  "test_length": 450,
  "status": "success"
}
```

---

## Story 10: Handle Configuration

**As a** Purple Agent
**I want to** load configuration from environment
**So that** I can adapt to different deployment environments

### Acceptance Criteria:
- [ ] Load OPENAI_API_KEY (required)
- [ ] Load PORT (default: 9010)
- [ ] Load LOG_LEVEL (default: INFO)
- [ ] Load LLM_MODEL (default: gpt-4)
- [ ] Load TIMEOUT (default: 30s)
- [ ] Fail fast if required config missing
- [ ] Validate config on startup

### Settings (Pydantic):
```python
class PurpleSettings(BaseSettings):
    openai_api_key: str
    port: int = 9010
    log_level: str = "INFO"
    llm_model: str = "gpt-4"
    timeout: int = 30
```

---

## Non-Functional Requirements

### Performance:
- Generate tests in under 10 seconds per spec
- Handle concurrent requests (up to 5)

### Reliability:
- Retry LLM calls on transient errors
- Graceful degradation (return simple tests if LLM fails)
- Health check endpoint

### Observability:
- Structured logging
- Metrics: generation_time, token_usage, error_rate
- Trace LLM API calls

### Security:
- Validate all inputs
- Sanitize LLM responses (no code injection)
- Rate limit requests (10/min)
