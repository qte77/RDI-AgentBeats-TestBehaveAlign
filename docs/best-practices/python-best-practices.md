---
title: Python Best Practices Reference
version: 1.0
applies-to: Agents and humans
purpose: Python coding standards, type annotations, and testing guidelines
---

## Code Style

- Use `ruff` for formatting (run `make format`)
- 88 character line limit
- Follow PEP 8 conventions
- Use descriptive variable names (no single letters except loop indices)

## Type Annotations

- **Always** use type hints for function signatures
- Use `from __future__ import annotations` for forward references
- Prefer built-in types: `list[str]` over `List[str]` (Python 3.11+)
- Use `None` instead of `Optional[T]` where possible: `str | None`

```python
from __future__ import annotations

def process_data(
    items: list[dict[str, str]], count: int | None = None
) -> dict[str, int]:
    """Process items and return statistics."""
    ...
```

## Imports

- Order: stdlib → third-party → local
- Use absolute imports for project code
- Group related imports
- Avoid `import *`

```python
# stdlib
import asyncio
from pathlib import Path

# third-party
import networkx as nx
from pydantic import BaseModel

# local
from agentbeats.messenger import Messenger
```

## Error Handling

- Raise specific exceptions, not generic `Exception`
- Use built-in exceptions where appropriate: `ValueError`, `TypeError`, `RuntimeError`
- Create custom exceptions for domain errors
- Document exceptions in docstrings

```python
class EvaluationError(Exception):
    """Raised when evaluation fails."""
    pass

def evaluate(data: dict[str, str]) -> float:
    """Evaluate data quality.

    Raises:
        EvaluationError: If data is invalid or incomplete
    """
    if not data:
        raise EvaluationError("Data cannot be empty")
    ...
```

## Pydantic Models

### When to Use Pydantic Validation

**Core Principle**: Validate at system boundaries, trust internal code.

Use Pydantic `model_validate()` for **external data** from:

- **API requests/responses** - HTTP, JSON-RPC, A2A protocol messages
- **File I/O** - JSON/YAML/TOML configuration files, data files
- **Cross-module boundaries** - When receiving data from another module where the source is untrusted or dynamically generated
- **User input** - CLI arguments, form data, uploaded files

**Internal code** (same module, trusted sources) can use direct construction for performance.

### Model Definition

- Use Pydantic for data validation and serialization
- Add `model_config` for strict validation (`strict=True` catches type errors early)
- Document fields with descriptions
- Use `frozen=True` for immutable data

```python
from pydantic import BaseModel, Field

class EvalRequest(BaseModel):
    """Request for agent evaluation."""

    model_config = {"strict": True, "frozen": True}

    agent_url: str = Field(..., description="URL of agent to evaluate")
    task: str = Field(..., description="Task description")
```

### Validation at Boundaries

Use `model_validate()` for external/untrusted data to catch schema violations:

```python
# GOOD: Validate external API response
response_data = await client.post(url, json=payload)
eval_result = EvaluationResult.model_validate(response_data.json())

# GOOD: Validate file data
config_data = json.loads(Path("config.json").read_text())
config = AppConfig.model_validate(config_data)

# GOOD: Validate cross-module data from untrusted source
def process_external_data(raw_data: dict[str, str]) -> ProcessedResult:
    """Process data from external module."""
    validated = InputData.model_validate(raw_data)  # Validate boundary
    return _internal_process(validated)

# ACCEPTABLE: Direct construction for internal trusted data
def _internal_process(data: InputData) -> ProcessedResult:
    """Internal function - data already validated."""
    result = ProcessedResult(score=0.95, valid=True)  # Trust internal code
    return result
```

### Error Handling

Pydantic validation errors should be caught at boundaries:

```python
from pydantic import ValidationError

try:
    request = EvalRequest.model_validate(request_data)
except ValidationError as e:
    raise ValueError(f"Invalid request: {e.errors()}") from e
```

## Async Patterns

- Use `async`/`await` for I/O operations
- Use `httpx.AsyncClient` for HTTP requests
- Handle timeouts explicitly

```python
import httpx

async def call_agent(url: str, data: dict[str, str]) -> dict[str, str]:
    """Call agent with timeout."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=data)
        response.raise_for_status()
        return response.json()
```

## Testing

- Use `pytest` for all tests
- Test file naming: `test_<module>.py`
- Test function naming: `test_<function>_<scenario>`
- Use fixtures for shared setup
- Mock external dependencies

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
def sample_traces() -> list[dict[str, str]]:
    """Provide sample trace data."""
    return [{"agent": "A", "target": "B", "action": "call"}]

async def test_messenger_captures_traces(sample_traces):
    """Test that messenger captures agent interactions."""
    ...
```

## Security

- **Never** commit secrets or API keys
- Validate all external input
- Use parameterized queries (if using SQL)
- Sanitize user-provided data before processing

## Documentation

- Add module-level docstrings explaining purpose
- Add function docstrings for public APIs
- Keep docstrings concise (1-2 sentences)
- Document parameters, returns, and exceptions only when not obvious

```python
"""Agent evaluation coordinator.

Orchestrates messenger, evaluators, and executor to assess agent quality.
"""

def run_evaluation(request: EvalRequest) -> dict[str, float]:
    """Run evaluation and return metrics."""
    ...
```
