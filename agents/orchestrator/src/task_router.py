"""Task Router — resolves events to skills and dispatches to best agent."""

from typing import Any

from shared.events.schemas import Event, AgentTaskAssigned
from shared.logging import get_logger
from agents.orchestrator.src.skill_registry import SkillRegistry, AgentManifest

logger = get_logger(__name__)

# Event type → required skills mapping
EVENT_SKILL_MAP: dict[str, list[str]] = {
    "HumanCommand": ["requirements_analysis"],
    "TicketCreated": ["tdd_implementation"],
    "DevReadyForQA": ["test_execution"],
    "QATestSummary": ["release_decision"],
    "ReleaseApproved": ["deployment"],
    "ClarificationNeeded": ["stakeholder_communication"],
}


class TaskRouter:
    """Routes incoming events to the best available agent based on skills."""

    def __init__(self, registry: SkillRegistry):
        self.registry = registry

    def resolve_skills(self, event: Event) -> list[str]:
        """Determine required skills for an event."""
        event_type = type(event).__name__
        return EVENT_SKILL_MAP.get(event_type, ["general"])

    def select_agent(self, event: Event) -> AgentManifest | None:
        """Select the best agent for handling an event."""
        required_skills = self.resolve_skills(event)
        candidates = self.registry.find_agents_for_skills(required_skills)

        if not candidates:
            logger.warning(
                "No agents available for event",
                event_type=type(event).__name__,
                required_skills=required_skills,
            )
            return None

        best = candidates[0]
        logger.info(
            "Selected agent for task",
            agent_id=best.agent_id,
            event_type=type(event).__name__,
            skills=required_skills,
        )
        return best

    def create_task(self, event: Event, agent_id: str) -> AgentTaskAssigned:
        """Create a task assignment event."""
        return AgentTaskAssigned(
            meta=event.meta,  # Preserve correlation
            task_id=event.meta.event_id,
            agent_id=agent_id,
            event_type=type(event).__name__,
            event_data=event.model_dump(),
        )
