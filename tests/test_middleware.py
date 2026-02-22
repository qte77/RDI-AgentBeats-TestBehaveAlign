"""Tests for request ID logging middleware.

TDD RED phase - these tests fail before the middleware is implemented.
Covers acceptance criteria for STORY-016.
"""

import uuid
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
from fastapi import FastAPI


@pytest.fixture
def app(temp_scenario_file: Path, monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    """Return the FastAPI app from a fresh server instance."""
    from green.server import create_server

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    server = create_server(temp_scenario_file)
    return server.app  # type: ignore[return-value]


class TestRequestIDMiddleware:
    """Test suite for request ID logging middleware (STORY-016)."""

    @pytest.mark.asyncio
    async def test_response_includes_x_request_id_header(self, app: FastAPI) -> None:
        """Response must include X-Request-ID header."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
            trust_env=False,
        ) as client:
            response = await client.get("/health")

        assert "x-request-id" in response.headers

    @pytest.mark.asyncio
    async def test_request_id_is_valid_uuid4(self, app: FastAPI) -> None:
        """Request ID must be a valid UUID4."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
            trust_env=False,
        ) as client:
            response = await client.get("/health")

        request_id = response.headers["x-request-id"]
        parsed = uuid.UUID(request_id)
        assert parsed.version == 4

    @pytest.mark.asyncio
    async def test_each_request_gets_unique_id(self, app: FastAPI) -> None:
        """Each request must receive a distinct request ID."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
            trust_env=False,
        ) as client:
            r1 = await client.get("/health")
            r2 = await client.get("/health")

        assert r1.headers["x-request-id"] != r2.headers["x-request-id"]

    @pytest.mark.asyncio
    async def test_middleware_logs_method_and_path(self, app: FastAPI) -> None:
        """Middleware must log HTTP method and path."""
        with patch("green.server.logger") as mock_logger:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
                trust_env=False,
            ) as client:
                await client.get("/health")

        assert mock_logger.info.called
        all_log_text = " ".join(str(c) for c in mock_logger.info.call_args_list)
        assert "GET" in all_log_text
        assert "/health" in all_log_text

    @pytest.mark.asyncio
    async def test_middleware_logs_status_code(self, app: FastAPI) -> None:
        """Middleware must log HTTP status code."""
        with patch("green.server.logger") as mock_logger:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
                trust_env=False,
            ) as client:
                await client.get("/health")

        all_log_text = " ".join(str(c) for c in mock_logger.info.call_args_list)
        assert "200" in all_log_text

    @pytest.mark.asyncio
    async def test_middleware_logs_request_id(self, app: FastAPI) -> None:
        """Middleware log entries must include the request ID."""
        with patch("green.server.logger") as mock_logger:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
                trust_env=False,
            ) as client:
                response = await client.get("/health")

        request_id = response.headers["x-request-id"]
        all_log_text = " ".join(str(c) for c in mock_logger.info.call_args_list)
        assert request_id in all_log_text

    @pytest.mark.asyncio
    async def test_middleware_logs_duration(self, app: FastAPI) -> None:
        """Middleware must log request duration."""
        with patch("green.server.logger") as mock_logger:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
                trust_env=False,
            ) as client:
                await client.get("/health")

        all_log_text = " ".join(str(c) for c in mock_logger.info.call_args_list)
        # Duration should appear as a number followed by ms or similar unit
        assert "duration" in all_log_text.lower() or "ms" in all_log_text.lower()
