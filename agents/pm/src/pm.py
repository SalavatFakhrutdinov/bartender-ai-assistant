"""PM Agent — release decision and risk assessment."""

from base_agent.agent import BaseAgent
from base_agent.llm import LLMClient
from shared.events.schemas import (
    AgentTaskAssigned,
    ReleaseApproved,
    ReleaseRejected,
)
from shared.logging import get_logger

logger = get_logger(__name__)


class PMAgent(BaseAgent):
    """Evaluates test results and makes release decisions."""

    def __init__(self):
        super().__init__(
            agent_type="PM",
            skills=[
                {"name": "release_decision", "proficiency": 0.8},
                {"name": "risk_assessment", "proficiency": 0.85},
            ],
            max_concurrent=1,
        )
        self.llm = LLMClient()

    async def handle_task(self, task: AgentTaskAssigned) -> None:
        """Evaluate QA results and make release decision."""
        event_data = task.event_data
        ticket_id = event_data.get("ticket_id", "unknown")
        overall_status = event_data.get("overall_status", "failed")
        blockers = event_data.get("blockers", [])

        logger.info("PM evaluating", ticket_id=ticket_id, status=overall_status)

        # Decision logic
        if overall_status == "passed" and not blockers:
            decision = ReleaseApproved(
                meta=task.meta,
                ticket_id=ticket_id,
                approved_by=self.agent_id,
                risk_level="low",
                notes="All tests passed. No blockers.",
            )
            logger.info("Release approved", ticket_id=ticket_id)
        else:
            decision = ReleaseRejected(
                meta=task.meta,
                ticket_id=ticket_id,
                rejected_by=self.agent_id,
                reason=f"Tests {overall_status}. Blockers: {blockers}",
                action_items=["Fix failing tests", "Re-run QA"],
                route_to="developer",
            )
            logger.info("Release rejected", ticket_id=ticket_id)

        await self.publish(decision)
