"""Purple Agent messenger for A2A communication.

Handles communication with Purple Agent via A2A protocol:
- Agent card discovery
- Test generation requests
- Retry logic with exponential backoff
- Timeout handling
- Response validation
"""

import ast
import asyncio
import logging
from typing import Any, Literal

import httpx

logger = logging.getLogger(__name__)


class PurpleAgentError(Exception):
    """Raised when Purple Agent communication fails."""

    pass


class PurpleAgentMessenger:
    """Messenger for communicating with Purple Agent via A2A protocol.

    Handles agent discovery, test generation requests, retries, and validation.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:9010",
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize Purple Agent messenger.

        Args:
            base_url: Base URL of Purple Agent (default: http://localhost:9010)
            timeout: Request timeout in seconds (default: 30.0)
            max_retries: Maximum retry attempts on failure (default: 3)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

    async def discover_agent_card(self) -> dict[str, Any]:
        """Discover Purple Agent via /.well-known/agent-card.json.

        Returns:
            Agent card metadata dictionary

        Raises:
            PurpleAgentError: If discovery fails
        """
        url = f"{self.base_url}/.well-known/agent-card.json"
        logger.info(f"Discovering Purple Agent at {url}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=self.timeout)
                response.raise_for_status()
                agent_card = response.json()
                logger.info(f"Discovered Purple Agent: {agent_card.get('name', 'Unknown')}")
                return agent_card
        except (httpx.HTTPError, httpx.ConnectError) as e:
            logger.error(f"Failed to discover Purple Agent: {e}")
            raise PurpleAgentError(f"Failed to discover Purple Agent: {e}")

    async def generate_tests(
        self,
        spec: str,
        track: Literal["tdd", "bdd"],
    ) -> str:
        """Send specification to Purple Agent to generate test code.

        Implements retry logic with exponential backoff (up to 3 attempts).
        Validates response syntax with ast.parse().

        Args:
            spec: Specification string (spec.py for TDD or spec.feature for BDD)
            track: Evaluation track ("tdd" or "bdd")

        Returns:
            Generated test code as string

        Raises:
            PurpleAgentError: If request fails, times out, or response is invalid
        """
        url = f"{self.base_url}/generate-tests"
        payload = {"spec": spec, "track": track}

        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"Sending request to Purple Agent (attempt {attempt + 1}/{self.max_retries})"
                )

                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        url,
                        json=payload,
                        timeout=self.timeout,
                    )
                    response.raise_for_status()

                    result = response.json()
                    tests = result["tests"]

                    logger.info(
                        f"Received response from Purple Agent ({len(tests)} characters)"
                    )

                    # Validate response syntax with ast.parse()
                    try:
                        ast.parse(tests)
                    except SyntaxError as e:
                        logger.error(f"Invalid Python syntax in response: {e}")
                        raise PurpleAgentError(f"Invalid Python syntax in response: {e}")

                    return tests

            except httpx.TimeoutException as e:
                logger.warning(f"Request timed out (attempt {attempt + 1}): {e}")
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = 2**attempt  # Exponential backoff: 1, 2, 4 seconds
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                continue

            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP error (attempt {attempt + 1}): {e}")
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = 2**attempt  # Exponential backoff: 1, 2, 4 seconds
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                continue

            except (httpx.HTTPError, KeyError) as e:
                logger.error(f"Request failed: {e}")
                raise PurpleAgentError(f"Request failed: {e}")

        # All retries exhausted
        error_msg = f"Failed after {self.max_retries} attempts"
        if last_error:
            error_msg += f": {last_error}"
        logger.error(error_msg)
        raise PurpleAgentError(error_msg)
