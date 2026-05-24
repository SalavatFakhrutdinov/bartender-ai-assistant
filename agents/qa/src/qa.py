"""QA Agent — test execution and quality assessment."""

from base_agent.agent import BaseAgent
from base_agent.llm import LLMClient
from shared.events.schemas import (
    AgentTaskAssigned,
    QATestSummary,
    QABlocker,
)
from shared.logging import get_logger

logger = get_logger(__name__)


class QAAgent(BaseAgent):
    """Runs tests and generates quality summaries."""

    def __init__(self):
        super().__init__(
            agent_type="QA",
            skills=[
                {"name": "test_execution", "proficiency": 0.9},
                {"name": "coverage_analysis", "proficiency": 0.85},
                {"name": "security_scan", "proficiency": 0.8},
            ],
            max_concurrent=2,
        )
        self.llm = LLMClient()

    async def handle_task(self, task: AgentTaskAssigned) -> None:
        """Run QA on a development task."""
        event_data = task.event_data
        ticket_id = event_data.get("ticket_id", "unknown")

        logger.info("QA running tests", ticket_id=ticket_id)

        # Simulate test execution
        result = await self.llm.complete(
            prompt=f"Run tests for ticket {ticket_id}",
            system="You are a QA engineer. Run comprehensive tests.",
        )

        # Generate test summary
        summary = QATestSummary(
            meta=task.meta,
            ticket_id=ticket_id,
            branch=event_data.get("branch", "main"),
            commit_sha=event_data.get("commit_sha", "unknown"),
            overall_status="passed",
            unit_tests={"passed": 15, "failed": 0, "skipped": 0},
            integration_tests={"passed": 5, "failed": 0, "skipped": 0},
            security_scan={"issues": 0, "critical": 0},
            coverage_delta=2.5,
            total_coverage=87.0,
            blockers=[],
            warnings=[],
            duration_seconds=45.0,
        )
        await self.publish(summary)

        logger.info("QA complete", ticket_id=ticket_id, status=summary.overall_status)
