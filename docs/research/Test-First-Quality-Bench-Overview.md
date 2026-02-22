# Test-First-Quality-Bench: Overview

## Purpose

Evaluate how well agentic coding tools generate **meaningful, specification-driven tests** in true test-first workflows.

**Hypothesis**: Current agentic coders produce tests to let code pass rather than validate requirements.

**Focus**: Exclusively on **spec-driven test quality**. Agents write tests from specifications alone - they NEVER see implementation during test generation.

---

## Two Benchmark Tracks

| Track | Spec Format | Test Format | Design Doc |
|-------|-------------|-------------|------------|
| **TDD** | Docstring + signature | pytest unit tests | [TDD-Track-Design.md](TDD-Track-Design.md) |
| **BDD** | Gherkin scenarios | pytest-bdd steps | [BDD-Track-Design.md](BDD-Track-Design.md) |

### Why Two Tracks?

| Aspect | TDD | BDD |
|--------|-----|-----|
| **Audience** | Developers | Developers + stakeholders |
| **Granularity** | Function/method level | Feature/behavior level |
| **Spec style** | Technical (types, edge cases) | Business language (Given/When/Then) |
| **Agent familiarity** | High (common format) | Medium (less common) |

---

## Shared Data Source

**Primary**: [EvalPlus](https://github.com/evalplus/evalplus) ([paper](https://arxiv.org/abs/2305.01210))

- **TDD Track**: Direct reuse of docstrings as specs
- **BDD Track**: Derive Gherkin from EvalPlus tests

### Selected Tasks (Prototype)

| Task ID | HumanEval | Name |
|---------|-----------|------|
| task_001 | HumanEval/0 | `has_close_elements` |
| task_002 | HumanEval/1 | `separate_paren_groups` |
| task_003 | HumanEval/2 | `truncate_number` |
| task_004 | HumanEval/3 | `below_zero` |
| task_005 | HumanEval/4 | `mean_absolute_deviation` |

---

## Shared Metrics

Both tracks use identical metrics for fair comparison:

| Metric | Weight | Description |
|--------|--------|-------------|
| **Mutation Score** | 30% | % mutants killed by generated tests |
| **Spec Coverage** | 25% | % requirements/scenarios covered |
| **Fault Detection** | 25% | % buggy implementations rejected |
| **Impl Independence** | 20% | Tests pass on alternative correct impls |

### Composite Score

```
Score = (0.30 × MutationScore) +
        (0.25 × SpecCoverage) +
        (0.25 × FaultDetectionRate) +
        (0.20 × ImplementationIndependence)
```

---

## Shared Evaluation Flow

```
┌─────────────────────────────────────────────────────────────┐
│ TDD TRACK                      │ BDD TRACK                  │
├────────────────────────────────┼────────────────────────────┤
│ Agent receives:                │ Agent receives:            │
│ - spec.py (docstring+sig)      │ - spec.feature (Gherkin)   │
└────────────────────────────────┴────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Agent generates tests (single-shot, no impl visible)        │
├────────────────────────────────┬────────────────────────────┤
│ TDD: pytest unit tests         │ BDD: pytest-bdd steps      │
└────────────────────────────────┴────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Run tests against hidden implementations:                   │
│ - correct.py      → Should PASS                            │
│ - buggy_v1.py     → Should FAIL                            │
│ - alternative.py  → Should PASS                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Mutation testing: mutmut run                                │
│ → Mutation Score = killed / total                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Compare to baseline + compare across tracks                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
test-first-quality-bench/
├── pyproject.toml
├── tasks/
│   ├── tdd/python/              # TDD Track tasks
│   │   └── task_001_.../
│   │       ├── spec.py          # Docstring + signature
│   │       ├── implementation/
│   │       └── baselines/
│   └── bdd/python/              # BDD Track tasks
│       └── task_001_.../
│           ├── spec/spec.feature
│           ├── implementation/  # Symlink to TDD
│           └── baselines/
├── harness/
│   ├── runner.py
│   ├── metrics.py
│   ├── mutation.py
│   ├── tdd/spec_coverage.py
│   └── bdd/spec_coverage.py
└── adapters/
    ├── base.py
    └── claude_code.py
```

---

## Implementation Checklist

### Phase 1: TDD Track

- [ ] Download [EvalPlus](https://github.com/evalplus/evalplus) dataset
- [ ] Extract `spec.py` from HumanEval/0-4 docstrings
- [ ] Create implementation variants (correct, buggy, alternative)
- [ ] Implement harness: `runner.py`, `metrics.py`, `mutation.py`
- [ ] Implement `adapters/claude_code.py`
- [ ] Run evaluation, collect mutation scores

### Phase 2: BDD Track

- [ ] Derive Gherkin from same 5 EvalPlus tasks
- [ ] Symlink implementations from TDD track
- [ ] Implement `harness/bdd/spec_coverage.py`
- [ ] Run evaluation, compare to TDD scores

### Phase 3: Validation

- [ ] Verify: Agent mutation score < EvalPlus baseline
- [ ] Compare TDD vs BDD performance
- [ ] Tune metric weights if needed

---

## Dependencies

```toml
[project]
dependencies = [
    "pytest>=8.0",
    "pytest-bdd>=7.0",
    "mutmut>=3.0",
    "gherkin-official>=29.0",
]
```

---

## Verification Commands

```bash
pytest harness/                                                    # Verify harness
python -m harness.runner --track tdd --adapter claude_code         # TDD evaluation
python -m harness.runner --track bdd --adapter claude_code         # BDD evaluation
mutmut run --paths-to-mutate=tasks/tdd/python/task_001/impl/       # Mutation test
```

---

## Documentation Index

| Document | Purpose |
|----------|---------|
| **This file** | Overview, metrics, checklist |
| [TDD-Track-Design.md](TDD-Track-Design.md) | TDD track: spec format, examples |
| [BDD-Track-Design.md](BDD-Track-Design.md) | BDD track: spec format, examples |
| [Test-First-Quality-Bench-Tools.md](Test-First-Quality-Bench-Tools.md) | Tool selection rationale |
| [Test-First-Quality-Bench-Research.md](Test-First-Quality-Bench-Research.md) | Research findings |

---

## Success Criteria

| Criterion | Target |
|-----------|--------|
| Harness functional | 10 tasks (5 TDD + 5 BDD) evaluate |
| Hypothesis validated | Agent scores < baseline scores |
| Reproducible | ±5% variance on repeat runs |
| Track comparison | TDD vs BDD scores analyzable |

---

## References

### Benchmarks
- [EvalPlus](https://github.com/evalplus/evalplus) - Primary data source
- [TestGenEval](https://github.com/microsoft/TestGenEval) - Microsoft test generation
- [TDD-Bench Verified](https://github.com/IBM/TDD-Bench-Verified) - IBM TDD benchmark

### Tools
- [mutmut](https://mutmut.readthedocs.io/) - Mutation testing
- [pytest-bdd](https://pytest-bdd.readthedocs.io/) - BDD execution
- [Gherkin](https://github.com/cucumber/gherkin) - Spec parsing

### Research
- [Test Overfitting in LLM APR](https://arxiv.org/pdf/2511.16858) - Validates hypothesis
- [MuTAP](https://arxiv.org/abs/2308.16557) - Mutation-guided test generation

---

## Future MVP (Deferred)

- Multi-language: TypeScript (Stryker), Go
- More agents: Cursor, Aider
- Scale: 30+ tasks per track
- Additional sources: TestGenEval, TDD-Bench Verified, MBPP
