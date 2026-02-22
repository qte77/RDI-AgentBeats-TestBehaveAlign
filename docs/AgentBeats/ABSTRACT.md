# TestBehaveAlign: A Test-First Quality Benchmark for AgentBeats

## Abstract

TestBehaveAlign evaluates AI agents on **test generation quality** through two tracks: TDD (Test-Driven Development) and BDD (Behavior-Driven Development). Unlike traditional benchmarks that assess code generation, we measure whether agents can write effective tests that detect bugs and guide implementation.

## Problem Statement

Current code generation benchmarks (HumanEval, MBPP) evaluate functional correctness but ignore test quality. Real-world software requires tests that:

- Catch regressions
- Document behavior
- Guide refactoring

## Our Approach

**Green Agent (Evaluator)**: Runs generated tests against correct and buggy implementations, measuring:

- **Fault Detection Rate**: Do tests pass on correct code and fail on buggy code?
- **Mutation Score**: Do tests catch artificially injected bugs?

**Purple Agent (Test Generator)**: Baseline agent that generates pytest or pytest-bdd tests from specifications.

## Innovation

1. **Objective Metrics**: No LLM-as-judge—all evaluation is automated (pytest, mutmut)
2. **Two Modalities**: TDD (docstring → unit tests) and BDD (Gherkin → acceptance tests)
3. **Realistic Tasks**: 5 problems from EvalPlus benchmark with known bugs
4. **Reproducible**: Containerized, deterministic evaluation

## Tracks

- **TDD Track**: Generate pytest tests from Python docstrings
- **BDD Track**: Generate pytest-bdd step definitions from Gherkin features

## Scoring

```text
MVP Score = (0.60 × Mutation Score) + (0.40 × Fault Detection Rate)
```

Both metrics are fully automated and deterministic.

## Deliverables

- 5 annotated tasks from HumanEval (0-4)
- Docker images for green and purple agents
- A2A protocol implementation
- Results in AgentBeats JSON format

## Target Audience

Researchers and practitioners interested in:

- Test generation capabilities of AI coding agents
- Quality assurance automation
- Agent-based software engineering

## Competition Alignment

- **Reproducible**: Fixed task set, containerized
- **Automated**: No manual scoring
- **Innovative**: First benchmark focusing on test quality over code quality
- **Rigorous**: Based on established benchmarks (EvalPlus) and mutation testing
