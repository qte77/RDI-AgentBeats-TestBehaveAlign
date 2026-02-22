# User Story: Green Agent

## Problem Statement

AI coding agents need objective evaluation of their test generation capabilities. Manual evaluation is inconsistent, time-consuming, and doesn't scale. The benchmark ecosystem requires an automated evaluator that can measure test quality through fault detection and mutation testing, producing standardized scores for leaderboard ranking.

## Target Users

- **Benchmark Administrators**: Run evaluations and review results
- **AgentBeats Platform**: Orchestrates evaluation runs via A2A protocol
- **Competition Participants**: Receive objective scores for their AI agents

## Value Proposition

Green Agent provides automated, reproducible test quality evaluation by:
- Executing generated tests against correct and buggy implementations
- Running mutation testing to measure test thoroughness
- Computing composite scores using a standardized formula
- Outputting results in AgentBeats-compatible JSON format

## User Stories

### Epic: Automated Test Quality Evaluation

As a **benchmark administrator**, I need the Green Agent to automatically evaluate test quality so that I can objectively rank AI coding agents without manual intervention.

---

### Story 1: Load Task Specifications

**As a** Green Agent
**I want to** load task specifications from the data directory
**So that** I can provide test generation prompts to the Purple Agent

### Acceptance Criteria:
- [ ] Read task directory structure (TDD or BDD track)
- [ ] Parse spec.py (TDD) or spec.feature (BDD)
- [ ] Load correct.py, buggy.py from implementation/ directory
- [ ] Validate task metadata (task_id, track, function_name)
- [ ] Handle missing files gracefully with clear errors

### Technical Notes:
- Track determined by scenario.toml config
- Path: `data/tasks/{track}/python/{task_id}/`
- Use Pydantic models for validation

---

### Story 2: Communicate with Purple Agent via A2A

**As a** Green Agent
**I want to** send specifications to Purple Agent using A2A protocol
**So that** I can receive generated test code

### Acceptance Criteria:
- [ ] Discover Purple Agent via /.well-known/agent-card.json
- [ ] Send POST request to /generate-tests with spec and track
- [ ] Receive test code in response
- [ ] Handle timeouts and errors (retry logic)
- [ ] Log all A2A interactions for debugging

### Technical Notes:
- Use a2a-sdk for communication
- Purple Agent on port 9010
- Request: `{spec: str, track: "tdd"|"bdd"}`
- Response: `{tests: str}`

---

### Story 3: Execute Tests Against Correct Implementation

**As a** Green Agent
**I want to** run generated tests against correct.py
**So that** I can verify tests pass on working code

### Acceptance Criteria:
- [ ] Create isolated test environment (temp directory)
- [ ] Write test code to file
- [ ] Copy correct.py to test environment
- [ ] Execute pytest (TDD) or pytest-bdd (BDD)
- [ ] Capture exit code and output
- [ ] Return binary result: PASS or FAIL
- [ ] Clean up test environment

### Technical Notes:
- Use subprocess to run pytest
- Timeout: 30 seconds per test run
- Collect coverage data (optional)

---

### Story 4: Execute Tests Against Buggy Implementation

**As a** Green Agent
**I want to** run generated tests against buggy.py
**So that** I can verify tests detect injected faults

### Acceptance Criteria:
- [ ] Same isolation as Story 3
- [ ] Run tests against buggy.py instead of correct.py
- [ ] Expect tests to FAIL
- [ ] Return binary result: detected bug (FAIL) or missed bug (PASS)
- [ ] Log which specific tests failed

### Technical Notes:
- Reuse executor logic from Story 3
- Buggy implementations have known defects

---

### Story 5: Calculate Fault Detection Rate

**As a** Green Agent
**I want to** calculate fault detection rate for each task
**So that** I can measure test effectiveness

### Acceptance Criteria:
- [ ] Compute: `(passed_correct AND failed_buggy) ? 1.0 : 0.0`
- [ ] Handle edge cases:
  - Tests fail on correct.py → score 0.0
  - Tests pass on buggy.py → score 0.0
  - Tests time out → score 0.0
- [ ] Aggregate across all tasks
- [ ] Include per-task breakdown in results

### Formula:
```python
fault_detection_rate = 1.0 if (passed_correct and failed_buggy) else 0.0
```

---

### Story 6: Run Mutation Testing

**As a** Green Agent
**I want to** run mutmut mutation testing on generated tests
**So that** I can measure test thoroughness

### Acceptance Criteria:
- [ ] Configure mutmut to mutate correct.py
- [ ] Run generated tests against each mutant
- [ ] Count killed vs survived mutants
- [ ] Calculate mutation score: `killed / total`
- [ ] Timeout per mutant: 10 seconds
- [ ] Handle mutmut errors gracefully

### Technical Notes:
- Use mutmut CLI via subprocess
- Mutation operators: arithmetic, boolean, comparison
- Cache mutants for reproducibility

---

### Story 7: Compute Composite Score

**As a** Green Agent
**I want to** calculate weighted composite score
**So that** I can rank test quality

### Acceptance Criteria:
- [ ] MVP formula: `0.60 × mutation + 0.40 × fault_detection`
- [ ] Validate inputs (0.0 to 1.0 range)
- [ ] Round to 2 decimal places
- [ ] Include component scores in output
- [ ] Handle missing metrics (default to 0.0)

### Formula:
```python
score = (0.60 * mutation_score) + (0.40 * fault_detection_rate)
```

---

### Story 8: Generate Results JSON

**As a** Green Agent
**I want to** output results in AgentBeats format
**So that** results integrate with the leaderboard

### Acceptance Criteria:
- [ ] Follow AgentBeats results schema
- [ ] Include participant ID (Purple Agent)
- [ ] Include task-level details
- [ ] Include aggregate scores
- [ ] Write to `output/results.json`
- [ ] Validate JSON schema

### Schema:
```json
{
  "participants": {"agent": "purple-agent-id"},
  "results": [{
    "score": 0.75,
    "task_rewards": {
      "mutation_score": 0.80,
      "fault_detection_rate": 0.65,
      "track": "tdd"
    },
    "detail": {
      "task_details": [...]
    }
  }]
}
```

---

### Story 9: Serve A2A Endpoints

**As a** Green Agent
**I want to** serve A2A HTTP endpoints
**So that** AgentBeats client can orchestrate evaluation

### Acceptance Criteria:
- [ ] Serve on port 9009
- [ ] GET /.well-known/agent-card.json → agent metadata
- [ ] POST /evaluate → start evaluation, return results
- [ ] Health check endpoint: GET /health
- [ ] Graceful shutdown on SIGTERM
- [ ] Log all incoming requests

### Endpoints:
- `GET /.well-known/agent-card.json` → `{name, version, capabilities}`
- `POST /evaluate` → `{results: {...}}`
- `GET /health` → `{status: "ok"}`

---

### Story 10: Handle Track Switching (TDD vs BDD)

**As a** Green Agent
**I want to** support both TDD and BDD evaluation modes
**So that** I can evaluate different testing paradigms

### Acceptance Criteria:
- [ ] Read track from scenario.toml config
- [ ] Load TDD tasks from data/tasks/tdd/
- [ ] Load BDD tasks from data/tasks/bdd/
- [ ] Use pytest for TDD, pytest-bdd for BDD
- [ ] Send track to Purple Agent in request
- [ ] Include track in results output

### Technical Notes:
- Single executor with mode switch
- No class hierarchy (KISS principle)
- Simple if/else for track handling

---

## Success Criteria

- [ ] Green Agent successfully loads task specifications from both TDD and BDD tracks
- [ ] A2A communication with Purple Agent completes without manual intervention
- [ ] Tests execute correctly against both correct.py and buggy.py implementations
- [ ] Fault detection rate accurately reflects test quality (1.0 when tests pass correct and fail buggy)
- [ ] Mutation testing produces valid mutation scores using mutmut
- [ ] Composite scores match formula: `0.60 × mutation + 0.40 × fault_detection`
- [ ] Results JSON validates against AgentBeats schema
- [ ] Full evaluation of 5 tasks completes in under 5 minutes

## Constraints

### Performance
- Evaluate 5 tasks in under 5 minutes
- Parallel test execution where possible

### Reliability
- Handle Purple Agent failures (timeouts, errors)
- Retry A2A requests up to 3 times
- Validate all inputs with Pydantic

### Observability
- Structured logging (JSON format)
- Log level configurable via env var
- Include timing metrics in output

### Security
- Isolate test execution (no network access)
- Sanitize test code (no file system writes outside /tmp)
- Validate all Purple Agent responses

## Out of Scope

- **Test generation**: Green Agent evaluates tests, does not generate them (Purple Agent's responsibility)
- **LLM integration**: No direct LLM calls; receives pre-generated tests from Purple Agent
- **Multi-language support**: MVP supports Python only
- **Custom scoring formulas**: Fixed formula for MVP; configurability deferred
- **Distributed execution**: Single-machine evaluation only
- **Historical tracking**: No persistence of past evaluation results
- **Agent ranking UI**: Outputs JSON only; leaderboard display handled by AgentBeats platform
