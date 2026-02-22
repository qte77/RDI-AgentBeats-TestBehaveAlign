---
title: Product Requirements Document - Green Agent
version: 2.1
---

## Project Overview

The Green Agent is an automated test quality evaluator that measures how well AI coding agents generate tests. It orchestrates evaluation workflows, runs tests against correct and buggy implementations, calculates objective quality metrics, and reports results in AgentBeats format.

**Epic**: Automated Test Quality Evaluation

**Status**: Planning Phase

---

## Functional Requirements

<!-- PARSER REQUIREMENT: Use exactly "#### Feature N:" format -->

### Data Preparation (CLI Scripts - Run Once)

#### Feature 1: Task Data Download (EvalPlus)

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

**Files**:
- `src/green/data_prep/download_evalplus.py`

---

#### Feature 2: Variant Generation (Buggy/Alternative)

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
- [ ] Validate buggy code is syntactically valid (ast.parse)
- [ ] Log which bugs were injected per task

**Technical Requirements**:
- Define BUG_PATTERNS dict mapping task_id to injection rules
- Use string replacement for bug injection
- Validate buggy code differs from correct code

**Files**:
- `src/green/data_prep/generate_variants.py`

---

#### Feature 3: BDD Feature Generation (Gherkin)

**Description**: Generate BDD Gherkin feature files from TDD docstring examples.

**Acceptance Criteria**:
- [ ] Parse TDD `spec.py` docstring examples (>>> format)
- [ ] Generate Gherkin `spec.feature` files with:
  - Feature description from docstring
  - Scenarios from docstring examples
  - Given/When/Then steps for each example
- [ ] Create BDD task structure: `data/tasks/bdd/python/task_*/`
- [ ] Symlink implementation/ to TDD implementations (reuse correct.py, buggy.py)
- [ ] Generate BDD metadata.json with track="bdd" and tdd_source reference

**Technical Requirements**:
- Use regex to parse >>> docstring examples
- Generate relative symlinks for implementation reuse
- Extract function name from spec or metadata

**Files**:
- `src/green/data_prep/generate_bdd.py`

---

### Core Evaluation (A2A Runtime)

#### Feature 4: Track Switching (TDD vs BDD)

**Description**: Support both TDD and BDD evaluation modes to evaluate different testing paradigms.

**Priority**: Depends on Features 1-3 (data must exist)

**Acceptance Criteria**:
- [ ] Read track from scenario.toml config
- [ ] Load TDD tasks from data/tasks/tdd/
- [ ] Load BDD tasks from data/tasks/bdd/
- [ ] Use pytest for TDD, pytest-bdd for BDD
- [ ] Send track to Purple Agent in request
- [ ] Include track in results output
- [ ] Validate track is supported ("tdd" or "bdd")

**Technical Requirements**:
- Load configuration from `scenario.toml` using toml parser
- Single executor with mode switch (KISS principle, no inheritance)
- Simple if/else for track handling
- Fail fast if required config missing

**Files**:
- `src/green/settings.py`
- `src/green/agent.py`

---

#### Feature 5: Task Loading & Specification Parsing

**Description**: Load task specifications from the data directory to provide test generation prompts to the Purple Agent.

**Acceptance Criteria**:
- [ ] Read task directory structure (TDD or BDD track)
- [ ] Parse spec.py (TDD) containing function signature and docstring
- [ ] Parse spec.feature (BDD) containing Gherkin scenarios
- [ ] Load correct.py, buggy.py from implementation/ directory
- [ ] Validate task metadata (task_id, track, function_name)
- [ ] Handle missing files gracefully with clear errors

**Technical Requirements**:
- Track determined by scenario.toml config
- Path: `data/tasks/{track}/python/{task_id}/`
- Use pathlib for cross-platform path handling
- Parse Python AST for spec.py extraction
- Use gherkin-official or pytest-bdd parser for .feature files
- Use Pydantic models for validation

**Files**:
- `src/green/agent.py`
- `src/green/models.py`

---

#### Feature 6: A2A Protocol Implementation (Server)

**Description**: Serve A2A HTTP endpoints so that AgentBeats client can orchestrate evaluation.

**Acceptance Criteria**:
- [ ] Serve on port 9009
- [ ] GET /.well-known/agent-card.json → agent metadata
- [ ] POST /evaluate → start evaluation, return results
- [ ] Health check endpoint: GET /health
- [ ] Graceful shutdown on SIGTERM
- [ ] Log all incoming requests with request IDs

**Technical Requirements**:
- Use a2a-sdk A2AStarletteApplication
- Define AgentCard with skills and capabilities
- Implement DefaultRequestHandler with Executor
- Use uvicorn ASGI server

**Files**:
- `src/green/server.py`
- `src/green/executor.py`

---

#### Feature 7: Communication with Purple Agent (A2A Client)

**Description**: Send specifications to Purple Agent using A2A protocol to receive generated test code.

**Acceptance Criteria**:
- [ ] Discover Purple Agent via /.well-known/agent-card.json
- [ ] Send POST request to /generate-tests with spec and track
- [ ] Receive test code in response: `{tests: str}`
- [ ] Handle timeouts (30 seconds per request)
- [ ] Implement retry logic (up to 3 attempts on failure)
- [ ] Log all A2A interactions for debugging

**Technical Requirements**:
- Use a2a-sdk for communication
- Purple Agent on port 9010
- Request: `{spec: str, track: "tdd"|"bdd"}`
- Implement exponential backoff for retries
- Validate response syntax with ast.parse()

**Files**:
- `src/green/messenger.py`
- `src/green/agent.py`
- `src/common/messenger.py`

---

#### Feature 8: Test Execution Against Correct Implementation

**Description**: Run generated tests against correct.py to verify tests pass on working code.

**Acceptance Criteria**:
- [ ] Create isolated test environment (temp directory per task)
- [ ] Write test code to file
- [ ] Copy correct.py to test environment
- [ ] Execute pytest (TDD) or pytest-bdd (BDD)
- [ ] Capture exit code, stdout, stderr, execution time
- [ ] Return binary result: PASS (0) or FAIL (non-zero)
- [ ] Implement 30-second timeout per test run
- [ ] Clean up test environment (temp files)

**Technical Requirements**:
- Use subprocess with timeout for isolation
- Create temp directories with tempfile module
- Capture output streams for debugging
- No network access in test environment

**Files**:
- `src/green/agent.py`
- `src/green/models.py`

---

#### Feature 9: Test Execution Against Buggy Implementation

**Description**: Run generated tests against buggy.py to verify tests detect injected faults.

**Acceptance Criteria**:
- [ ] Same isolation as Feature 8
- [ ] Run tests against buggy.py instead of correct.py
- [ ] Expect tests to FAIL (detect injected bugs)
- [ ] Return binary result: detected bug (FAIL) or missed bug (PASS)
- [ ] Log which specific tests failed and why
- [ ] Validate test failure is due to buggy implementation (not infrastructure)

**Technical Requirements**:
- Reuse test execution infrastructure from Feature 8
- Distinguish assertion failures from import/syntax errors
- Buggy implementations have known defects

**Files**:
- `src/green/agent.py`
- `src/green/models.py`

---

#### Feature 10: Fault Detection Score Calculation

**Description**: Calculate fault detection rate for each task to measure test effectiveness.

**Acceptance Criteria**:
- [ ] Calculate per-task: `fault_detection = 1.0 if (passed_correct AND failed_buggy) else 0.0`
- [ ] Handle edge cases:
  - Tests fail on correct.py → 0.0
  - Tests pass on buggy.py → 0.0
  - Tests timeout → 0.0
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

#### Feature 11: Mutation Testing Integration

**Description**: Run mutmut mutation testing on generated tests to measure test thoroughness.

**Acceptance Criteria**:
- [ ] Configure mutmut to mutate correct.py
- [ ] Generate mutations using standard operators (arithmetic, boolean, comparison)
- [ ] Run generated tests against each mutant
- [ ] Count killed vs survived mutants
- [ ] Calculate mutation score: `killed / total`
- [ ] Timeout per mutant: 10 seconds
- [ ] Cache mutations for reproducibility
- [ ] Handle mutmut errors gracefully (skip if unavailable)

**Technical Requirements**:
- Use mutmut Python API or subprocess
- Implement timeout per mutant execution
- Handle mutmut unavailability gracefully

**Files**:
- `src/green/agent.py`
- `src/green/models.py`

---

#### Feature 12: Composite Scoring

**Description**: Calculate weighted composite score to rank test quality.

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

#### Feature 13: Results JSON Generation

**Description**: Output results in AgentBeats format so results integrate with the leaderboard.

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
- [ ] Include participant ID (Purple Agent)
- [ ] Include task-level details
- [ ] Validate JSON schema before writing
- [ ] Create output directory if missing

**Technical Requirements**:
- Use Pydantic model with model_dump_json()
- Validate against AgentBeats schema

**Files**:
- `src/green/models.py`
- `src/green/agent.py`

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
- [ ] Load OpenAI env vars: `OPENAI_API_KEY`, `OPENAI_BASE_URL`
- [ ] Support OpenAI-compatible endpoints (Azure, local models, etc.)
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
└── settings.py        # Configuration (pydantic-settings)
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

---

## Dependencies

### Python Packages (Main - Runtime)

From `pyproject.toml` main dependencies:
- `a2a-sdk[http-server]>=0.3.0` - Agent-to-agent communication
- `uvicorn>=0.30.0` - ASGI server
- `httpx>=0.27.0` - HTTP client
- `openai>=1.0.0` - LLM client (OpenAI-compatible endpoint support via OPENAI_BASE_URL)
- `pydantic-settings>=2.12.0` - Environment configuration (includes pydantic)
- `pytest>=8.0.0` - Test execution (TDD) - Green runtime requirement
- `pytest-bdd>=7.0.0` - BDD test support
- `mutmut>=3.4.0` - Mutation testing

### Python Packages (Scripts - Data Preparation)

From `[dependency-groups] scripts`:
- `evalplus>=0.2.0` - EvalPlus benchmark data download (Features 1-3)

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
- Multi-language support (MVP supports Python only)
- Custom scoring formulas (fixed formula for MVP)
- Distributed execution (single-machine evaluation only)
- Historical tracking (no persistence of past results)

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

Story Breakdown - Phase 1 (13 stories total):

**Data Preparation (CLI Scripts - Top Priority)**:
- **Feature 1 (Task Download)** → STORY-001: Download EvalPlus HumanEval tasks to data/tasks/tdd/
- **Feature 2 (Variant Generation)** → STORY-002: Generate buggy.py and alternative.py (depends: STORY-001)
- **Feature 3 (BDD Generation)** → STORY-003: Generate Gherkin spec.feature files (depends: STORY-001)

**Core Evaluation (A2A Runtime)**:
- **Feature 4 (Track Switching)** → STORY-004: Implement track configuration loading (depends: STORY-002, STORY-003)
- **Feature 5 (Task Loading)** → STORY-005: Implement task directory loading and spec parsing (depends: STORY-004)
- **Feature 6 (A2A Server)** → STORY-006: Implement A2A server with AgentCard and endpoints
- **Feature 7 (A2A Client)** → STORY-007: Implement Purple Agent communication (depends: STORY-006)
- **Feature 8 (Test Execution - Correct)** → STORY-008: Implement test execution against correct.py (depends: STORY-005, STORY-007)
- **Feature 9 (Test Execution - Buggy)** → STORY-009: Implement test execution against buggy.py (depends: STORY-008)
- **Feature 10 (Fault Detection)** → STORY-010: Implement fault detection score calculation (depends: STORY-008, STORY-009)
- **Feature 11 (Mutation Testing)** → STORY-011: Implement mutation testing integration (depends: STORY-008)
- **Feature 12 (Composite Scoring)** → STORY-012: Implement composite score calculation (depends: STORY-010, STORY-011)
- **Feature 13 (Results Output)** → STORY-013: Implement AgentBeats results.json generation (depends: STORY-012)
