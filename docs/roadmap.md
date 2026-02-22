# Roadmap

## Completed

### Green Agent Sprint 1 (STORY-001 to STORY-013)

Data preparation and core evaluation pipeline.

- **Data prep** (STORY-001 to STORY-003): EvalPlus download, buggy variant
  generation, BDD Gherkin generation
- **Core evaluation** (STORY-004 to STORY-013): Track switching, task loading,
  A2A server/client, test execution (correct + buggy), fault detection, mutation
  testing, composite scoring, results JSON output

All 13 stories passing. 184+ tests.

### Green Agent Sprint 2 (STORY-014 to STORY-020)

SDK alignment, hardening, and test coverage.

- **SDK alignment** (STORY-014, STORY-015): Messenger migrated to a2a-sdk
  `ClientFactory`, executor implemented with trace tracking
- **Implementation gaps** (STORY-016, STORY-017): Request ID logging middleware,
  BDD track dispatch via pytest-bdd
- **AC alignment** (STORY-018): Sprint 1 PRD text updated to match
  implementation decisions
- **Test hardening** (STORY-019, STORY-020): Data prep edge cases, server and
  execution isolation coverage

All 7 stories passing.

## In Progress

(none)

## Planned

### Purple Agent Sprint 1 (10 stories)

Baseline test generator with LLM integration.

- **Configuration and server** (STORY-001 to STORY-003): Pydantic settings,
  A2A discovery endpoint, request handler with validation
- **LLM integration** (STORY-004): OpenAI API with retries and backoff
- **Test generation** (STORY-005, STORY-006): TDD pytest generation, BDD
  pytest-bdd step definition generation
- **Quality and delivery** (STORY-007 to STORY-010): Code validation
  (`ast.parse`), track switching, structured JSON response, structured logging

Status: not started.
