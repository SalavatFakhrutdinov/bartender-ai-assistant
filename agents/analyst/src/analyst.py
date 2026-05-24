"""Analyst Agent — requirement decomposition and ticket creation."""

from base_agent.agent import BaseAgent
from base_agent.llm import LLMClient
from base_agent.memory import AgentMemory
from shared.events.schemas import (
    AgentTaskAssigned,
    TicketCreated,
    ClarificationNeeded,
)
from shared.logging import get_logger

logger = get_logger(__name__)


class AnalystAgent(BaseAgent):
    """Analyzes feature requests and creates structured tickets."""

    def __init__(self):
        super().__init__(
            agent_type="Analyst",
            skills=[
                {"name": "requirements_analysis", "proficiency": 0.9},
                {"name": "ticket_creation", "proficiency": 0.95},
                {"name": "ambiguity_resolution", "proficiency": 0.85},
            ],
            max_concurrent=2,
        )
        self.llm = LLMClient()
        self.memory = AgentMemory()

    async def handle_task(self, task: AgentTaskAssigned) -> None:
        """Process an assigned task."""
        event_data = task.event_data
        command = event_data.get("command", "")
        args = event_data.get("args", "")

        logger.info("Analyst processing", command=command, args=args)

        if command == "analyze":
            await self._create_ticket(args, task)
        else:
            logger.warning("Unknown command", command=command)

    async def _create_ticket(self, description: str, task: AgentTaskAssigned) -> None:
        """Decompose a feature request into a structured ticket."""
        # Use LLM to analyze (stub in Phase 0)
        analysis = await self.llm.complete(
            prompt=f"Analyze this feature request and create a ticket: {description}",
            system="You are a requirements analyst. Decompose requests into clear tickets.",
        )

        # Create ticket event
        ticket = TicketCreated(
            meta=task.meta,
            ticket_id=f"T-{task.task_id[:8]}",
            title=description[:80],
            description=description,
            acceptance_criteria=[
                "Implementation satisfies the feature request",
                "Tests cover the new functionality",
                "Documentation is updated if needed",
            ],
            tags=["feature"],
            complexity="M",
            assigned_to_skill="tdd_implementation",
        )

        await self.publish(ticket)
        logger.info("Ticket created", ticket_id=ticket.ticket_id, title=ticket.title)

        # Store in memory
        await self.memory.remember(
            event_type="ticket_creation",
            context=description,
            outcome=ticket.ticket_id,
        )
