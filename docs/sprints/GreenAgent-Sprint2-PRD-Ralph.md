---
title: Product Requirements Document - Green Agent Sprint 2
version: 2.0
---

## Project Overview

Sprint 2 addresses gaps identified during AC verification of Sprint 1 (13 stories, 184 tests passing) and aligns architecture with the reference implementation (`qte77/RDI-AgentBeats-MAS-GraphJudge` `feat-tracing-cfg` branch).

Cross-referencing AC bullets against code revealed 4 missing implementations, 6 partial implementations, and 10 test gaps. Cross-repo comparison identified architectural divergences from the authoritative reference: raw httpx vs a2a-sdk for messaging, missing shared common package, no task lifecycle tracking.

**Epic**: Green Agent AC Compliance, Hardening & SDK Alignment

**Status**: Planning Phase

**Predecessor**: GreenAgent-Sprint1-PRD-Ralph.md (13 stories, all passing)

**Reference**: `qte77/RDI-AgentBeats-MAS-GraphJudge` `feat-tracing-cfg` (authoritative)

---

## Functional Requirements

<!-- PARSER REQUIREMENT: Use exactly "#### Feature N:" format -->

### P0: SDK Alignment (Reference Repo Divergences)

#### Feature 14: Migrate Messenger to a2a-sdk ClientFactory

**Description**: Replace raw httpx messenger with a2a-sdk `ClientFactory.connect()` pattern, aligning with the reference implementation (`common/messenger.py` in MAS-GraphJudge). This gives implicit AgentCard discovery, client caching per URL, and proper TaskState lifecycle tracking.

**Acceptance Criteria**:
- [ ] Replace `httpx.AsyncClient` with `ClientFactory.connect(url)` from a2a-sdk
- [ ] Use `create_text_message_object()` for message construction
- [ ] Iterate `send_message()` events and check `TaskState.completed`
- [ ] Implement client caching per agent URL (avoid reconnect per request)
- [ ] Implement `close()` method to clean up cached clients
- [ ] Remove explicit `discover_agent_card()` method (SDK handles discovery internally)
- [ ] Preserve retry logic with exponential backoff
- [ ] Preserve response validation with `ast.parse()`
- [ ] Preserve 30-second timeout configuration

**Technical Requirements**:
- Import `Client`, `ClientConfig`, `ClientFactory`, `create_text_message_object` from `a2a.client`
- Import `TaskState` from `a2a.types`
- Use `httpx.AsyncClient` only for transport config passed to `ClientConfig` (not for protocol)
- Reference: `MAS-GraphJudge/src/common/messenger.py:62-77`

**Files**:
- `src/green/messenger.py`

**Traces to**: Sprint 1 STORY-007 AC "Use a2a-sdk for communication" (Flag F4), cross-repo comparison

---

#### Feature 15: Executor Implementation with Trace Tracking

**Description**: Implement the executor's `execute()` method (currently an empty `pass`), aligned with the reference implementation which uses UUID trace IDs, multi-round coordination, and latency measurement.

**Acceptance Criteria**:
- [ ] `execute()` receives A2A message and delegates to agent evaluation
- [ ] Generate `trace_id` via `uuid.uuid4()` per evaluation
- [ ] Parse incoming message to extract evaluation parameters
- [ ] Call agent's evaluation pipeline (load task, request tests, execute, score)
- [ ] Record start/end time and compute latency per operation
- [ ] Return results as A2A response artifact
- [ ] Handle errors and return appropriate A2A error responses
- [ ] Call `await messenger.close()` in finally block

**Technical Requirements**:
- Use existing `GreenAgent` methods for the evaluation pipeline
- Follow a2a-sdk `AgentExecutor` interface
- Reference: `MAS-GraphJudge/src/green/executor.py:38-104`

**Files**:
- `src/green/executor.py`
- `src/green/agent.py`

**Traces to**: Sprint 1 STORY-006 AC "POST /evaluate → start evaluation, return results" (Flag F7)

---

### P1: Implementation Gaps

#### Feature 16: Request ID Logging Middleware

**Description**: Add ASGI middleware to log all incoming HTTP requests with unique request IDs for observability.

**Acceptance Criteria**:
- [ ] Generate UUID request ID for each incoming HTTP request
- [ ] Add middleware to FastAPI/ASGI application in server.py
- [ ] Log method, path, status code, and duration per request
- [ ] Include request ID in all log entries for that request
- [ ] Return request ID in response header (`X-Request-ID`)

**Technical Requirements**:
- Implement as Starlette/FastAPI middleware
- Use `uuid4()` for request ID generation
- Use structured logging (existing logger)

**Files**:
- `src/green/server.py`

**Traces to**: Sprint 1 STORY-006 AC "Log all incoming requests with request IDs" (Flag F3)

---

#### Feature 17: BDD Track Dispatch in Test Execution

**Description**: Implement actual pytest-bdd dispatch when `track="bdd"` so BDD evaluation uses BDD-specific test execution.

**Acceptance Criteria**:
- [ ] When `track="tdd"`, invoke `pytest` (current behavior)
- [ ] When `track="bdd"`, invoke `pytest` with `pytest-bdd` plugin loaded
- [ ] Remove FIXME comments from `agent.py:230` and `agent.py:250`
- [ ] BDD test execution writes step definition files alongside test file
- [ ] Both tracks capture same result structure (exit code, stdout, stderr, time)

**Technical Requirements**:
- Modify `_execute_test_in_isolation()` to accept and use `track` parameter
- BDD execution should write a conftest.py with step definitions if needed
- Reuse existing subprocess/timeout infrastructure

**Files**:
- `src/green/agent.py`

**Traces to**: Sprint 1 STORY-004 AC "Use pytest for TDD, pytest-bdd for BDD" (Flag F5)

---

### P2: AC Text Alignment

#### Feature 18: Align AC Text with Implementation Decisions

**Description**: Update Sprint 1 PRD acceptance criteria to reflect intentional implementation decisions confirmed by cross-repo analysis. GraphJudge also does not implement AST parsing for spec loading or gherkin parsers — confirming these are not expected patterns.

**Acceptance Criteria**:
- [ ] STORY-005: Change "Parse Python AST for spec.py extraction" to "Load spec.py content via read_text()" (AST used in data_prep, not loading; GraphJudge has no spec.py concept)
- [ ] STORY-005: Change "Use gherkin-official or pytest-bdd parser for .feature files" to "Load spec.feature content via read_text()" (GraphJudge has no .feature files either)
- [ ] STORY-006: Change "Use a2a-sdk A2AStarletteApplication" to "Use a2a-sdk A2ARESTFastAPIApplication" (SDK class renamed)
- [ ] Update prd.json to reflect AC text changes

**Technical Requirements**:
- Edit `docs/sprints/GreenAgent-Sprint1-PRD-Ralph.md`
- Edit `ralph/docs/prd.json`
- No code changes

**Files**:
- `docs/sprints/GreenAgent-Sprint1-PRD-Ralph.md`
- `ralph/docs/prd.json`

**Traces to**: Flags F1, F2, F6

---

### P3: Test Hardening

#### Feature 19: Data Prep Test Coverage

**Description**: Add missing test coverage for data preparation edge cases and error paths.

**Acceptance Criteria**:
- [ ] Test evalplus ImportError handling (`download_evalplus.py:22-27`)
- [ ] Test log message content (not just record count) for download progress
- [ ] Test BUG_PATTERNS coverage for tasks 002-005 (not just task_001)
- [ ] Test ValueError path when buggy code equals correct code (`generate_variants.py:87-91`)

**Technical Requirements**:
- Use `unittest.mock` to simulate ImportError for evalplus
- Use `caplog` with message content assertions
- Parametrize BUG_PATTERNS tests across all 5 tasks

**Files**:
- `tests/test_download_evalplus.py`
- `tests/test_generate_variants.py`

**Traces to**: Flags T1, T2, T5, T6

---

#### Feature 20: Server & Execution Test Coverage

**Description**: Add missing test coverage for server infrastructure and test execution isolation.

**Acceptance Criteria**:
- [ ] Test that uvicorn is configured as the ASGI server
- [ ] Test network isolation guard (socket patching in conftest.py blocks network calls)
- [ ] Test temp directory cleanup (verify directory is deleted after execution)
- [ ] Test per-mutant timeout configuration is written correctly to pyproject.toml

**Technical Requirements**:
- Mock subprocess to verify network-blocking conftest is written
- Use `tmp_path` and verify directory absence after context manager exits
- Parse written pyproject.toml to verify timeout value

**Files**:
- `tests/test_server.py`
- `tests/test_test_execution.py`
- `tests/test_mutation_testing.py`

**Traces to**: Flags T7, T8, T10

---

## Non-Functional Requirements

### SDK Alignment
- [ ] Messenger uses a2a-sdk types exclusively for protocol (httpx only for transport config)
- [ ] Executor follows a2a-sdk AgentExecutor interface
- [ ] Client lifecycle managed (close() called in finally blocks)

### Test Quality
- [ ] All new tests follow existing pytest patterns
- [ ] No test relies on external services or network
- [ ] All tests complete in < 5 seconds individually (except timeout tests)

### Documentation
- [ ] AC text changes documented with rationale
- [ ] Sprint 1 PRD updated in-place (not duplicated)
- [ ] Cross-repo alignment decisions documented

---

## Module Structure

Changes to existing files:
- `src/green/messenger.py` — rewrite: httpx → a2a-sdk ClientFactory
- `src/green/executor.py` — implement execute() with trace tracking
- `src/green/server.py` — add request ID middleware
- `src/green/agent.py` — BDD dispatch
- `tests/` — new test cases
- `docs/sprints/GreenAgent-Sprint1-PRD-Ralph.md` — AC text updates

---

## Dependencies

Already in `pyproject.toml`:
- `a2a-sdk[http-server]>=0.3.0` (messenger rewrite uses client-side imports)
- `pytest-bdd>=7.0.0` (now actually used in execution)
- `starlette` (via a2a-sdk, for middleware)

---

## Out of Scope

- Shared `src/common/` package (GraphJudge pattern — defer to Sprint 3 when Purple Agent exists)
- Peer discovery service with TTL cache (GraphJudge `common/peer_discovery.py` — not needed for single-agent evaluation)
- Docker ENTRYPOINT argparse alignment (cosmetic — current uvicorn approach works)
- Mutation caching across runs (STORY-011 F9 — low risk)
- Configurable composite score weights (STORY-012 F10 — future enhancement)
- Explicit mutmut operator configuration (STORY-011 F8 — mutmut defaults sufficient)

---

## Cross-Repo Alignment Reference

| Concern | GraphJudge (authoritative) | Our Sprint 2 Action |
|---------|---------------------------|-------------------|
| Messenger | `ClientFactory.connect()` + a2a-sdk | STORY-014: Rewrite messenger |
| Executor | Full impl with trace_id, latency | STORY-015: Implement with tracing |
| Request logging | Not implemented | STORY-016: Add middleware (our AC requires it) |
| BDD dispatch | Not applicable | STORY-017: Implement (our AC requires it) |
| AST/Gherkin parsing | Not applicable | STORY-018: Update AC text (accept read_text) |
| Shared common pkg | `src/common/` | Out of scope (Sprint 3) |
| Peer discovery | `common/peer_discovery.py` | Out of scope |

---

## Notes for Ralph Loop

<!-- PARSER REQUIREMENT: Include story count in parentheses -->
<!-- PARSER REQUIREMENT: Use (depends: STORY-XXX, STORY-YYY) for dependencies -->

Story Breakdown - Phase 2 (7 stories total):

- **Feature 14 (Messenger SDK Migration)** → STORY-014: Migrate messenger from raw httpx to a2a-sdk ClientFactory
- **Feature 15 (Executor Implementation)** → STORY-015: Implement executor with trace tracking and latency measurement (depends: STORY-014)
- **Feature 16 (Request Logging)** → STORY-016: Add request ID logging middleware to server
- **Feature 17 (BDD Dispatch)** → STORY-017: Implement BDD track dispatch in test execution
- **Feature 18 (AC Alignment)** → STORY-018: Update Sprint 1 AC text to match implementation decisions
- **Feature 19 (Data Prep Tests)** → STORY-019: Add data prep edge case and error path tests (depends: STORY-018)
- **Feature 20 (Server/Exec Tests)** → STORY-020: Add server and execution isolation tests (depends: STORY-015, STORY-016, STORY-017)
