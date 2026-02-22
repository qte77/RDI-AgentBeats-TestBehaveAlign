"""A2A executor for Green Agent.

Implements AgentExecutor interface for A2A protocol integration.
Orchestrates test evaluation workflow.
"""

import logging
import time
import uuid
from pathlib import Path

from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import TaskArtifactUpdateEvent, TaskState, TaskStatus, TaskStatusUpdateEvent
from a2a.utils.artifact import new_data_artifact

from green.agent import (
    GreenAgent,
    aggregate_fault_detection_scores,
    calculate_composite_score,
    calculate_fault_detection_score,
    execute_test_against_buggy,
    execute_test_against_correct,
    generate_agentbeats_results,
    load_task,
    run_mutation_testing,
)
from green.messenger import PurpleAgentMessenger
from green.models import TaskDetail
from green.settings import Settings

logger = logging.getLogger(__name__)


class GreenAgentExecutor(AgentExecutor):
    """Green Agent executor for A2A protocol.

    Handles evaluation requests and orchestrates test quality assessment.
    """

    def __init__(self, scenario_file: Path) -> None:
        """Initialize executor with scenario configuration.

        Args:
            scenario_file: Path to scenario.toml configuration file

        Raises:
            FileNotFoundError: If scenario file does not exist
            ValueError: If scenario file is invalid
        """
        if not scenario_file.exists():
            raise FileNotFoundError(f"Scenario file not found: {scenario_file}")

        self.settings = Settings.from_file(scenario_file)

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute evaluation request.

        Args:
            context: A2A request context with user message
            event_queue: Event queue for publishing updates

        Generates a UUID trace_id per evaluation, runs the full agent
        evaluation pipeline, records latency, and publishes results as
        an A2A artifact. Calls messenger.close() in the finally block.
        """
        trace_id = str(uuid.uuid4())
        logger.info("Starting evaluation [trace_id=%s]", trace_id)

        messenger = PurpleAgentMessenger()

        try:
            start_time = time.time()

            participant_id = context.get_user_input().strip() or "unknown"

            agent = GreenAgent(self.settings)
            track = self.settings.track
            task_dir = agent.get_task_directory()

            fault_detection_scores: list[float] = []
            mutation_scores: list[float] = []
            task_details: list[TaskDetail] = []

            for i in range(self.settings.task_count):
                task_id = f"task_{i + 1:03d}"

                try:
                    task = load_task(task_dir / task_id, track)

                    test_code = await messenger.generate_tests(spec=task.spec, track=track)

                    correct_result = execute_test_against_correct(
                        test_code, task.correct_implementation, track
                    )
                    buggy_result = execute_test_against_buggy(
                        test_code, task.buggy_implementation, track
                    )

                    fd_score = calculate_fault_detection_score(correct_result, buggy_result)
                    fault_detection_scores.append(fd_score)

                    mutation_result = run_mutation_testing(
                        test_code, task.correct_implementation, track
                    )
                    mutation_scores.append(mutation_result.mutation_score)

                    task_composite = calculate_composite_score(
                        mutation_result.mutation_score, fd_score
                    )

                    task_details.append(
                        TaskDetail(
                            task_id=task_id,
                            mutation_score=mutation_result.mutation_score,
                            fault_detection_rate=fd_score,
                            composite_score=task_composite.score,
                            passed_correct=correct_result.passed,
                            failed_buggy=not buggy_result.passed,
                        )
                    )

                except Exception as e:
                    logger.warning("Task %s failed [trace_id=%s]: %s", task_id, trace_id, e)
                    task_details.append(
                        TaskDetail(
                            task_id=task_id,
                            mutation_score=0.0,
                            fault_detection_rate=0.0,
                            composite_score=0.0,
                            passed_correct=False,
                            failed_buggy=False,
                        )
                    )
                    fault_detection_scores.append(0.0)
                    mutation_scores.append(0.0)

            fault_detection_rate = aggregate_fault_detection_scores(fault_detection_scores)
            avg_mutation_score = (
                sum(mutation_scores) / len(mutation_scores) if mutation_scores else 0.0
            )
            composite = calculate_composite_score(avg_mutation_score, fault_detection_rate)

            pass_rate = (
                sum(1 for d in task_details if d.passed_correct and d.failed_buggy)
                / len(task_details)
                if task_details
                else 0.0
            )

            output = generate_agentbeats_results(
                participant_id=participant_id,
                task_details=task_details,
                composite=composite,
                pass_rate=pass_rate,
                track=track,
            )

            total_latency = time.time() - start_time
            logger.info("Evaluation completed in %.2fs [trace_id=%s]", total_latency, trace_id)

            result_data = output.model_dump()
            result_data["trace_id"] = trace_id
            result_data["latency"] = total_latency

            artifact = new_data_artifact("agentbeats_results", result_data)

            await event_queue.enqueue_event(
                TaskArtifactUpdateEvent(
                    context_id=context.context_id or "",
                    task_id=context.task_id or "",
                    artifact=artifact,
                )
            )

            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    context_id=context.context_id or "",
                    task_id=context.task_id or "",
                    final=True,
                    status=TaskStatus(state=TaskState.completed),
                )
            )

        except Exception as e:
            logger.error("Evaluation failed [trace_id=%s]: %s", trace_id, e)

            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    context_id=context.context_id or "",
                    task_id=context.task_id or "",
                    final=True,
                    status=TaskStatus(state=TaskState.failed),
                )
            )

        finally:
            await messenger.close()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel running evaluation task.

        Args:
            context: A2A request context
            event_queue: Event queue for publishing updates
        """
        # Minimal implementation for graceful cancellation
        pass
