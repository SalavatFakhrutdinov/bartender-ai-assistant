"""NATS event → Telegram message formatting."""

from shared.events.schemas import (
    Event,
    TicketCreated,
    QATestSummary,
    ReleaseApproved,
    ReleaseRejected,
    AgentError,
)
from shared.logging import get_logger

logger = get_logger(__name__)


class Surfacer:
    """Formats NATS events as human-readable Telegram messages."""

    def event_to_telegram(self, event: Event) -> str:
        """Convert an event to a Telegram message string."""
        event_type = type(event).__name__

        if isinstance(event, TicketCreated):
            return self._format_ticket(event)
        elif isinstance(event, QATestSummary):
            return self._format_qa(event)
        elif isinstance(event, ReleaseApproved):
            return self._format_approval(event)
        elif isinstance(event, ReleaseRejected):
            return self._format_rejection(event)
        elif isinstance(event, AgentError):
            return self._format_error(event)
        else:
            return f"📡 *{event_type}*\n```{event.model_dump_json(indent=2)[:400]}```"

    def _format_ticket(self, event: TicketCreated) -> str:
        return (
            f"🎫 *New Ticket: {event.ticket_id}*\n"
            f"*{event.title}*\n"
            f"Complexity: {event.complexity}\n"
            f"Assigned to: {event.assigned_to_skill}\n"
            f"Acceptance criteria: {len(event.acceptance_criteria)} items"
        )

    def _format_qa(self, event: QATestSummary) -> str:
        emoji = "✅" if event.overall_status == "passed" else "⚠️"
        return (
            f"{emoji} *QA Results: {event.ticket_id}*\n"
            f"Status: {event.overall_status}\n"
            f"Coverage: {event.total_coverage:.1f}%\n"
            f"Duration: {event.duration_seconds:.0f}s\n"
            f"Blockers: {len(event.blockers)}"
        )

    def _format_approval(self, event: ReleaseApproved) -> str:
        return (
            f"🚀 *Release Approved: {event.ticket_id}*\n"
            f"Risk level: {event.risk_level}\n"
            f"Approved by: {event.approved_by}"
        )

    def _format_rejection(self, event: ReleaseRejected) -> str:
        return (
            f"❌ *Release Rejected: {event.ticket_id}*\n"
            f"Reason: {event.reason}\n"
            f"Routed to: {event.route_to}\n"
            f"Action items: {len(event.action_items)}"
        )

    def _format_error(self, event: AgentError) -> str:
        return (
            f"🔥 *Agent Error: {event.agent_id}*\n"
            f"Type: {event.error_type}\n"
            f"Message: {event.error_message[:200]}"
        )
