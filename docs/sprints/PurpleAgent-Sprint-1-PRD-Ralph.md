---
title: Product Requirements Document - Purple Agent
version: 2.0
---

## Project Overview

The Purple Agent is a baseline test generator that creates pytest or pytest-bdd tests from specifications. It receives specs from the Green Agent via A2A protocol, generates tests using LLM (OpenAI), and returns valid, executable test code for evaluation.

**Epic**: Baseline Test Generation from Specifications

**Status**: Planning Phase

---

## Functional Requirements

<!-- PARSER REQUIREMENT: Use exactly "#### Feature N:" format -->

#### Feature 1: A2A Discovery Endpoint

**Description**: Serve the A2A agent-card endpoint so that Green Agent can discover capabilities.

**Acceptance Criteria**:
- [ ] Serve on port 9010
- [ ] GET /.well-known/agent-card.json returns metadata
- [ ] Include name, version, capabilities in response
- [ ] Include supported tracks (TDD, BDD)
- [ ] Follow A2A protocol specification
- [ ] GET /health returns health status

**Technical Requirements**:
- Use a2a-sdk AgentCard model
- Configure via PurpleSettings
- Response schema:
  ```json
  {
    "name": "testbehavealign-purple",
    "version": "0.1.0",
    "capabilities": ["test-generation"],
    "tracks": ["tdd", "bdd"]
  }
  ```

**Files**:
- `src/purple/server.py`
- `src/purple/settings.py`

---

#### Feature 2: Test Generation Request Handler

**Description**: Receive test generation requests via A2A to process specifications and generate tests.

**Acceptance Criteria**:
- [ ] POST /generate-tests endpoint
- [ ] Parse request JSON: `{spec: str, track: "tdd"|"bdd"}`
- [ ] Validate track is supported
- [ ] Validate spec is non-empty
- [ ] Return 400 on invalid input with error message
- [ ] Return 500 on generation errors with error details

**Technical Requirements**:
- Use Pydantic for request validation
- Return structured error responses
- Set Content-Type: application/json in responses

**Files**:
- `src/purple/agent.py`
- `src/purple/models.py`
- `src/purple/executor.py`

---

#### Feature 3: TDD Test Generation (pytest)

**Description**: Generate pytest tests from Python docstrings to evaluate TDD test generation quality.

**Acceptance Criteria**:
- [ ] Parse function signature from spec.py
- [ ] Extract docstring examples (>>> examples)
- [ ] Generate pytest test functions
- [ ] Cover edge cases mentioned in docstring
- [ ] Follow pytest naming conventions (`test_<feature>_<scenario>`)
- [ ] Return valid Python code (no syntax errors)
- [ ] Import: `import pytest` and `from solution import <function_name>`

**Technical Requirements**:
- Use LLM with structured prompts for TDD
- Extract function name from spec for imports

**Files**:
- `src/purple/agent.py`

---

#### Feature 4: BDD Test Generation (pytest-bdd)

**Description**: Generate pytest-bdd step definitions from Gherkin features to evaluate BDD test generation quality.

**Acceptance Criteria**:
- [ ] Parse Gherkin feature file
- [ ] Extract Given/When/Then steps
- [ ] Generate pytest-bdd step definitions
- [ ] Implement step logic based on scenario description
- [ ] Follow pytest-bdd conventions
- [ ] Return valid Python code
- [ ] Import: `from pytest_bdd import scenarios, given, when, then, parsers`
- [ ] Include `scenarios('spec.feature')` call

**Technical Requirements**:
- Use LLM with structured prompts for BDD
- Use parsers for parameterized steps: `@given(parsers.parse(...))`

**Files**:
- `src/purple/agent.py`

---

#### Feature 5: LLM Integration

**Description**: Use OpenAI API to generate test code leveraging LLM capabilities.

**Acceptance Criteria**:
- [ ] Load OPENAI_API_KEY from environment (required)
- [ ] Construct prompt based on track (TDD or BDD)
- [ ] Call OpenAI API (gpt-4 or gpt-3.5-turbo)
- [ ] Parse code from LLM response
- [ ] Handle API errors (rate limits, timeouts)
- [ ] Retry failed requests (up to 3 times)
- [ ] Log token usage

**Technical Requirements**:
- Use openai Python SDK
- Implement retry with tenacity or manual backoff
- Extract code blocks from markdown responses
- Implement exponential backoff (1s, 2s, 4s)

**Files**:
- `src/purple/agent.py`
- `src/common/llm_client.py`
- `src/purple/settings.py`

---

#### Feature 6: Code Validation

**Description**: Validate generated test code before returning to ensure syntactically correct output.

**Acceptance Criteria**:
- [ ] Parse generated code with ast.parse()
- [ ] Check for syntax errors
- [ ] Verify required imports (pytest, pytest-bdd)
- [ ] Verify test function definitions exist
- [ ] Return error if validation fails
- [ ] Log validation failures
- [ ] Do NOT execute code (safety)

**Technical Requirements**:
- Use ast module for syntax validation
- Use regex or ast for import/function checks
- TDD: at least one `def test_` function
- BDD: at least one `@given`, `@when`, or `@then` decorator

**Files**:
- `src/purple/agent.py`

---

#### Feature 7: Track Switching

**Description**: Support both TDD and BDD modes to generate appropriate tests per track.

**Acceptance Criteria**:
- [ ] Read track from request payload
- [ ] Branch logic: TDD → pytest, BDD → pytest-bdd
- [ ] Use different prompts per track
- [ ] Return error if track unsupported
- [ ] Include track in response metadata
- [ ] Use simple if/else (KISS principle)

**Technical Requirements**:
- Simple conditional branching
- Track-specific prompt templates

**Files**:
- `src/purple/agent.py`

---

#### Feature 8: Response Format

**Description**: Return generated test code in A2A format so Green Agent can execute tests.

**Acceptance Criteria**:
- [ ] Return JSON response: `{tests: str}`
- [ ] Include metadata: generation_time, token_count, track
- [ ] Set Content-Type: application/json
- [ ] Return 200 on success
- [ ] Return 500 on generation failure
- [ ] Preserve newlines in test code string

**Technical Requirements**:
- Use Pydantic model for response serialization
- Response schema:
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

**Files**:
- `src/purple/models.py`
- `src/purple/agent.py`

---

#### Feature 9: Logging

**Description**: Log all incoming requests and responses for debugging test generation issues.

**Acceptance Criteria**:
- [ ] Log request: timestamp, spec_length, track
- [ ] Log response: success, test_length, generation_time
- [ ] Log errors: stack trace, error message
- [ ] Use structured logging (JSON)
- [ ] Include correlation ID per request
- [ ] Log level configurable via LOG_LEVEL env var

**Technical Requirements**:
- Use Python logging with JSON formatter
- Generate UUID for request IDs

**Files**:
- `src/purple/agent.py`
- `src/purple/settings.py`

---

#### Feature 10: Configuration Management

**Description**: Load configuration from environment to adapt to different deployment environments.

**Acceptance Criteria**:
- [ ] Load OPENAI_API_KEY (required)
- [ ] Load PORT (default: 9010)
- [ ] Load LOG_LEVEL (default: INFO)
- [ ] Load LLM_MODEL (default: gpt-4)
- [ ] Load TIMEOUT (default: 30s)
- [ ] Fail fast if required config missing
- [ ] Validate config on startup
- [ ] Log configuration at startup (excluding secrets)

**Technical Requirements**:
- Use pydantic-settings BaseSettings
- Use PURPLE_ env prefix for agent-specific settings

**Files**:
- `src/purple/settings.py`
- `src/common/settings.py`

---

## Non-Functional Requirements

### Performance
- [ ] Generate tests in < 10 seconds per spec (P95)
- [ ] Handle concurrent requests (up to 5 simultaneous)
- [ ] LLM API call: < 30 seconds with retries
- [ ] Response time: < 1 second for validation errors

### Reliability
- [ ] Retry LLM calls on transient errors (up to 3 times)
- [ ] Implement exponential backoff (1s, 2s, 4s)
- [ ] Timeout: 30 seconds per LLM request
- [ ] Graceful degradation: return error, not crash
- [ ] Health check: `GET /health` returns 200 when operational

### Observability
- [ ] Structured JSON logging (not printf)
- [ ] Request tracing with correlation IDs
- [ ] Metrics: generation_time, token_usage, error_rate
- [ ] All errors logged with full context
- [ ] Startup logs: version, config, capabilities

### Security
- [ ] Validate all inputs (no injection attacks)
- [ ] Never log API keys or secrets
- [ ] Sanitize LLM responses (no arbitrary code execution)
- [ ] Rate limit requests (10 per minute per client IP)
- [ ] No file system writes outside /tmp
- [ ] No network calls outside OpenAI API

### Maintainability
- [ ] Code split by function: models, agent, server, settings
- [ ] Pydantic for data validation
- [ ] Clear error messages for debugging
- [ ] No hardcoded secrets

---

## Module Structure (A2A-Compliant)

The Purple Agent follows the A2A SDK standard module structure:

```
src/purple/
├── __init__.py        # Package init, exports __version__
├── agent.py           # Core business logic (Agent class)
├── executor.py        # A2A execution wrapper (AgentExecutor)
├── server.py          # HTTP server setup (uvicorn, AgentCard)
├── messenger.py       # A2A client (imports from common)
├── models.py          # Domain models (GenerateRequest, TestResponse, etc.)
└── settings.py        # Configuration (pydantic-settings)
```

### Module Responsibilities

| Module | Responsibility | Key Classes/Functions |
|--------|---------------|----------------------|
| `agent.py` | Core test generation logic | `Agent` class with `run(message, updater)` |
| `executor.py` | A2A task lifecycle | `Executor(AgentExecutor)` - manages Agent per context |
| `server.py` | HTTP server setup | `main()` - argparse, AgentCard, AgentSkill, uvicorn |
| `messenger.py` | A2A client communication | Re-exports from `common.messenger` |
| `models.py` | Domain Pydantic models | `GenerateRequest`, `TestResponse`, `GenerationMetadata` |
| `settings.py` | Environment configuration | `PurpleSettings(BaseSettings)` with env prefix |

---

## Dependencies

### Python Packages (from pyproject.toml)

- `a2a-sdk[http-server]>=0.3.0` - Agent-to-agent communication
- `uvicorn>=0.30.0` - ASGI server
- `openai>=1.0.0` - OpenAI API client
- `httpx>=0.27.0` - HTTP client
- `pydantic-settings>=2.12.0` - Environment configuration (includes pydantic)

### External Services

- OpenAI API (gpt-4 or gpt-3.5-turbo)
- Network connectivity (HTTPS to api.openai.com)

---

## Out of Scope

- Green Agent implementation
- Test execution or evaluation
- Mutation testing
- Task data generation
- UI or visualization
- Alternative LLM providers (MVP uses OpenAI only)
- Test optimization (no iterative refinement)
- Caching generated tests (each request generates fresh)
- Multi-language support (Python only)
- Custom prompt templates (fixed prompts for MVP)

---

## Success Metrics

| Metric | Target | Rationale |
|--------|--------|-----------|
| Test Generation Success | 90%+ | Tests generated for 9/10 specs without errors |
| Code Validity | 100% | Generated code is syntactically valid |
| API Availability | 99.9% | Service stays up during evaluation runs |
| Generation Time | < 10s P95 | Meets performance expectations |
| Error Handling | 100% | All errors return proper HTTP status + message |
| Security | 0 secrets in logs | Never expose API keys or credentials |

---

## Notes for Ralph Loop

<!-- PARSER REQUIREMENT: Include story count in parentheses -->
<!-- PARSER REQUIREMENT: Use (depends: STORY-XXX, STORY-YYY) for dependencies -->

Story Breakdown - Phase 1 (10 stories total):

- **Feature 10 (Configuration)** → STORY-001: Implement environment configuration with pydantic-settings
- **Feature 1 (A2A Discovery)** → STORY-002: Implement agent-card.json discovery endpoint (depends: STORY-001)
- **Feature 2 (Request Handler)** → STORY-003: Implement POST /generate-tests with validation (depends: STORY-002)
- **Feature 5 (LLM Integration)** → STORY-004: Implement OpenAI API integration with retries (depends: STORY-001)
- **Feature 3 (TDD Generation)** → STORY-005: Implement pytest test generation (depends: STORY-004)
- **Feature 4 (BDD Generation)** → STORY-006: Implement pytest-bdd step generation (depends: STORY-004)
- **Feature 6 (Code Validation)** → STORY-007: Implement syntax validation with ast.parse (depends: STORY-005, STORY-006)
- **Feature 7 (Track Switching)** → STORY-008: Implement track-based routing (depends: STORY-005, STORY-006)
- **Feature 8 (Response Format)** → STORY-009: Implement structured JSON response (depends: STORY-007, STORY-008)
- **Feature 9 (Logging)** → STORY-010: Implement structured JSON logging (depends: STORY-003)
