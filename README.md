# TestBehaveAlign

> Measure test quality, not just code correctness.

TestBehaveAlign evaluates AI agents on test generation quality, not just code generation. It measures whether agents can write effective tests that catch bugs and guide implementation.

[![AgentBeats](https://img.shields.io/badge/AgentBeats-Benchmark-blue)](https://agentbeats.dev)
[![Python](https://img.shields.io/badge/python-3.13+-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE.md)

## Overview

Unlike traditional benchmarks (HumanEval, MBPP) that measure code correctness, TestBehaveAlign measures **test quality** through:

- **Fault Detection**: Do tests pass on correct code and fail on buggy code?
- **Mutation Score**: Do tests catch artificially injected bugs?

**Two Evaluation Tracks**:
- **TDD**: Generate pytest tests from Python docstrings
- **BDD**: Generate pytest-bdd step definitions from Gherkin features

**All metrics are objective and deterministic** - no LLM-as-judge required.

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key (for purple agent test generation)

### Run Locally

```bash
# 1. Clone repository
git clone https://github.com/YOUR_ORG/RDI-AgentBeats-TestBehaveAlign.git
cd RDI-AgentBeats-TestBehaveAlign

# 2. Set up environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Download benchmark data (5 tasks from EvalPlus)
pip install -e .[scripts]  # Install data download dependencies
python scripts/download_evalplus.py
python scripts/create_variants.py
python scripts/generate_gherkin.py

# 4. Run evaluation
docker compose up

# 5. Check results
cat output/results.json
```

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐
│  Purple Agent   │────▶│   Green Agent    │
│ (Test Generator)│     │   (Evaluator)    │
└─────────────────┘     └──────────────────┘
        │                        │
        │  1. Generates tests    │  2. Runs tests vs
        │     from specs         │     correct + buggy
        ▼                        ▼
   pytest code           ✓ PASS / ✗ FAIL
                                │
                         3. Mutation testing
                                │
                         4. Calculate score
                                ▼
                          results.json
```

**Green Agent** (Port 9009): Evaluator that runs tests and calculates quality metrics
**Purple Agent** (Port 9010): Baseline test generator using LLM (OpenAI)

---

## Scoring Formula

```
Score = (0.60 × Mutation Score) + (0.40 × Fault Detection Rate)
```

- **Mutation Score**: Percentage of injected bugs caught by tests (via mutmut)
- **Fault Detection Rate**: Binary - tests must PASS on correct.py AND FAIL on buggy.py

---

## Documentation

- [Competition Abstract](docs/AgentBeats/ABSTRACT.md) - Problem statement and approach
- [Architecture Diagrams](docs/arch_vis/) - PlantUML system diagrams
- [Green Agent PRD](docs/GreenAgent-PRD.md) - Evaluator requirements
- [Purple Agent PRD](docs/PurpleAgent-PRD.md) - Test generator requirements
- [Demo Video Script](docs/AgentBeats/DEMO_VIDEO_SCRIPT.md) - 3-minute demo guide

---

## Development

### Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### Run Tests

```bash
pytest tests/
```

### Validate Results

```bash
python scripts/validate_results.py output/results.json
```

### Local Testing (without AgentBeats client)

```bash
# Use local Docker images instead of GHCR
docker compose -f docker-compose-local.yml up
```

---

## AgentBeats Submission

1. **Register agents** at [agentbeats.dev](https://agentbeats.dev)
   - Register green agent → get `agentbeats_id`
   - Register purple agent → get `agentbeats_id`

2. **Update scenario.toml** with real agent IDs

3. **Push Docker images** to GHCR:
   ```bash
   ./scripts/docker/build.sh
   ./scripts/docker/push.sh
   ```

4. **Trigger workflow**:
   ```bash
   gh workflow run agentbeats-run-scenario.yml
   ```

See [Submission Guide](docs/AgentBeats/SUBMISSION-GUIDE.md) for details.

---

## Project Structure

```
├── data/tasks/              # Benchmark tasks (5 from HumanEval)
│   ├── tdd/python/         # TDD track (pytest)
│   └── bdd/python/         # BDD track (pytest-bdd)
├── src/
│   ├── green/              # Evaluator agent
│   └── purple/             # Baseline test generator
├── scripts/
│   ├── download_evalplus.py    # Download benchmark data
│   ├── create_variants.py      # Generate buggy implementations
│   └── generate_gherkin.py     # Derive BDD from TDD
├── docs/                   # Architecture & requirements
├── scenario.toml           # AgentBeats configuration
└── docker-compose.yml      # Local testing setup
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT License - see [LICENSE.md](LICENSE.md)

---

## Citation

```bibtex
@software{testbehavealign2026,
  title={TestBehaveAlign: A Test-First Quality Benchmark for AI Coding Agents},
  author={Your Organization},
  year={2026},
  url={https://github.com/YOUR_ORG/RDI-AgentBeats-TestBehaveAlign}
}
```

---

## Contact

- GitHub Issues: [Report bugs or request features](https://github.com/YOUR_ORG/RDI-AgentBeats-TestBehaveAlign/issues)
- AgentBeats: [Competition page](https://agentbeats.dev)
