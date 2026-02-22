"""Tests for Purple Agent messenger communication.

Tests A2A protocol communication, retry logic, timeout handling, and validation.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from green.messenger import PurpleAgentError, PurpleAgentMessenger


@pytest.fixture
def purple_messenger() -> PurpleAgentMessenger:
    """Create messenger instance for testing."""
    return PurpleAgentMessenger(base_url="http://localhost:9010")


@pytest.mark.asyncio
async def test_discover_agent_card_success(purple_messenger: PurpleAgentMessenger) -> None:
    """Test successful agent card discovery from Purple Agent."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "Purple Agent",
        "description": "Test generator",
        "url": "http://localhost:9010",
        "version": "0.0.0",
    }

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        agent_card = await purple_messenger.discover_agent_card()

    assert agent_card["name"] == "Purple Agent"
    assert agent_card["url"] == "http://localhost:9010"


@pytest.mark.asyncio
async def test_discover_agent_card_failure(purple_messenger: PurpleAgentMessenger) -> None:
    """Test agent card discovery failure handling."""
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))

    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(PurpleAgentError, match="Failed to discover Purple Agent"):
            await purple_messenger.discover_agent_card()


@pytest.mark.asyncio
async def test_generate_tests_success(purple_messenger: PurpleAgentMessenger) -> None:
    """Test successful test generation request."""
    spec = "def add(a: int, b: int) -> int:\n    '''Add two numbers.'''"
    expected_tests = "def test_add():\n    assert add(1, 2) == 3"

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"tests": expected_tests}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        tests = await purple_messenger.generate_tests(spec=spec, track="tdd")

    assert tests == expected_tests
    assert "def test_add" in tests


@pytest.mark.asyncio
async def test_generate_tests_invalid_syntax_raises_error(
    purple_messenger: PurpleAgentMessenger,
) -> None:
    """Test that invalid Python syntax in response raises error."""
    spec = "def add(a: int, b: int) -> int:\n    pass"
    invalid_tests = "def test_add(\n    assert invalid syntax"

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"tests": invalid_tests}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(PurpleAgentError, match="Invalid Python syntax in response"):
            await purple_messenger.generate_tests(spec=spec, track="tdd")


@pytest.mark.asyncio
async def test_generate_tests_timeout(purple_messenger: PurpleAgentMessenger) -> None:
    """Test timeout handling (30 seconds per request)."""
    spec = "def add(a: int, b: int) -> int:\n    pass"

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Request timed out"))

    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(PurpleAgentError, match="Request timed out"):
            await purple_messenger.generate_tests(spec=spec, track="tdd")


@pytest.mark.asyncio
async def test_generate_tests_retry_on_failure(purple_messenger: PurpleAgentMessenger) -> None:
    """Test retry logic with exponential backoff (up to 3 attempts)."""
    spec = "def add(a: int, b: int) -> int:\n    pass"

    # First two calls fail, third succeeds
    mock_response_success = MagicMock(spec=httpx.Response)
    mock_response_success.status_code = 200
    mock_response_success.json.return_value = {"tests": "def test_add(): pass"}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(
        side_effect=[
            httpx.HTTPStatusError(
                "Server error", request=MagicMock(), response=MagicMock(status_code=500)
            ),
            httpx.HTTPStatusError(
                "Server error", request=MagicMock(), response=MagicMock(status_code=500)
            ),
            mock_response_success,
        ]
    )

    with (
        patch("httpx.AsyncClient", return_value=mock_client),
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        tests = await purple_messenger.generate_tests(spec=spec, track="tdd")

    assert tests == "def test_add(): pass"
    # Verify exponential backoff: 1s, 2s delays
    assert mock_sleep.call_count == 2
    assert mock_sleep.call_args_list[0][0][0] == 1  # First retry: 1 second
    assert mock_sleep.call_args_list[1][0][0] == 2  # Second retry: 2 seconds


@pytest.mark.asyncio
async def test_generate_tests_retry_exhausted(purple_messenger: PurpleAgentMessenger) -> None:
    """Test that after 3 failed attempts, error is raised."""
    spec = "def add(a: int, b: int) -> int:\n    pass"

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=MagicMock(status_code=500)
        )
    )

    with (
        patch("httpx.AsyncClient", return_value=mock_client),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        with pytest.raises(PurpleAgentError, match="Failed after 3 attempts"):
            await purple_messenger.generate_tests(spec=spec, track="tdd")


@pytest.mark.asyncio
async def test_generate_tests_sends_correct_request(
    purple_messenger: PurpleAgentMessenger,
) -> None:
    """Test that request contains spec and track in correct format."""
    spec = "def add(a: int, b: int) -> int:\n    '''Add two numbers.'''"
    track = "tdd"

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"tests": "def test_add(): pass"}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        await purple_messenger.generate_tests(spec=spec, track=track)

        # Verify POST was called with correct URL and payload
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://localhost:9010/generate-tests"
        assert call_args[1]["json"] == {"spec": spec, "track": track}


@pytest.mark.asyncio
async def test_generate_tests_bdd_track(purple_messenger: PurpleAgentMessenger) -> None:
    """Test that BDD track is correctly sent in request."""
    spec = """Feature: Add numbers
    Scenario: Add two positive numbers
        Given I have numbers 1 and 2
        When I add them
        Then I get 3
    """
    track = "bdd"

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"tests": "def test_bdd(): pass"}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        await purple_messenger.generate_tests(spec=spec, track=track)

        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["track"] == "bdd"


@pytest.mark.asyncio
async def test_logging_interactions(purple_messenger: PurpleAgentMessenger, caplog) -> None:
    """Test that all A2A interactions are logged for debugging."""
    import logging

    caplog.set_level(logging.INFO, logger="green.messenger")

    spec = "def add(a: int, b: int) -> int:\n    pass"

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"tests": "def test_add(): pass"}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        await purple_messenger.generate_tests(spec=spec, track="tdd")

    # Verify logging occurred
    assert any("Sending request to Purple Agent" in record.message for record in caplog.records)
    assert any("Received response from Purple Agent" in record.message for record in caplog.records)
