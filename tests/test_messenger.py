"""Tests for Purple Agent messenger - a2a-sdk ClientFactory migration.

Tests A2A protocol communication via a2a-sdk, retry logic, and response validation.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from a2a.types import TaskState, TextPart

from green.messenger import PurpleAgentError, PurpleAgentMessenger

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_completed_task(text: str) -> MagicMock:
    """Create a mock completed Task with text in the first artifact."""
    mock_part = MagicMock()
    mock_part.root = TextPart(text=text)  # real TextPart for isinstance checks

    mock_artifact = MagicMock()
    mock_artifact.parts = [mock_part]

    mock_task = MagicMock()
    mock_task.status.state = TaskState.completed
    mock_task.artifacts = [mock_artifact]
    return mock_task


def make_send_message(*events: Any):
    """Return an async generator function that yields the given events."""

    async def _send(message: Any, **kwargs: Any) -> Any:
        for event in events:
            yield event

    return _send


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def messenger() -> PurpleAgentMessenger:
    return PurpleAgentMessenger(base_url="http://localhost:9010")


@pytest.fixture
def mock_a2a_client():
    """A mock a2a Client."""
    return MagicMock()


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_messenger_returns_completed_task_text(
    messenger: PurpleAgentMessenger, mock_a2a_client: MagicMock
) -> None:
    """generate_tests extracts text from the completed task artifact."""
    expected = "def test_add():\n    assert add(1, 2) == 3"
    task = make_completed_task(expected)
    mock_a2a_client.send_message = make_send_message((task, None))

    with patch(
        "green.messenger.ClientFactory.connect",
        new=AsyncMock(return_value=mock_a2a_client),
    ):
        result = await messenger.generate_tests(spec="def add(a, b): pass", track="tdd")

    assert result == expected


@pytest.mark.asyncio
async def test_messenger_uses_client_factory_connect(
    messenger: PurpleAgentMessenger, mock_a2a_client: MagicMock
) -> None:
    """generate_tests uses ClientFactory.connect instead of raw httpx."""
    task = make_completed_task("def test_ok(): pass")
    mock_a2a_client.send_message = make_send_message((task, None))

    with patch(
        "green.messenger.ClientFactory.connect",
        new=AsyncMock(return_value=mock_a2a_client),
    ) as mock_connect:
        await messenger.generate_tests(spec="def f(): pass", track="tdd")

    mock_connect.assert_awaited_once()
    # First positional argument must be the agent URL
    assert mock_connect.call_args.args[0] == "http://localhost:9010"


@pytest.mark.asyncio
async def test_messenger_passes_httpx_client_to_config(
    messenger: PurpleAgentMessenger, mock_a2a_client: MagicMock
) -> None:
    """ClientConfig is created with httpx.AsyncClient for transport (not for protocol)."""
    task = make_completed_task("def test_ok(): pass")
    mock_a2a_client.send_message = make_send_message((task, None))

    from a2a.client import ClientConfig

    with patch(
        "green.messenger.ClientFactory.connect",
        new=AsyncMock(return_value=mock_a2a_client),
    ) as mock_connect:
        await messenger.generate_tests(spec="def f(): pass", track="tdd")

    _, kwargs = mock_connect.call_args[0], mock_connect.call_args.kwargs
    client_config = kwargs.get("client_config") or mock_connect.call_args.args[1]
    assert isinstance(client_config, ClientConfig)
    assert client_config.httpx_client is not None


# ---------------------------------------------------------------------------
# Client caching
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_messenger_caches_client_per_url(
    messenger: PurpleAgentMessenger, mock_a2a_client: MagicMock
) -> None:
    """ClientFactory.connect is called only once per URL across multiple requests."""
    task = make_completed_task("def test_ok(): pass")
    mock_a2a_client.send_message = make_send_message((task, None))

    with patch(
        "green.messenger.ClientFactory.connect",
        new=AsyncMock(return_value=mock_a2a_client),
    ) as mock_connect:
        await messenger.generate_tests(spec="spec1", track="tdd")
        await messenger.generate_tests(spec="spec2", track="bdd")

    assert mock_connect.await_count == 1


@pytest.mark.asyncio
async def test_messenger_close_clears_cached_clients(
    messenger: PurpleAgentMessenger, mock_a2a_client: MagicMock
) -> None:
    """close() purges the client cache so the next request reconnects."""
    task = make_completed_task("def test_ok(): pass")
    mock_a2a_client.send_message = make_send_message((task, None))

    with patch(
        "green.messenger.ClientFactory.connect",
        new=AsyncMock(return_value=mock_a2a_client),
    ) as mock_connect:
        await messenger.generate_tests(spec="spec1", track="tdd")
        await messenger.close()
        # Need to rebuild the side_effect since generator is exhausted
        mock_a2a_client.send_message = make_send_message((task, None))
        await messenger.generate_tests(spec="spec2", track="tdd")

    assert mock_connect.await_count == 2


def test_messenger_has_close_method(messenger: PurpleAgentMessenger) -> None:
    """Messenger exposes a close() method for resource cleanup."""
    import inspect

    assert callable(getattr(messenger, "close", None))
    assert inspect.iscoroutinefunction(messenger.close)


# ---------------------------------------------------------------------------
# Discovery removed
# ---------------------------------------------------------------------------


def test_messenger_has_no_discover_agent_card_method(
    messenger: PurpleAgentMessenger,
) -> None:
    """discover_agent_card() is removed; SDK handles discovery internally."""
    assert not hasattr(messenger, "discover_agent_card")


# ---------------------------------------------------------------------------
# Response validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_messenger_raises_on_invalid_syntax(
    messenger: PurpleAgentMessenger, mock_a2a_client: MagicMock
) -> None:
    """PurpleAgentError is raised when the response contains invalid Python."""
    task = make_completed_task("def test_broken(\n    assert invalid")
    mock_a2a_client.send_message = make_send_message((task, None))

    with patch(
        "green.messenger.ClientFactory.connect",
        new=AsyncMock(return_value=mock_a2a_client),
    ):
        with pytest.raises(PurpleAgentError, match="Invalid Python syntax"):
            await messenger.generate_tests(spec="def f(): pass", track="tdd")


# ---------------------------------------------------------------------------
# Retry logic
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_messenger_retries_on_timeout(
    messenger: PurpleAgentMessenger, mock_a2a_client: MagicMock
) -> None:
    """generate_tests retries with exponential backoff on TimeoutException."""
    task = make_completed_task("def test_ok(): pass")

    call_count = 0

    async def send_with_timeout(message: Any, **kwargs: Any) -> Any:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise httpx.TimeoutException("timed out")
        yield (task, None)

    mock_a2a_client.send_message = send_with_timeout

    with (
        patch(
            "green.messenger.ClientFactory.connect",
            new=AsyncMock(return_value=mock_a2a_client),
        ),
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        result = await messenger.generate_tests(spec="def f(): pass", track="tdd")

    assert result == "def test_ok(): pass"
    assert mock_sleep.await_count == 2
    assert mock_sleep.call_args_list[0].args[0] == 1  # 2^0
    assert mock_sleep.call_args_list[1].args[0] == 2  # 2^1


@pytest.mark.asyncio
async def test_messenger_raises_after_exhausted_retries(
    messenger: PurpleAgentMessenger, mock_a2a_client: MagicMock
) -> None:
    """PurpleAgentError is raised after all retry attempts fail."""

    async def always_timeout(message: Any, **kwargs: Any) -> Any:
        for _ in range(0):  # makes this an async generator without unreachable code
            yield None
        raise httpx.TimeoutException("timed out")

    mock_a2a_client.send_message = always_timeout

    with (
        patch(
            "green.messenger.ClientFactory.connect",
            new=AsyncMock(return_value=mock_a2a_client),
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        with pytest.raises(PurpleAgentError, match="Failed after 3 attempts"):
            await messenger.generate_tests(spec="def f(): pass", track="tdd")


@pytest.mark.asyncio
async def test_messenger_logs_send_interactions(
    messenger: PurpleAgentMessenger, mock_a2a_client: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    """Sending and receiving are logged for observability."""
    import logging

    caplog.set_level(logging.INFO, logger="green.messenger")

    task = make_completed_task("def test_ok(): pass")
    mock_a2a_client.send_message = make_send_message((task, None))

    with patch(
        "green.messenger.ClientFactory.connect",
        new=AsyncMock(return_value=mock_a2a_client),
    ):
        await messenger.generate_tests(spec="def f(): pass", track="tdd")

    messages = [r.message for r in caplog.records]
    assert any("Sending request" in m for m in messages)
    assert any("Received response" in m for m in messages)
