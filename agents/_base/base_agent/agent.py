"""BaseAgent — abstract base class for all swarm agents.

Provides:
- NATS connection and heartbeat loop
- Skill manifest registration
- Task subscription and handling
- Retry logic
"""

import asyncio
import os
from abc import ABC, abstractmethod
from typing import Any

from shared.logging import get_logger
from shared.config import get_settings
from shared.nats_client import NatsClient
from shared.events.schemas import (
    Event,
    AgentHeartbeat,
    AgentTaskAssigned,
    AgentError,
)
from shared.events.subjects import AGENT_HEARTBEAT, AGENT_TASK_ASSIGNED, AGENT_ERROR

logger = get_logger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all swarm agents.

    Subclasses must implement `handle_task()` and define their skills.
    """

    def __init__(
        self,
        agent_id: str | None = None,
        agent_type: str | None = None,
        skills: list[dict[str, Any]] | None = None,
        max_concurrent: int = 1,
    ):
        self.agent_id = agent_id or os.environ.get("AGENT_ID", "unknown")
        self.agent_type = agent_type or os.environ.get("AGENT_TYPE", "Unknown")
        self.skills = skills or []
        self.max_concurrent = max_concurrent
        self.current_load = 0
        self._nats: NatsClient | None = None
        self._heartbeat_task: asyncio.Task | None = None
        self._running = False

    @property
    def manifest(self) -> dict[str, Any]:
        """Agent registration manifest."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "skills": self.skills,
            "max_concurrent": self.max_concurrent,
            "current_load": self.current_load,
            "version": "0.1.0",
        }

    async def start(self) -> None:
        """Start the agent: connect to NATS, register, begin heartbeat."""
        settings = get_settings()
        self._nats = NatsClient(nats_url=settings.nats.url)
        await self._nats.connect()

        self._running = True

        # Subscribe to task assignments
        await self._nats.subscribe(
            AGENT_TASK_ASSIGNED,
            self._on_task_assigned,
            durable=f"{self.agent_id}-tasks",
            deliver_group=f"{self.agent_type.lower()}-pool",
        )

        # Start heartbeat loop
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        logger.info(
            "Agent started",
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            skills=[s["name"] for s in self.skills],
        )

    async def stop(self) -> None:
        """Graceful shutdown."""
        self._running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        if self._nats:
            await self._nats.disconnect()
        logger.info("Agent stopped", agent_id=self.agent_id)

    async def _heartbeat_loop(self) -> None:
        """Publish heartbeat every 30 seconds."""
        settings = get_settings()
        interval = settings.agent.heartbeat_interval_seconds

        while self._running:
            try:
                heartbeat = AgentHeartbeat(
                    agent_id=self.agent_id,
                    agent_type=self.agent_type,
                    skills=self.skills,
                    current_load=self.current_load,
                    max_concurrent=self.max_concurrent,
                    status="healthy" if self.current_load < self.max_concurrent else "busy",
                )
                if self._nats:
                    await self._nats.publish(heartbeat)
            except Exception as e:
                logger.error("Heartbeat failed", error=str(e))
            await asyncio.sleep(interval)

    async def _on_task_assigned(self, event: Event) -> None:
        """Handle incoming task assignment."""
        assert isinstance(event, AgentTaskAssigned)

        if event.agent_id != self.agent_id:
            return  # Not for us

        logger.info(
            "Task received",
            task_id=event.task_id,
            event_type=event.event_type,
        )

        self.current_load += 1
        try:
            await self.handle_task(event)
        except Exception as e:
            logger.error("Task failed", task_id=event.task_id, error=str(e))
            error_event = AgentError(
                agent_id=self.agent_id,
                task_id=event.task_id,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            if self._nats:
                await self._nats.publish(error_event)
        finally:
            self.current_load -= 1

    @abstractmethod
    async def handle_task(self, task: AgentTaskAssigned) -> None:
        """Process an assigned task. Must be implemented by subclasses."""
        ...

    async def publish(self, event: Event) -> None:
        """Publish an event to NATS."""
        if self._nats:
            await self._nats.publish(event)
