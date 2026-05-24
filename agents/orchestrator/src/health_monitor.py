"""Health Monitor — tracks agent heartbeats and circuit breaker logic."""

from dataclasses import dataclass
from datetime import datetime, timezone

from shared.logging import get_logger
from agents.orchestrator.src.skill_registry import SkillRegistry

logger = get_logger(__name__)

HEARTBEAT_TIMEOUT_SECONDS = 90
MAX_MISSED_HEARTBEATS = 3


@dataclass
class AgentHealth:
    """Health status for a single agent."""

    agent_id: str
    status: str = "healthy"
    last_heartbeat: datetime | None = None
    missed_heartbeats: int = 0


class HealthMonitor:
    """Monitors agent health via heartbeat events.

    - Tracks last heartbeat per agent
    - Flags agents as degraded/unhealthy after missed heartbeats
    - Circuit breaker: pauses task routing for failing agents
    """

    def __init__(self, registry: SkillRegistry):
        self.registry = registry
        self._health: dict[str, AgentHealth] = {}

    def record_heartbeat(self, agent_id: str) -> None:
        """Record a heartbeat from an agent."""
        if agent_id not in self._health:
            self._health[agent_id] = AgentHealth(agent_id=agent_id)

        health = self._health[agent_id]
        health.last_heartbeat = datetime.now(timezone.utc)
        health.missed_heartbeats = 0
        health.status = "healthy"

        self.registry.update_heartbeat(agent_id)

    def check_all_agents(self) -> list[AgentHealth]:
        """Check health of all registered agents."""
        now = datetime.now(timezone.utc)
        results = []

        for agent in self.registry.get_all_agents():
            health = self._health.get(agent.agent_id)
            if not health or not health.last_heartbeat:
                # No heartbeats yet
                continue

            age = (now - health.last_heartbeat).total_seconds()
            if age > HEARTBEAT_TIMEOUT_SECONDS:
                health.missed_heartbeats += 1
                if health.missed_heartbeats >= MAX_MISSED_HEARTBEATS:
                    health.status = "unhealthy"
                    logger.warning(
                        "Agent marked unhealthy",
                        agent_id=agent.agent_id,
                        missed=health.missed_heartbeats,
                    )
                else:
                    health.status = "degraded"

            results.append(health)

        return results

    def get_unhealthy_agents(self) -> list[str]:
        """Return IDs of agents that should not receive tasks."""
        return [
            h.agent_id for h in self._health.values()
            if h.status == "unhealthy"
        ]
