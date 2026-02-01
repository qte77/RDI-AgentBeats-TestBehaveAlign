"""A2A server for Green Agent.

HTTP server with A2A protocol endpoints for test quality evaluation.
Serves AgentCard, evaluation endpoints, and health checks.
"""

import asyncio
import logging
import signal
from pathlib import Path

import uvicorn
from a2a.server.apps.rest.fastapi_app import A2ARESTFastAPIApplication
from a2a.server.request_handlers.default_request_handler import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from green.executor import GreenAgentExecutor

logger = logging.getLogger(__name__)


class GreenAgentServer:
    """Green Agent A2A server.

    Serves HTTP endpoints for test quality evaluation using A2A protocol.
    """

    def __init__(self, scenario_file: Path, port: int = 9009) -> None:
        """Initialize server with configuration.

        Args:
            scenario_file: Path to scenario.toml configuration
            port: Port to serve on (default: 9009)
        """
        self.port = port
        self.scenario_file = scenario_file
        self.executor = GreenAgentExecutor(scenario_file)
        self._uvicorn_server: uvicorn.Server | None = None

        # Create AgentCard
        agent_card = AgentCard(
            name="Green Agent",
            description="Test quality evaluator for AI coding agents",
            url="http://localhost:9009",
            version="0.0.0",
            capabilities=AgentCapabilities(),
            skills=[
                AgentSkill(
                    id="evaluate-tests",
                    name="Evaluate Test Quality",
                    description=(
                        "Evaluate generated tests using fault detection and mutation testing"
                    ),
                    tags=["testing", "evaluation", "quality"],
                )
            ],
            default_input_modes=["text"],
            default_output_modes=["text"],
        )

        # Create task store and request handler
        task_store = InMemoryTaskStore()
        request_handler = DefaultRequestHandler(
            agent_executor=self.executor,
            task_store=task_store,
        )

        # Create A2A application and build FastAPI app
        a2a_app = A2ARESTFastAPIApplication(
            agent_card=agent_card,
            http_handler=request_handler,
        )
        self.app = a2a_app.build()

        # Store agent_card on both server and app for easy access
        self.agent_card = agent_card
        self.app.agent_card = agent_card  # type: ignore

        # Add health endpoint to FastAPI app
        self._add_health_endpoint()

        # Setup graceful shutdown
        self._shutdown_event = asyncio.Event()
        self._setup_signal_handlers()

    def _add_health_endpoint(self) -> None:
        """Add health check endpoint to FastAPI app."""

        # Add health endpoint to the FastAPI app
        @self.app.get("/health")
        async def health() -> dict[str, str]:
            """Health check endpoint."""
            return {"status": "ok"}

        # Explicitly mark as used to satisfy type checker
        _ = health

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""

        def handle_shutdown(signum: int, _frame: object) -> None:  # noqa: ARG001
            """Handle shutdown signals."""
            logger.info(f"Received signal {signum}, initiating graceful shutdown")
            self._shutdown_event.set()

        signal.signal(signal.SIGTERM, handle_shutdown)
        signal.signal(signal.SIGINT, handle_shutdown)

    async def start(self) -> None:
        """Start the A2A server."""
        logger.info(f"Starting Green Agent server on port {self.port}")

        # Create uvicorn config
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info",
        )
        self._uvicorn_server = uvicorn.Server(config)

        # Run server until shutdown signal
        await self._uvicorn_server.serve()

    async def shutdown(self) -> None:
        """Gracefully shutdown the server."""
        logger.info("Shutting down Green Agent server")
        if self._uvicorn_server:
            self._uvicorn_server.should_exit = True
        self._shutdown_event.set()

    async def stop(self) -> None:
        """Stop the server (alias for shutdown)."""
        await self.shutdown()


def create_server(scenario_file: Path, port: int = 9009) -> GreenAgentServer:
    """Create Green Agent A2A server.

    Args:
        scenario_file: Path to scenario.toml configuration
        port: Port to serve on (default: 9009)

    Returns:
        Configured GreenAgentServer instance
    """
    return GreenAgentServer(scenario_file, port)
