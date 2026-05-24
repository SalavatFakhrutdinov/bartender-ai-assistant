"""Event Correlator — tracks event chains across the swarm workflow."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from shared.logging import get_logger

logger = get_logger(__name__)


class ChainState(str, Enum):
    """States in the swarm event chain."""

    STARTED = "started"
    TICKET_CREATED = "ticket_created"
    CODE_PUSHED = "code_pushed"
    DEV_READY = "dev_ready"
    QA_SUMMARY = "qa_summary"
    RELEASE_DECIDED = "release_decided"
    COMPLETED = "completed"
    REJECTED = "rejected"


@dataclass
class EventChain:
    """Tracks a single feature-request-to-release chain."""

    correlation_id: str
    state: ChainState = ChainState.STARTED
    events: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: str | None = None


class EventCorrelator:
    """Tracks and manages event chains.

    In Phase 0, uses in-memory storage. In production, this should use Redis.
    """

    def __init__(self):
        self._chains: dict[str, EventChain] = {}

    def start_chain(self, correlation_id: str, initial_event: dict[str, Any]) -> EventChain:
        """Start tracking a new event chain."""
        chain = EventChain(
            correlation_id=correlation_id,
            events=[initial_event],
        )
        self._chains[correlation_id] = chain
        logger.info("Event chain started", correlation_id=correlation_id)
        return chain

    def add_event(self, correlation_id: str, event: dict[str, Any]) -> EventChain | None:
        """Add an event to an existing chain and update state."""
        chain = self._chains.get(correlation_id)
        if not chain:
            logger.warning("Chain not found", correlation_id=correlation_id)
            return None

        chain.events.append(event)
        chain.updated_at = datetime.now(timezone.utc)

        # Update state machine
        event_type = event.get("event_type", "")
        if event_type == "TicketCreated":
            chain.state = ChainState.TICKET_CREATED
        elif event_type == "CodePushed":
            chain.state = ChainState.CODE_PUSHED
        elif event_type == "DevReadyForQA":
            chain.state = ChainState.DEV_READY
        elif event_type == "QATestSummary":
            chain.state = ChainState.QA_SUMMARY
        elif event_type in ("ReleaseApproved", "ReleaseRejected"):
            chain.state = ChainState.RELEASE_DECIDED
            if event_type == "ReleaseApproved":
                chain.state = ChainState.COMPLETED
            else:
                chain.state = ChainState.REJECTED

        return chain

    def get_chain(self, correlation_id: str) -> EventChain | None:
        """Get a chain by correlation ID."""
        return self._chains.get(correlation_id)

    def get_all_chains(self) -> list[EventChain]:
        """Get all tracked chains."""
        return list(self._chains.values())
