"""Purple Agent messenger for A2A communication.

Handles communication with Purple Agent via A2A protocol:
- a2a-sdk ClientFactory with implicit AgentCard discovery
- Client caching per agent URL
- Test generation requests
- Retry logic with exponential backoff
- Timeout handling
- Response validation
"""

import ast
import asyncio
import logging
from typing import Literal

import httpx
from a2a.client import Client, ClientConfig, ClientFactory, create_text_message_object
from a2a.types import TaskState, TextPart

logger = logging.getLogger(__name__)


class PurpleAgentError(Exception):
    """Raised when Purple Agent communication fails."""

    pass


class PurpleAgentMessenger:
    """Messenger for communicating with Purple Agent via A2A protocol.

    Uses a2a-sdk ClientFactory for implicit AgentCard discovery, client caching,
    and proper TaskState lifecycle tracking.
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
        self._clients: dict[str, Client] = {}

    async def _get_client(self, url: str) -> Client:
        """Return a cached client for url, creating one on first access."""
        if url not in self._clients:
            config = ClientConfig(
                httpx_client=httpx.AsyncClient(timeout=self.timeout, trust_env=False)
            )
            self._clients[url] = await ClientFactory.connect(url, client_config=config)
        return self._clients[url]

    async def close(self) -> None:
        """Clean up all cached clients."""
        self._clients.clear()

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
        message = create_text_message_object(content=f"{track}:{spec}")
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"Sending request to Purple Agent (attempt {attempt + 1}/{self.max_retries})"
                )

                client = await self._get_client(self.base_url)
                tests: str | None = None

                async for event in client.send_message(message):
                    if isinstance(event, tuple):
                        task, _ = event
                        if task.status.state == TaskState.completed:
                            if task.artifacts:
                                for artifact in task.artifacts:
                                    for part in artifact.parts:
                                        if isinstance(part.root, TextPart):
                                            tests = part.root.text
                                            break
                                    if tests is not None:
                                        break

                if tests is None:
                    raise PurpleAgentError("No tests returned from Purple Agent")

                logger.info(f"Received response from Purple Agent ({len(tests)} characters)")

                try:
                    ast.parse(tests)
                except SyntaxError as e:
                    logger.error(f"Invalid Python syntax in response: {e}")
                    raise PurpleAgentError(f"Invalid Python syntax in response: {e}")

                return tests

            except PurpleAgentError:
                raise

            except httpx.TimeoutException as e:
                logger.warning(f"Request timed out (attempt {attempt + 1}): {e}")
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = 2**attempt  # Exponential backoff: 1, 2, 4 seconds
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                continue

            except Exception as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = 2**attempt
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                continue

        error_msg = f"Failed after {self.max_retries} attempts"
        if last_error:
            error_msg += f": {last_error}"
        logger.error(error_msg)
        raise PurpleAgentError(error_msg)
