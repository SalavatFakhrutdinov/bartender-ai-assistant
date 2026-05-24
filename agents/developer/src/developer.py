"""Developer Agent — TDD implementation and git operations."""

from base_agent.agent import BaseAgent
from base_agent.llm import LLMClient
from shared.events.schemas import (
    AgentTaskAssigned,
    CodePushed,
    DevReadyForQA,
)
from shared.logging import get_logger

logger = get_logger(__name__)


class DeveloperAgent(BaseAgent):
    """Implements features following TDD principles."""

    def __init__(self):
        super().__init__(
            agent_type="Developer",
            skills=[
                {"name": "tdd_implementation", "proficiency": 0.85},
                {"name": "code_review", "proficiency": 0.8},
                {"name": "test_writing", "proficiency": 0.9},
            ],
            max_concurrent=2,
        )
        self.llm = LLMClient()

    async def handle_task(self, task: AgentTaskAssigned) -> None:
        """Process a development task."""
        event_data = task.event_data
        ticket_id = event_data.get("ticket_id", "unknown")

        logger.info("Developer implementing", ticket_id=ticket_id)

        # Stub implementation: simulate coding
        implementation = await self.llm.complete(
            prompt=f"Implement ticket {ticket_id}",
            system="You are a developer. Write clean, tested code.",
        )

        # Simulate code push
        code_push = CodePushed(
            meta=task.meta,
            ticket_id=ticket_id,
            branch=f"feature/{ticket_id}",
            commit_sha="abc1234",
            commit_message=f"feat: implement {ticket_id}",
            files_changed=["src/main.py", "tests/test_main.py"],
            diff_lines=42,
        )
        await self.publish(code_push)

        # Signal ready for QA
        dev_ready = DevReadyForQA(
            meta=task.meta,
            ticket_id=ticket_id,
            branch=f"feature/{ticket_id}",
            commit_sha="abc1234",
            ci_status="passed",
            test_count=5,
            coverage_percent=87.0,
        )
        await self.publish(dev_ready)

        logger.info("Developer done", ticket_id=ticket_id)
