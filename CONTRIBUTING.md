---
title: Contribution Guidelines
version: 1.0
applies-to: Agents and humans
purpose: Developer setup, workflow, and contribution guidelines
---

Contributions welcome! Follow these guidelines for both human and agent contributors:

## Core Principles

- **KISS** (Keep It Simple, Stupid) - Simplest solution that works
- **DRY** (Don't Repeat Yourself) - Single source of truth
- **YAGNI** (You Aren't Gonna Need It) - Implement only what's requested
- **User Experience, Joy, and Success** - Optimize for user value

See `.claude/rules/core-principles.md` for complete guidelines.

## Development Workflow

### 1. Setup Environment

```bash
make setup_dev  # Install dependencies and configure tools
```

### 2. Make Changes

Follow TDD: Write tests before implementing features.

### 3. Validate

```bash
make ruff        # Format and lint
make type_check  # Type checking
make test_all    # Run tests
make validate    # Run all checks (required before committing)
```

### 4. Commit

All changes must pass `make validate` before committing.
