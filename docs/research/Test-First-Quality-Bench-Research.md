# Research Findings: Agentic Coding Test Generation Quality

## Executive Summary

**Hypothesis**: "Current agentic coders produce tests to let code pass"

**Status**: ✅ **VALIDATED BY RESEARCH**

Current evidence strongly supports that LLMs and agentic coding tools generate tests that overfit to implementation details rather than specification requirements. This document synthesizes research findings on test quality evaluation, benchmarks, and improvement approaches.

---

## Key Findings

### 1. Test Overfitting is Empirically Verified

**Source**: ["Is the Cure Still Worse Than the Disease?"](https://arxiv.org/pdf/2511.16858) (arXiv:2511.16858)

Recent research specifically investigating LLM-based automatic program repair (APR) confirms that:
- LLMs **can and do overfit on white-box tests**
- When improving code based on white-box tests, the **overfitting rate goes UP** for affected instances
- Tests written after seeing implementation encode the implementation's bugs, not the specification

**Key experiment**:
- Evaluated 449 instances using Claude-3.7-Sonnet and GPT-4o
- Metric: Test overfitting rate (passes white-box tests but fails black-box tests)
- Finding: Overfitting persists even after removing additional context

**Security implications**: Researchers observed LLMs using reflection to access private methods just to pass tests.

---

### 2. Code Coverage Masks Low Test Quality

**Source**: [Meta Engineering Blog](https://engineering.fb.com/2025/09/30/security/llms-are-the-key-to-mutation-testing-and-better-compliance/)

Tests can achieve **100% line and branch coverage with only 4% mutation score**.

- High coverage ≠ high quality
- Coverage is weakly correlated with fault detection capability
- Mutation testing (injecting faults) reveals true test effectiveness

---

### 3. Existing Benchmarks Landscape

**Sources**: [Symflower Benchmark Analysis](https://symflower.com/en/company/blog/2025/benchmarks-llm-agents/), [Awesome Agentic Benchmarks](https://github.com/closedloop-technologies/awesome-agentic-benchmarks)

#### Test Generation Benchmarks (Directly Relevant)

| Benchmark | Tasks | Focus | Source |
|-----------|-------|-------|--------|
| **[TestGenEval](https://github.com/microsoft/TestGenEval)** | SWE-bench repos | Unit test generation | Microsoft |
| **[ProjectTest](https://arxiv.org/abs/2406.06304)** | 20 projects × 3 langs | Multi-language test gen | [arXiv:2406.06304](https://arxiv.org/abs/2406.06304) |
| **[TDD-Bench Verified](https://github.com/IBM/TDD-Bench-Verified)** | 449 issues | TDD workflow | [arXiv:2412.02883](https://arxiv.org/abs/2412.02883) |
| **[SWT-Bench](https://github.com/logic-star-ai/swt-bench)** | Test reproduction | Fail-to-pass tests | NeurIPS 2024 |

#### Code Generation Benchmarks (With Reusable Tests)

| Benchmark | Tasks | Tests/Task | Reuse Strategy | Source |
|-----------|-------|------------|----------------|--------|
| **[EvalPlus](https://github.com/evalplus/evalplus)** | 164 | 80× expanded | Best ground truth | [arXiv:2305.01210](https://arxiv.org/abs/2305.01210) |
| **[HumanEval](https://github.com/openai/human-eval)** | 164 | 7.7 avg | Baseline | [arXiv:2107.03374](https://arxiv.org/abs/2107.03374) |
| **[MBPP](https://github.com/google-research/google-research/tree/master/mbpp)** | 974 | ~3 tests | Simple problems | [arXiv:2108.07732](https://arxiv.org/abs/2108.07732) |
| **[APPS](https://github.com/hendrycks/apps)** | 10,000 | Varies | Competitive programming | [arXiv:2105.09938](https://arxiv.org/abs/2105.09938) |
| **[SWE-bench](https://www.swebench.com/)** | 2,294 | Real tests | GitHub issues | [arXiv:2310.06770](https://arxiv.org/abs/2310.06770) |
| **[SWE-bench Lite](https://github.com/SWE-bench/SWE-bench)** | 300 | Subset | Faster evaluation | [GitHub](https://github.com/SWE-bench/SWE-bench) |

#### Other Agentic Benchmarks

| Benchmark | Focus | Source |
|-----------|-------|--------|
| **[ACE-Bench](https://openreview.net/forum?id=41xrZ3uGuI)** | End-to-end feature coding | OpenReview |
| **[Terminal-Bench](https://www.tbench.ai/)** | CLI interaction | [tbench.ai](https://www.tbench.ai/) |

**Gap**: None measure whether tests are **specification-driven** vs **implementation-derived**.

---

## Mutation Testing: The Better Metric

### What is Mutation Testing?

Inject small changes ("mutations") into code and verify tests catch them. A good test suite kills most mutants.

### Approaches Using Mutation for Test Quality

| Approach | Mutation Score | Method |
|----------|----------------|--------|
| **[MuTAP](https://arxiv.org/abs/2308.16557)** | 93.57% | Augment prompts with surviving mutants |
| **[MutGen](https://arxiv.org/html/2506.02954)** | 89.5% (HumanEval-Java) | Mutation-guided test generation |
| **Meta ACH** | Not published | Generates problem-specific mutants + tests that catch them |

### Tools
- **[mutmut](https://mutmut.readthedocs.io/)**: Python mutation testing
- **[Stryker](https://stryker-mutator.io/)**: JavaScript/TypeScript mutation testing
- **[PIT](https://pitest.org/)**: Java mutation testing (industry standard)

---

## Composite Quality Metrics

### Early Quality Score (EQS)

**Source**: [Introducing EQS - StartEarly.ai](https://www.startearly.ai/post/introducing-eqs---early-quality-score)

Combines three dimensions:
1. **Coverage**: How much code is tested
2. **Mutation Score**: How effective at fault detection
3. **Method-Scope**: How broadly tests span the codebase

Distinguishes between tests that *exist* vs tests that *actually work*.

---

## Human Baseline Datasets Available

| Dataset | Size | Quality | Use Case |
|---------|------|---------|----------|
| **[TDD-Bench Verified](https://github.com/IBM/TDD-Bench-Verified)** | 449 GitHub issues | Human-validated | Real TDD workflows |
| **[HumanEval](https://github.com/openai/human-eval)** | 164 problems | Expert-curated | Avg 7.7 tests/problem |
| **[SWE-bench Verified](https://github.com/SWE-bench/SWE-bench)** | 500 issues | Curated subset of SWE-bench | Real developer tests |

### Using Human Baselines

Key insight: Compare agent-generated tests to human ground truth tests for the same specification.

Metric: **Test quality delta** = How far agent tests are from human reference implementation

---

## Current Benchmark Landscape (2025-2026)

**Source**: [8 Benchmarks Shaping AI Agents](https://ainativedev.io/news/8-benchmarks-shaping-the-next-generation-of-ai-agents)

### Recent Launches

| Benchmark | Focus | Insight | Source |
|-----------|-------|---------|--------|
| **Terminal-Bench** (May 2025) | Real CLI environments | Real software work context | [tbench.ai](https://www.tbench.ai/) |
| **Context-Bench** (Oct 2025) | Long-running context | Multi-step workflows | [Letta/UC Berkeley](https://ainativedev.io/news/8-benchmarks-shaping-the-next-generation-of-ai-agents) |
| **DPAI Arena** (Oct 2025) | Multi-language coding | JetBrains initiative | [JetBrains](https://ainativedev.io/news/8-benchmarks-shaping-the-next-generation-of-ai-agents) |
| **ACE-Bench** | End-to-end features | Execution-based evaluation | [OpenReview](https://openreview.net/forum?id=41xrZ3uGuI) |

### Evaluation Gap

**Source**: [Rethinking Coding Agent Benchmarks](https://medium.com/@steph.jarmak/rethinking-coding-agent-benchmarks-5cde3c696e4a) (Medium, Jan 2026)

> "Our ability to evaluate agent behavior is lagging far behind our ability to build agents."

**Problem**: Current benchmarks don't measure:
- How well agents perform with **limited information** (enterprise reality)
- Whether tests are **meaningful** or just **passing**
- **Implementation independence** (would tests catch bugs in alternative correct implementations?)

---

## Why This Problem Matters

### For TDD/BDD Workflows

**Source**: [Original Test Overfitting Paper (2015)](https://people.cs.umass.edu/~brun/pubs/pubs/Smith15fse.pdf) - Smith, Barr, Le Goues, Brun

TDD and BDD rely on **meaningful tests written from specification first**. If agents produce tests that overfit to implementation:

1. **Feedback loop breaks**: Tests don't guide design
2. **Refactoring risk**: Tests pass on buggy implementation, fail when refactoring ([Smith et al., 2015](https://dl.acm.org/doi/10.1145/2786805.2786825))
3. **Quality illusion**: 100% coverage but low fault detection ([Meta, 2025](https://engineering.fb.com/2025/09/30/security/llms-are-the-key-to-mutation-testing-and-better-compliance/))

### Enterprise Impact

**Source**: [Rethinking Coding Agent Benchmarks](https://medium.com/@steph.jarmak/rethinking-coding-agent-benchmarks-5cde3c696e4a)

Enterprises using agentic coders for mission-critical code face:
- False confidence in test suites
- Downstream quality issues in production
- Compliance gaps (tests don't verify requirements)

---

## Spec-Driven Testing: The Alternative

### Key Principle

**Write tests from requirements, not from implementation observation.**

Test should answer: "Does this implementation satisfy the specification?"

NOT: "What does this code do?"

### How to Verify Spec-Driven Tests

1. **Pass on correct implementation** → ✓
2. **Pass on alternative correct implementation** → ✓ (implementation independence)
3. **Fail on implementation with subtle bugs** → ✓ (fault detection)
4. **Cover all acceptance criteria** → ✓ (spec coverage)

---

## State-of-the-Art Performance Gap

**Sources**: [SWE-bench Verified Leaderboard](https://llm-stats.com/benchmarks/swe-bench-verified-(agentic-coding)), [ACE-Bench Paper](https://openreview.net/forum?id=41xrZ3uGuI)

### Claude 4 Sonnet with OpenHands (Current Best)
- **SWE-bench Verified**: 70.4% resolved rate ([source](https://llm-stats.com/benchmarks/swe-bench-verified-(agentic-coding)))
- **ACE-Bench**: 7.5% resolved rate ([source](https://openreview.net/forum?id=41xrZ3uGuI))

**Gap**: Large discrepancy suggests benchmarks measure different capabilities.

Test quality might be a missing factor.

---

## Research Directions

### Open Questions

1. **Can agentic coders be trained to write spec-driven tests?**
   - Prompt engineering: explicitly instructing spec-first approach
   - Fine-tuning: training on TDD examples

2. **What's the optimal test-to-code ratio for mutation score?**
   - More tests ≠ better mutation scores
   - Quality over quantity

3. **How does test generation time affect quality?**
   - Iterative refinement vs single-shot
   - Cost/benefit tradeoff

4. **Can specification format influence test quality?**
   - Natural language vs structured (JSON/Gherkin)
   - BDD scenarios vs acceptance criteria

---

## Sources

### Test Generation Benchmarks
- [TestGenEval](https://github.com/microsoft/TestGenEval) - Microsoft test generation benchmark
- [ProjectTest](https://arxiv.org/abs/2406.06304) - Multi-language test generation (Python, Java, JS)
- [TDD-Bench Verified](https://github.com/IBM/TDD-Bench-Verified) ([paper](https://arxiv.org/abs/2412.02883)) - IBM TDD benchmark
- [SWT-Bench](https://github.com/logic-star-ai/swt-bench) - Test reproduction benchmark

### Code Generation Benchmarks (With Reusable Tests)
- [EvalPlus](https://github.com/evalplus/evalplus) ([paper](https://arxiv.org/abs/2305.01210)) - 80× expanded test suites
- [HumanEval](https://github.com/openai/human-eval) ([paper](https://arxiv.org/abs/2107.03374)) - OpenAI baseline
- [MBPP](https://github.com/google-research/google-research/tree/master/mbpp) ([paper](https://arxiv.org/abs/2108.07732)) - 974 simple problems
- [APPS](https://github.com/hendrycks/apps) ([paper](https://arxiv.org/abs/2105.09938)) - 10K competitive problems
- [SWE-bench](https://www.swebench.com/) ([paper](https://arxiv.org/abs/2310.06770)) - Real GitHub issues
- [SWE-bench Lite](https://github.com/SWE-bench/SWE-bench) - 300-task subset

### Test Quality Research
- [Is the Cure Still Worse Than the Disease?](https://arxiv.org/pdf/2511.16858) - LLM test overfitting
- [Original Test Overfitting Paper](https://dl.acm.org/doi/10.1145/2786805.2786825) (Smith et al., 2015)
- [MuTAP](https://arxiv.org/abs/2308.16557) - Mutation-guided test generation
- [Meta Mutation Testing](https://engineering.fb.com/2025/09/30/security/llms-are-the-key-to-mutation-testing-and-better-compliance/)

### Benchmark Analysis
- [8 Benchmarks Shaping Agentic AI](https://ainativedev.io/news/8-benchmarks-shaping-the-next-generation-of-ai-agents)
- [Rethinking Coding Agent Benchmarks](https://medium.com/@steph.jarmak/rethinking-coding-agent-benchmarks-5cde3c696e4a)
- [Symflower Benchmark Analysis](https://symflower.com/en/company/blog/2025/benchmarks-llm-agents/)
- [Awesome Agentic Benchmarks](https://github.com/closedloop-technologies/awesome-agentic-benchmarks)
- [SWE-bench Verified Leaderboard](https://llm-stats.com/benchmarks/swe-bench-verified-(agentic-coding))
