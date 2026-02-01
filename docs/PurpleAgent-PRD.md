---
title: Product Requirements Document - Purple Agent
version: 1.0
---

## Project Overview

The Purple Agent is a baseline test generator that creates pytest or pytest-bdd tests from specifications. It receives specs from the Green Agent via A2A protocol, generates tests using LLM (OpenAI), and returns valid, executable test code for evaluation.

**Epic**: Baseline Test Generation from Specifications

**Status**: Planning Phase

---

## Functional Requirements

<!-- PARSER REQUIREMENT: Use exactly "#### Feature N:" format -->

#### Feature 1: A2A Discovery Endpoint

**Description**: Implement A2A-compliant discovery endpoint for agent identification.

**Acceptance Criteria**:
- [ ] Serve HTTP on port 9010
- [ ] Implement `GET /.well-known/agent-card.json` endpoint
  - Return JSON with: `{name, version, capabilities, tracks}`
  - name: "testbehavealign-purple"
  - version: "0.1.0"
  - capabilities: ["test-generation"]
  - tracks: ["tdd", "bdd"]
- [ ] Follow A2A protocol specification
- [ ] Return 200 with valid JSON

**Technical Requirements**:
- Use a2a-sdk AgentCard model
- Configure via PurpleSettings

**Files**:
- `src/purple/server.py`
- `src/purple/settings.py`

---

#### Feature 2: Test Generation Request Handler

**Description**: Handle incoming test generation requests with validation.

**Acceptance Criteria**:
- [ ] Implement `POST /generate-tests` endpoint
- [ ] Parse request JSON:
  - `spec` (string, required): function/feature specification
  - `track` (string, required): "tdd" or "bdd"
- [ ] Validate inputs:
  - spec is non-empty
  - track is "tdd" or "bdd"
  - Return 400 on validation failure with error message
- [ ] Return 500 on generation errors with error details
- [ ] Set Content-Type: application/json in responses

**Technical Requirements**:
- Use Pydantic for request validation
- Return structured error responses

**Files**:
- `src/purple/agent.py`
- `src/purple/models.py`
- `src/purple/executor.py`

---

#### Feature 3: TDD Test Generation (pytest)

**Description**: Generate pytest test functions from Python function specifications.

**Acceptance Criteria**:
- [ ] Parse function signature from spec.py
- [ ] Extract docstring examples (>>> style)
- [ ] Generate pytest test functions:
  - Function names: `test_<feature>_<scenario>`
  - Use standard assertions: `assert condition`
  - Import: `import pytest` and `from solution import <function_name>`
- [ ] Cover docstring examples + edge cases:
  - Empty inputs (if applicable)
  - Boundary values
  - Invalid types (if documented)
- [ ] Return valid Python code (no syntax errors)
- [ ] Code must be executable with `pytest`

**Technical Requirements**:
- Use LLM with structured prompts for TDD
- Extract function name from spec for imports

**Files**:
- `src/purple/agent.py`

---

#### Feature 4: BDD Test Generation (pytest-bdd)

**Description**: Generate pytest-bdd step definitions from Gherkin feature files.

**Acceptance Criteria**:
- [ ] Parse Gherkin feature file
- [ ] Extract Given/When/Then steps from scenarios
- [ ] Generate pytest-bdd step definitions:
  - `@given`, `@when`, `@then` decorators
  - Use `pytest_bdd.scenarios('spec.feature')`
  - Implement step logic based on scenario description
  - Use parsers for parameterized steps: `@given(parsers.parse(...))`
- [ ] Import: `from pytest_bdd import scenarios, given, when, then, parsers`
- [ ] Return valid Python code executable with `pytest-bdd`
- [ ] Steps must match feature file exactly

**Technical Requirements**:
- Use LLM with structured prompts for BDD
- Include scenarios() call in generated code

**Files**:
- `src/purple/agent.py`

---

#### Feature 5: LLM Integration

**Description**: Integrate with OpenAI API for test code generation.

**Acceptance Criteria**:
- [ ] Load `OPENAI_API_KEY` from environment (required)
- [ ] Call OpenAI API (gpt-4 or gpt-3.5-turbo)
- [ ] Construct prompts based on track:
  - TDD: Request pytest test generation
  - BDD: Request pytest-bdd step definitions
- [ ] Parse code from LLM response
- [ ] Handle API errors:
  - Rate limits: implement exponential backoff
  - Timeouts: retry up to 3 times
  - Invalid API key: fail with clear error
- [ ] Log token usage for each request
- [ ] Track generation time (seconds)

**Technical Requirements**:
- Use openai Python SDK
- Implement retry with tenacity or manual backoff
- Extract code blocks from markdown responses

**Files**:
- `src/purple/agent.py`
- `src/common/llm_client.py`
- `src/purple/settings.py`

---

#### Feature 6: Code Validation

**Description**: Validate generated code syntax before returning to caller.

**Acceptance Criteria**:
- [ ] Validate generated code syntax using `ast.parse()`
- [ ] Return error if syntax invalid
- [ ] Check required imports:
  - TDD: `import pytest`
  - BDD: `from pytest_bdd`
- [ ] Verify test functions/steps exist:
  - TDD: at least one function starting with `def test_`
  - BDD: at least one `@given`, `@when`, or `@then` decorator
- [ ] Log validation failures
- [ ] Do NOT execute code (safety)

**Technical Requirements**:
- Use ast module for syntax validation
- Use regex or ast for import/function checks

**Files**:
- `src/purple/agent.py`

---

#### Feature 7: Track Switching

**Description**: Route requests to appropriate generator based on track parameter.

**Acceptance Criteria**:
- [ ] Read `track` from request payload
- [ ] Branch logic:
  - `track == "tdd"`: generate pytest (Feature 3)
  - `track == "bdd"`: generate pytest-bdd (Feature 4)
  - Otherwise: return 400 "unsupported track"
- [ ] Use different prompts per track
- [ ] Include track in response metadata
- [ ] Use simple if/else (KISS principle)

**Technical Requirements**:
- Simple conditional branching
- Track-specific prompt templates

**Files**:
- `src/purple/agent.py`

---

#### Feature 8: Response Format

**Description**: Return structured JSON response with generated tests and metadata.

**Acceptance Criteria**:
- [ ] Return JSON response:
  ```json
  {
    "tests": "<generated_test_code>",
    "metadata": {
      "generation_time": <seconds>,
      "token_count": <int>,
      "track": "tdd|bdd"
    }
  }
  ```
- [ ] tests: Multi-line string with newlines preserved
- [ ] metadata.generation_time: Elapsed time in seconds
- [ ] metadata.token_count: Tokens used in LLM call
- [ ] Set Content-Type: application/json
- [ ] Return 200 on success

**Technical Requirements**:
- Use Pydantic model for response serialization
- Preserve newlines in test code string

**Files**:
- `src/purple/models.py`
- `src/purple/agent.py`

---

#### Feature 9: Logging

**Description**: Implement structured logging for debugging and monitoring.

**Acceptance Criteria**:
- [ ] Log all incoming requests with:
  - Timestamp (ISO 8601)
  - Request ID (correlation for debugging)
  - Track (tdd or bdd)
  - Spec length (characters)
- [ ] Log responses with:
  - Success/failure status
  - Generated code length
  - Generation time
  - Token count
- [ ] Log errors with:
  - Stack trace
  - Error message
  - Request context
- [ ] Use structured JSON logging (not unstructured strings)
- [ ] Log level configurable via `LOG_LEVEL` env var

**Technical Requirements**:
- Use Python logging with JSON formatter
- Generate UUID for request IDs

**Files**:
- `src/purple/agent.py`
- `src/purple/settings.py`

---

#### Feature 10: Configuration Management

**Description**: Manage configuration via environment variables with validation.

**Acceptance Criteria**:
- [ ] Load from environment variables:
  - `OPENAI_API_KEY` (required, string)
  - `PORT` (optional, default: 9010, int)
  - `LOG_LEVEL` (optional, default: "INFO", string)
  - `LLM_MODEL` (optional, default: "gpt-4", string)
  - `TIMEOUT` (optional, default: 30, int, seconds)
- [ ] Fail fast on startup if `OPENAI_API_KEY` missing
- [ ] Validate config types on startup
- [ ] Use Pydantic for configuration
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

### Agent Class Pattern

```python
class Agent:
    required_config_keys: list[str] = ["spec", "track"]

    def __init__(self):
        self.settings = PurpleSettings()
        self.llm_client = LLMClient(self.settings.llm)

    def validate_request(self, request: GenerateRequest) -> tuple[bool, str]: ...
    async def run(self, message: Message, updater: TaskUpdater) -> None: ...
    async def generate_tests(self, spec: str, track: str) -> str: ...
```

### Executor Pattern (Standard A2A)

```python
class Executor(AgentExecutor):
    def __init__(self):
        self.agents: dict[str, Agent] = {}

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Validate message, get/create task, run agent, handle errors
        ...

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())
```

### Server Pattern

```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9010)
    parser.add_argument("--card-url", type=str)
    args = parser.parse_args()

    skill = AgentSkill(id="generate_tests", name="Test Generator", ...)
    agent_card = AgentCard(name="Purple Agent", version="1.0.0", skills=[skill], ...)

    handler = DefaultRequestHandler(agent_executor=Executor(), task_store=InMemoryTaskStore())
    server = A2AStarletteApplication(agent_card=agent_card, http_handler=handler)
    uvicorn.run(server.build(), host=args.host, port=args.port)
```

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
