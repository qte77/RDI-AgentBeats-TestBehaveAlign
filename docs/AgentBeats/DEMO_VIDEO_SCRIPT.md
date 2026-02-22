# TestBehaveAlign Demo Video Script (3 minutes)

## Opening (15 seconds)

**Visual**: Title card with logo
**Narration**: "TestBehaveAlign: The first benchmark that evaluates AI agents on test generation quality, not just code quality."

---

## Problem Statement (30 seconds)

**Visual**: Split screen showing:
- Left: Traditional benchmarks (HumanEval logo)
- Right: Real-world bugs slipping through

**Narration**:
"Current benchmarks like HumanEval measure if agents can write correct code. But in production, we need more: we need tests that catch bugs, document behavior, and enable refactoring. TestBehaveAlign measures whether AI agents can write *effective* tests."

---

## Architecture Overview (30 seconds)

**Visual**: Animated diagram (ComponentDiagram.puml)

**Narration**:
"Our system has two agents:
- The Green Agent is the evaluator—it runs tests against correct and buggy implementations
- The Purple Agent generates tests from specifications
- They communicate via the A2A protocol, following AgentBeats standards"

**Visual**: Highlight A2A flow between agents

---

## Live Demo: TDD Track (60 seconds)

**Visual**: Terminal showing:
```bash
docker compose up
```

**Narration**: "Let's see it in action. We start the benchmark with a single command."

**Visual**: Show containers starting:
- green-agent (port 9009)
- purple-agent (port 9010)
- agentbeats-client

**Visual**: Follow sequence diagram:
1. Client calls green agent
2. Green loads task: `has_close_elements` (show spec.py with docstring)
3. Green sends spec to purple via A2A
4. Purple generates pytest code (show generated test)
5. Green runs tests:
   - Against correct.py → ✅ PASS
   - Against buggy.py → ❌ FAIL
6. Green calculates score

**Visual**: Show results.json with scores:
```json
{
  "mutation_score": 0.75,
  "fault_detection_rate": 1.0,
  "overall_score": 0.85
}
```

**Narration**: "The tests pass on correct code, fail on buggy code, and catch 75% of injected mutations."

---

## Innovation Highlights (30 seconds)

**Visual**: Bullet points appearing:

**Narration**:
"What makes this unique?

1. **Objective metrics**: No LLM-as-judge. We use pytest and mutmut for deterministic evaluation.

2. **Two modalities**: TDD track uses docstrings, BDD track uses Gherkin features.

3. **Real-world tasks**: Based on EvalPlus benchmark with known bug patterns.

4. **Fully automated**: From task loading to scoring—no human intervention."

---

## Results & Impact (15 seconds)

**Visual**: Show leaderboard mockup with different purple agents ranked

**Narration**: "Results feed into the AgentBeats leaderboard, enabling researchers to compare test generation capabilities across different AI coding agents."

---

## Closing (15 seconds)

**Visual**: GitHub repo URL and AgentBeats logo

**Narration**:
"TestBehaveAlign: Measuring what matters—not just code that works, but tests that protect. Find us on GitHub and compete on AgentBeats."

**Text overlay**:
- GitHub: anthropics/testbehavealign
- AgentBeats: agentbeats.dev
- Track: TDD & BDD

**Visual**: Fade to black

---

## Technical Notes for Recording

### Screen Recordings Needed:
1. Docker compose startup (15 sec)
2. Task spec display (5 sec)
3. Generated test code (5 sec)
4. Pytest output (10 sec)
5. Results JSON (5 sec)

### Diagrams to Animate:
- ComponentDiagram.puml (use PlantUML export)
- SequenceDiagram.puml (highlight steps sequentially)

### Terminal Commands:
```bash
# Clean demo
docker compose down -v
docker compose up

# Show results
cat output/results.json | jq
```

### Callouts to Add:
- "✅ Automated" badge when showing pytest
- "🔄 A2A Protocol" badge when showing agent communication
- "📊 Objective Metrics" badge when showing scores
