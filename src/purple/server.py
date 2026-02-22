"""Minimal A2A server stub for Purple Agent.

Provides a health endpoint and agent-card so the container starts
without errors. Full implementation is planned for Purple Agent Sprint 1.
"""

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.types import ASGIApp


async def health(request: Request) -> JSONResponse:
    """Health check endpoint."""
    _ = request
    return JSONResponse({"status": "ok"})


async def agent_card(request: Request) -> JSONResponse:
    """Minimal agent-card for discovery."""
    _ = request
    return JSONResponse(
        {
            "name": "Purple Agent",
            "description": "Baseline test generator (stub)",
            "version": "0.0.0",
            "capabilities": {},
            "skills": [],
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
        }
    )


def create_app() -> ASGIApp:
    """Factory for uvicorn --factory mode."""
    return Starlette(
        routes=[
            Route("/health", health),
            Route("/.well-known/agent-card.json", agent_card),
        ],
    )
