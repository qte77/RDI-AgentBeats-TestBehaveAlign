---
title: Product Requirements Document - Green Agent
version: 1.0
---

## Project Overview

The Green Agent is an automated test quality evaluator that measures how well AI coding agents generate tests. It orchestrates evaluation workflows, runs tests against correct and buggy implementations, calculates objective quality metrics, and reports results in AgentBeats format.

**Epic**: Automated Test Quality Evaluation

**Status**: Planning Phase

---

## Functional Requirements

<!-- PARSER REQUIREMENT: Use exactly "#### Feature N:" format -->

#### Feature 1: Track Switching (TDD vs BDD)

**Description**: Determine execution track (TDD or BDD) early in the workflow to configure all downstream operations.

**Acceptance Criteria**:
- [ ] Read `track` from scenario.toml config
- [ ] Branch execution based on track:
  - TDD: use pytest, load spec.py, parse docstrings
  - BDD: use pytest-bdd, load spec.feature, parse Gherkin
- [ ] Send track to Purple Agent in requests
- [ ] Include track in results output
- [ ] Use simple if/else logic (KISS principle, no inheritance)
- [ ] Validate track is supported ("tdd" or "bdd")

**Technical Requirements**:
- Load configuration from `scenario.toml` using toml parser
- Validate track value on startup (fail fast)
- Pass track context through all evaluation stages

**Files**:
- `src/green/settings.py`
- `src/green/agent.py`

---

#### Feature 2: Task Loading & Specification Parsing

**Description**: Load task directories and parse specification files for both TDD and BDD tracks.

**Acceptance Criteria**:
- [ ] Load task directory from `data/tasks/{track}/python/{task_id}/`
- [ ] Parse `spec.py` (TDD) containing function signature and docstring
- [ ] Parse `spec.feature` (BDD) containing Gherkin scenarios
- [ ] Load implementation files: `correct.py`, `buggy.py`, `alternative.py`
- [ ] Validate task metadata: task_id, track, function_name
- [ ] Provide clear error messages for missing files
- [ ] Support both TDD and BDD track selection via config

**Technical Requirements**:
- Use pathlib for cross-platform path handling
- Parse Python AST for spec.py extraction
- Use gherkin-official or pytest-bdd parser for .feature files

**Files**:
- `src/green/agent.py`
- `src/green/models.py`

---

#### Feature 3: A2A Protocol Implementation (Server)

**Description**: Implement A2A-compliant HTTP server for receiving evaluation requests.

**Acceptance Criteria**:
- [ ] Serve HTTP on port 9009
- [ ] Implement `GET /.well-known/agent-card.json` endpoint
  - Return: `{name, version, capabilities, supported_tracks}`
- [ ] Implement `POST /evaluate` endpoint
  - Accept: empty request (config from scenario.toml)
  - Return: `{results: {...}}` in AgentBeats format
- [ ] Implement `GET /health` health check endpoint
- [ ] Log all incoming requests with request IDs
- [ ] Graceful shutdown on SIGTERM
- [ ] Use uvicorn ASGI server

**Technical Requirements**:
- Use a2a-sdk A2AStarletteApplication
- Define AgentCard with skills and capabilities
- Implement DefaultRequestHandler with Executor

**Files**:
- `src/green/server.py`
- `src/green/executor.py`

---

#### Feature 4: Communication with Purple Agent (A2A Client)

**Description**: Communicate with Purple Agent to request test generation via A2A protocol.

**Acceptance Criteria**:
- [ ] Discover Purple Agent via `GET /.well-known/agent-card.json`
- [ ] Send `POST /generate-tests` requests with:
  - `spec`: function/feature specification as string
  - `track`: "tdd" or "bdd"
- [ ] Receive test code in response: `{tests: str}`
- [ ] Implement retry logic (up to 3 attempts on failure)
- [ ] Handle timeouts (30 seconds per request)
- [ ] Parse and validate Purple Agent responses
- [ ] Log all A2A interactions for debugging

**Technical Requirements**:
- Use Messenger class from common module
- Implement exponential backoff for retries
- Validate response syntax with ast.parse()

**Files**:
- `src/green/messenger.py`
- `src/green/agent.py`
- `src/common/messenger.py`

---

#### Feature 5: Test Execution Against Correct Implementation

**Description**: Execute generated tests against correct implementation to verify test validity.

**Acceptance Criteria**:
- [ ] Create isolated test environment (temp directory per task)
- [ ] Write generated test code to file
- [ ] Copy `correct.py` to test environment
- [ ] Execute tests using:
  - TDD: `pytest` with standard plugins
  - BDD: `pytest-bdd` with Gherkin feature support
- [ ] Capture: exit code, stdout, stderr, execution time
- [ ] Return binary result: PASS (0) or FAIL (non-zero)
- [ ] Implement 30-second timeout per test run
- [ ] Clean up test environment (temp files)
- [ ] Log test execution details

**Technical Requirements**:
- Use subprocess with timeout for isolation
- Create temp directories with tempfile module
- Capture output streams for debugging

**Files**:
- `src/green/agent.py`
- `src/green/models.py`

---

#### Feature 6: Test Execution Against Buggy Implementation

**Description**: Execute generated tests against buggy implementation to measure fault detection capability.

**Acceptance Criteria**:
- [ ] Same isolation and execution as Feature 5
- [ ] Run tests against `buggy.py` instead of `correct.py`
- [ ] Expect tests to FAIL (detect injected bugs)
- [ ] Return binary result: bug detected (FAIL) or missed (PASS)
- [ ] Log which test functions failed and why
- [ ] Validate test failure is due to buggy implementation (not infrastructure)

**Technical Requirements**:
- Reuse test execution infrastructure from Feature 5
- Distinguish assertion failures from import/syntax errors

**Files**:
- `src/green/agent.py`
- `src/green/models.py`

---

#### Feature 7: Fault Detection Score Calculation

**Description**: Calculate fault detection score based on test results against correct and buggy implementations.

**Acceptance Criteria**:
- [ ] Calculate per-task: `fault_detection = 1.0 if (passed_correct AND failed_buggy) else 0.0`
- [ ] Handle edge cases:
  - Tests timeout → 0.0
  - Tests fail on correct.py → 0.0
  - Tests pass on buggy.py → 0.0
- [ ] Aggregate across all tasks: `avg_fault_detection`
- [ ] Include per-task breakdown in output
- [ ] Validate scores in range [0.0, 1.0]

**Technical Requirements**:
- Use Pydantic models for score validation
- Aggregate with simple averaging

**Files**:
- `src/green/agent.py`
- `src/green/models.py`

---

#### Feature 8: Mutation Testing Integration

**Description**: Run mutation testing to measure test thoroughness beyond fault detection.

**Acceptance Criteria**:
- [ ] Configure mutmut to mutate `correct.py`
- [ ] Generate mutations using standard operators (arithmetic, boolean, comparison)
- [ ] Run generated tests against each mutant
- [ ] Count: killed mutants vs survived mutants
- [ ] Calculate: `mutation_score = killed / total`
- [ ] Timeout per mutant: 10 seconds
- [ ] Cache mutations for reproducibility
- [ ] Handle mutmut errors gracefully (skip if unavailable)
- [ ] Log mutation testing summary

**Technical Requirements**:
- Use mutmut Python API or subprocess
- Implement timeout per mutant execution
- Handle mutmut unavailability gracefully

**Files**:
- `src/green/agent.py`
- `src/green/models.py`

---

#### Feature 9: Composite Scoring

**Description**: Calculate final composite score from fault detection and mutation testing metrics.

**Acceptance Criteria**:
- [ ] MVP formula: `score = (0.60 × mutation_score) + (0.40 × fault_detection_rate)`
- [ ] Validate component scores in [0.0, 1.0]
- [ ] Round final score to 2 decimal places
- [ ] Include all component scores in output
- [ ] Handle missing metrics (default to 0.0)

**Technical Requirements**:
- Configurable weights (future enhancement)
- Pydantic validation for score bounds

**Files**:
- `src/green/agent.py`
- `src/green/models.py`

---

#### Feature 10: Results JSON Generation

**Description**: Generate AgentBeats-compliant results.json output file.

**Acceptance Criteria**:
- [ ] Output to `output/results.json`
- [ ] Follow AgentBeats schema:
  ```json
  {
    "participants": {"agent": "purple-agent-uuid"},
    "results": [{
      "score": 0.75,
      "pass_rate": 0.65,
      "task_rewards": {
        "mutation_score": 0.55,
        "fault_detection_rate": 0.80,
        "track": "tdd",
        "task_count": 5
      },
      "detail": {
        "task_details": [...]
      }
    }]
  }
  ```
- [ ] Include all task-level metrics
- [ ] Validate JSON schema before writing
- [ ] Create output directory if missing

**Technical Requirements**:
- Use Pydantic model with model_dump_json()
- Validate against AgentBeats schema

**Files**:
- `src/green/models.py`
- `src/green/agent.py`

---

#### Feature 11: Task Data Download (EvalPlus)

**Description**: Download benchmark tasks from EvalPlus HumanEval dataset for evaluation.

**Acceptance Criteria**:
- [ ] Download HumanEval tasks 0-4 from EvalPlus benchmark
- [ ] Extract function specs (signature + docstring) to `spec.py`
- [ ] Extract canonical solutions to `implementation/correct.py`
- [ ] Generate `metadata.json` with task_id, function_name, track, source
- [ ] Structure output as `data/tasks/tdd/python/task_{001..005}/`
- [ ] Handle evalplus import errors gracefully
- [ ] Log download progress and success

**Technical Requirements**:
- Use `evalplus.data.get_human_eval_plus()` API
- Map HumanEval IDs to task names (e.g., 0 → task_001_has_close_elements)
- Create directory structure with pathlib

**Test Requirements** (TDD - write tests first):
- [ ] Test task mapping (HumanEval ID → task name)
- [ ] Test directory structure creation
- [ ] Test spec.py content extraction
- [ ] Test metadata.json generation
- [ ] Test error handling when evalplus unavailable

**Files**:
- `src/green/data_prep.py`
- `src/green/models.py`
- `tests/green/test_data_prep.py`

---

#### Feature 12: Variant Generation (Buggy/Alternative)

**Description**: Generate buggy and alternative implementations from correct solutions for fault detection testing.

**Acceptance Criteria**:
- [ ] Read `correct.py` from each task directory
- [ ] Generate `buggy.py` with injected known defects:
  - Off-by-one errors (< vs <=)
  - Logic errors (incorrect conditions)
  - Arithmetic errors (// vs /)
  - Missing checks
- [ ] Generate `alternative.py` (alternative correct implementation)
- [ ] Use task-specific bug patterns when available
- [ ] Fall back to generic bug injection if no pattern defined
- [ ] Log which bugs were injected per task

**Technical Requirements**:
- Define BUG_PATTERNS dict mapping task_id to injection rules
- Use string replacement for bug injection
- Validate buggy code is syntactically valid

**Test Requirements** (TDD - write tests first):
- [ ] Test bug pattern application for each task type
- [ ] Test fallback generic bug injection
- [ ] Test buggy code is syntactically valid (ast.parse)
- [ ] Test buggy code differs from correct code
- [ ] Test alternative.py generation

**Files**:
- `src/green/data_prep.py`
- `src/green/models.py`
- `tests/green/test_data_prep.py`

---

#### Feature 13: BDD Feature Generation (Gherkin)

**Description**: Generate BDD Gherkin feature files from TDD docstring examples.

**Acceptance Criteria**:
- [ ] Parse TDD `spec.py` docstring examples (>>> format)
- [ ] Generate Gherkin `spec.feature` files with:
  - Feature description from docstring
  - Scenarios from docstring examples
  - Given/When/Then steps for each example
  - Edge case scenario template
- [ ] Create BDD task structure: `data/tasks/bdd/python/task_*/`
- [ ] Symlink implementation/ to TDD implementations (reuse correct.py, buggy.py)
- [ ] Generate BDD metadata.json with track="bdd" and tdd_source reference

**Technical Requirements**:
- Use regex to parse >>> docstring examples
- Generate relative symlinks for implementation reuse
- Extract function name from spec or metadata

**Test Requirements** (TDD - write tests first):
- [ ] Test docstring example parsing (>>> format)
- [ ] Test Gherkin feature file generation
- [ ] Test Given/When/Then step formatting
- [ ] Test symlink creation
- [ ] Test BDD metadata.json generation

**Files**:
- `src/green/data_prep.py`
- `src/green/models.py`
- `tests/green/test_data_prep.py`

---

#### Feature 14: Results Validation

**Description**: Validate results.json against AgentBeats schema before submission.

**Acceptance Criteria**:
- [ ] Validate JSON syntax (parseable)
- [ ] Check required top-level keys: `participants`, `results`
- [ ] Validate `participants.agent` is non-empty
- [ ] Validate `results` is non-empty list
- [ ] For each result item, validate:
  - Required fields: `score`, `task_rewards`
  - `score` in range [0, 100]
  - `task_rewards.mutation_score` in range [0, 1]
  - `task_rewards.fault_detection_rate` in range [0, 1]
  - `task_rewards.track` is "tdd" or "bdd"
- [ ] Return detailed error messages for each violation
- [ ] Exit code 0 if valid, 1 if invalid

**Technical Requirements**:
- Use Pydantic for schema validation
- Provide CLI interface for standalone validation
- Support custom file path argument

**Test Requirements** (TDD - write tests first):
- [ ] Test valid results.json passes validation
- [ ] Test missing participants key fails
- [ ] Test missing results key fails
- [ ] Test score out of range [0, 100] fails
- [ ] Test mutation_score out of range [0, 1] fails
- [ ] Test invalid track value fails
- [ ] Test detailed error messages returned

**Files**:
- `src/green/models.py`
- `tests/green/test_models.py`

---

## Non-Functional Requirements

### Performance
- [ ] Evaluate 5 tasks in < 5 minutes total
- [ ] Per-task evaluation: < 60 seconds
- [ ] A2A request to Purple Agent: < 30 seconds
- [ ] Mutation testing per task: < 2 minutes

### Reliability
- [ ] Retry A2A requests on failure (up to 3 times)
- [ ] Handle Purple Agent timeouts gracefully
- [ ] Validate all Purple Agent responses
- [ ] Isolate test execution (no interference between tasks)
- [ ] Clean up resources (temp directories, file handles)

### Observability
- [ ] Structured JSON logging
- [ ] Log levels: DEBUG, INFO, WARNING, ERROR
- [ ] Log level configurable via `LOG_LEVEL` env var
- [ ] Include timing metrics in output (execution_time per task)
- [ ] Request IDs for tracing A2A interactions

### Security
- [ ] Isolate test execution (subprocess, temp directories)
- [ ] No network access in test environment
- [ ] Sanitize test code (validate imports, no file system writes outside /tmp)
- [ ] Validate Purple Agent responses (syntax check with ast.parse)
- [ ] No arbitrary code execution in evaluation context

### Configuration
- [ ] Load config from `scenario.toml`
- [ ] Load env vars: `LOG_LEVEL`, `PORT`, `TIMEOUT`
- [ ] Fail fast if required config missing
- [ ] Validate config on startup

---

## Module Structure (A2A-Compliant)

The Green Agent follows the A2A SDK standard module structure:

```
src/green/
├── __init__.py        # Package init, exports __version__
├── agent.py           # Core business logic (Agent class)
├── executor.py        # A2A execution wrapper (AgentExecutor)
├── server.py          # HTTP server setup (uvicorn, AgentCard)
├── messenger.py       # A2A client (imports from common)
├── models.py          # Domain models (EvalRequest, ScoreResult, etc.)
├── settings.py        # Configuration (pydantic-settings)
└── data_prep.py       # Task data preparation (download, variants, BDD generation)
```

### Module Responsibilities

| Module | Responsibility | Key Classes/Functions |
|--------|---------------|----------------------|
| `agent.py` | Core evaluation logic | `Agent` class with `run(message, updater)` |
| `executor.py` | A2A task lifecycle | `Executor(AgentExecutor)` - manages Agent per context |
| `server.py` | HTTP server setup | `main()` - argparse, AgentCard, AgentSkill, uvicorn |
| `messenger.py` | A2A client communication | Re-exports from `common.messenger` |
| `models.py` | Domain Pydantic models | `EvalRequest`, `TaskResult`, `ScoreResult`, `AgentBeatsOutput` |
| `settings.py` | Environment configuration | `GreenSettings(BaseSettings)` with env prefix |
| `data_prep.py` | Task data preparation | `download_tasks()`, `create_variants()`, `generate_bdd()` |

### Agent Class Pattern

```python
class Agent:
    required_roles: list[str] = ["purple_agent"]
    required_config_keys: list[str] = ["track", "task_ids"]

    def __init__(self):
        self.messenger = Messenger()
        self.settings = GreenSettings()

    def validate_request(self, request: EvalRequest) -> tuple[bool, str]: ...
    async def run(self, message: Message, updater: TaskUpdater) -> None: ...
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
    parser.add_argument("--port", type=int, default=9009)
    parser.add_argument("--card-url", type=str)
    args = parser.parse_args()

    skill = AgentSkill(id="evaluate_tests", name="Test Quality Evaluator", ...)
    agent_card = AgentCard(name="Green Agent", version="1.0.0", skills=[skill], ...)

    handler = DefaultRequestHandler(agent_executor=Executor(), task_store=InMemoryTaskStore())
    server = A2AStarletteApplication(agent_card=agent_card, http_handler=handler)
    uvicorn.run(server.build(), host=args.host, port=args.port)
```

### Common Module Structure

Shared utilities used by both Green and Purple agents:

```
src/common/
├── __init__.py        # Package init
├── models.py          # Shared models (JSONRPCRequest/Response, InteractionStep)
├── settings.py        # Shared settings (LLMSettings)
├── messenger.py       # A2A client utilities (create_message, send_message, Messenger)
└── llm_client.py      # LLM client wrapper (optional, for shared LLM access)
```

---

## Dependencies

### Python Packages (Main - Runtime)

From `pyproject.toml` main dependencies:
- `a2a-sdk[http-server]>=0.3.0` - Agent-to-agent communication
- `uvicorn>=0.30.0` - ASGI server
- `httpx>=0.27.0` - HTTP client
- `openai>=1.0.0` - LLM client (shared with Purple)
- `pydantic-settings>=2.12.0` - Environment configuration (includes pydantic)
- `pytest>=8.0.0` - Test execution (TDD) - Green runtime requirement
- `pytest-bdd>=7.0.0` - BDD test support
- `mutmut>=3.4.0` - Mutation testing

### Python Packages (Scripts - Data Preparation)

From `[dependency-groups] scripts`:
- `evalplus>=0.2.0` - Benchmark data download (Feature 11)

Install with: `uv sync --group scripts`

### Python Packages (Dev - Testing/Linting)

From `[dependency-groups] dev`:
- `pytest-asyncio>=0.24.0` - Async test support
- `pytest-cov>=7.0.0` - Coverage reporting
- `ruff>=0.8.0` - Linting
- `pyright>=1.1.0` - Type checking

Install with: `uv sync --group dev`

### External Services

- None (evaluation is self-contained)

---

## Out of Scope

- Implementation of Purple Agent
- LLM calls (Purple Agent responsibility)
- LeaderBoard UI (AgentBeats responsibility)
- Custom test assertions beyond pytest

---

## Success Metrics

| Metric | Target | Rationale |
|--------|--------|-----------|
| Task Loading | 100% success | All 5 tasks load without errors |
| A2A Communication | 100% success | All requests to Purple Agent succeed or retry gracefully |
| Test Isolation | 100% isolation | Temp directories cleaned after each task |
| Results Generation | Valid JSON | output/results.json conforms to AgentBeats schema |
| Score Calculation | Deterministic | Same tests → same scores on re-run |
| Performance | < 5 min for 5 tasks | Fits within competition timeframe |

---

## Notes for Ralph Loop

<!-- PARSER REQUIREMENT: Include story count in parentheses -->
<!-- PARSER REQUIREMENT: Use (depends: STORY-XXX, STORY-YYY) for dependencies -->

Story Breakdown - Phase 1 (14 stories total):

**Data Preparation (CLI - run once before evaluation)**:
- **Feature 11 (Task Download)** → STORY-001: Implement EvalPlus task download
- **Feature 12 (Variant Generation)** → STORY-002: Implement buggy/alternative generation (depends: STORY-001)
- **Feature 13 (BDD Generation)** → STORY-003: Implement Gherkin feature file generation (depends: STORY-001)

**Core Evaluation (A2A Runtime)**:
- **Feature 1 (Track Switching)** → STORY-004: Implement track configuration loading
- **Feature 2 (Task Loading)** → STORY-005: Implement task directory loading and spec parsing (depends: STORY-004)
- **Feature 3 (A2A Server)** → STORY-006: Implement A2A server with AgentCard and endpoints
- **Feature 4 (A2A Client)** → STORY-007: Implement Purple Agent communication (depends: STORY-006)
- **Feature 5 (Test Execution - Correct)** → STORY-008: Implement test execution against correct.py (depends: STORY-005, STORY-007)
- **Feature 6 (Test Execution - Buggy)** → STORY-009: Implement test execution against buggy.py (depends: STORY-008)
- **Feature 7 (Fault Detection)** → STORY-010: Implement fault detection score calculation (depends: STORY-008, STORY-009)
- **Feature 8 (Mutation Testing)** → STORY-011: Implement mutation testing integration (depends: STORY-008)
- **Feature 9 (Composite Scoring)** → STORY-012: Implement composite score calculation (depends: STORY-010, STORY-011)
- **Feature 10 (Results Output)** → STORY-013: Implement AgentBeats results.json generation (depends: STORY-012)
- **Feature 14 (Results Validation)** → STORY-014: Implement results.json schema validation (depends: STORY-013)
