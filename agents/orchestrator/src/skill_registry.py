"""Skill Registry — maintains agent manifests and skill-to-agent mappings."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AgentManifest:
    """Agent registration manifest."""

    agent_id: str
    agent_type: str
    skills: list[dict[str, Any]] = field(default_factory=list)
    max_concurrent: int = 1
    current_load: int = 0
    version: str = "0.1.0"
    last_heartbeat: datetime | None = None


class SkillRegistry:
    """In-memory registry of agent skills and availability.

    Maps skills to agents and maintains load/health state.
    """

    def __init__(self):
        self._agents: dict[str, AgentManifest] = {}
        self._skill_index: dict[str, set[str]] = {}  # skill -> agent_ids

    def register(self, manifest: AgentManifest) -> None:
        """Register or update an agent manifest."""
        self._agents[manifest.agent_id] = manifest

        # Update skill index
        for skill_info in manifest.skills:
            skill_name = skill_info["name"]
            if skill_name not in self._skill_index:
                self._skill_index[skill_name] = set()
            self._skill_index[skill_name].add(manifest.agent_id)

        logger.info(
            "Agent registered",
            agent_id=manifest.agent_id,
            agent_type=manifest.agent_type,
            skills=[s["name"] for s in manifest.skills],
        )

    def deregister(self, agent_id: str) -> None:
        """Remove an agent from the registry."""
        if agent_id not in self._agents:
            return

        manifest = self._agents.pop(agent_id)
        for skill_info in manifest.skills:
            skill_name = skill_info["name"]
            if skill_name in self._skill_index:
                self._skill_index[skill_name].discard(agent_id)

        logger.info("Agent deregistered", agent_id=agent_id)

    def update_heartbeat(self, agent_id: str) -> None:
        """Update last heartbeat timestamp for an agent."""
        if agent_id in self._agents:
            self._agents[agent_id].last_heartbeat = datetime.now(timezone.utc)

    def update_load(self, agent_id: str, current_load: int) -> None:
        """Update current load for an agent."""
        if agent_id in self._agents:
            self._agents[agent_id].current_load = current_load

    def find_agents_for_skills(
        self, required_skills: list[str]
    ) -> list[AgentManifest]:
        """Find agents that have ALL the required skills.

        Returns agents sorted by: load (asc), proficiency (desc),
        heartbeat recency (desc).
        """
        candidate_ids: set[str] | None = None
        for skill in required_skills:
            agents_with_skill = self._skill_index.get(skill, set())
            if candidate_ids is None:
                candidate_ids = set(agents_with_skill)
            else:
                candidate_ids &= agents_with_skill

        if not candidate_ids:
            return []

        candidates = [self._agents[aid] for aid in candidate_ids if aid in self._agents]

        # Score and sort
        def score(agent: AgentManifest) -> tuple:
            # Lower load = better
            load_score = agent.current_load / max(agent.max_concurrent, 1)
            # More recent heartbeat = better (if available)
            hb_age = 0.0
            if agent.last_heartbeat:
                hb_age = (datetime.now(timezone.utc) - agent.last_heartbeat).total_seconds()
            return (load_score, hb_age)

        candidates.sort(key=score)
        return candidates

    def get_all_agents(self) -> list[AgentManifest]:
        """Return all registered agents."""
        return list(self._agents.values())

    def get_agent(self, agent_id: str) -> AgentManifest | None:
        """Get a specific agent by ID."""
        return self._agents.get(agent_id)
