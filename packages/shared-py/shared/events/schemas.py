"""Pydantic v2 event schemas for all inter-service communication.

Every event published to NATS JetStream must conform to one of these schemas.
The `Event` base class provides common metadata (timestamp, correlation_id,
event_id) that all events share.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class EventMeta(BaseModel):
    """Common metadata attached to every event."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source: str = Field(
        default="unknown", description="Service or agent that emitted the event"
    )
    version: str = Field(default="1.0", description="Schema version")


class Event(BaseModel):
    """Base class for all events."""

    meta: EventMeta = Field(default_factory=EventMeta)

    def nats_subject(self) -> str:
        """Return the NATS subject for this event type."""
        from shared.events.subjects import EVENT_TO_SUBJECT

        return EVENT_TO_SUBJECT.get(self.__class__.__name__, "unknown")


# =============================================================================
# Ticket Events
# =============================================================================


class TicketCreated(Event):
    """Emitted when an Analyst decomposes a feature request into a ticket."""

    ticket_id: str
    title: str
    description: str
    acceptance_criteria: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    complexity: str = Field(default="M", pattern="^(S|M|L|XL)$")
    assigned_to_skill: str = Field(default="tdd_implementation")
    estimated_hours: float | None = None


class TicketUpdated(Event):
    """Emitted when a ticket is modified (status change, reassignment, etc.)."""

    ticket_id: str
    updates: dict[str, Any]
    reason: str | None = None


class TicketClosed(Event):
    """Emitted when a ticket is closed (merged, cancelled, or abandoned)."""

    ticket_id: str
    resolution: str = Field(pattern="^(merged|cancelled|abandoned)$")
    final_sha: str | None = None


# =============================================================================
# Code Events
# =============================================================================


class CodePushed(Event):
    """Emitted when a Developer agent pushes code to a branch."""

    ticket_id: str
    branch: str
    commit_sha: str
    commit_message: str
    files_changed: list[str] = Field(default_factory=list)
    diff_lines: int = 0


class PRReady(Event):
    """Emitted when a Developer opens a PR for review."""

    ticket_id: str
    pr_number: int | None = None
    branch: str
    target_branch: str = "main"


class DevReadyForQA(Event):
    """Emitted when CI passes and code is ready for QA."""

    ticket_id: str
    branch: str
    commit_sha: str
    ci_status: str = Field(pattern="^(passed|failed|skipped)$")
    test_count: int = 0
    coverage_percent: float = 0.0


# =============================================================================
# QA Events
# =============================================================================


class QATestSummary(Event):
    """Emitted by QA agent after running the full test matrix."""

    ticket_id: str
    branch: str
    commit_sha: str
    overall_status: str = Field(pattern="^(passed|failed|warning)$")
    unit_tests: dict[str, Any] = Field(default_factory=dict)
    integration_tests: dict[str, Any] = Field(default_factory=dict)
    security_scan: dict[str, Any] = Field(default_factory=dict)
    coverage_delta: float = 0.0
    total_coverage: float = 0.0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    duration_seconds: float = 0.0


class QABlocker(Event):
    """Emitted when QA finds a critical failure that blocks release."""

    ticket_id: str
    severity: str = Field(pattern="^(critical|high|medium)$")
    description: str
    reproduction_steps: str | None = None
    logs: str | None = None


# =============================================================================
# UAT Events
# =============================================================================


class UATReady(Event):
    """Emitted when QA passes and staging URL is ready for human UAT."""

    ticket_id: str
    staging_url: str
    deployment_sha: str
    test_plan: str | None = None


class UATFeedback(Event):
    """Emitted when a human tester provides UAT feedback via Telegram."""

    ticket_id: str
    tester_id: str
    feedback: str
    approved: bool = False
    issues: list[str] = Field(default_factory=list)


# =============================================================================
# Release Events
# =============================================================================


class ReleaseApproved(Event):
    """Emitted by PM agent when release is approved."""

    ticket_id: str
    approved_by: str
    risk_level: str = Field(pattern="^(low|medium|high)$")
    notes: str | None = None


class ReleaseRejected(Event):
    """Emitted by PM agent when release is rejected."""

    ticket_id: str
    rejected_by: str
    reason: str
    action_items: list[str] = Field(default_factory=list)
    route_to: str = Field(pattern="^(analyst|developer)$")


class ReleaseDeployed(Event):
    """Emitted after successful production deployment."""

    ticket_id: str
    deployment_sha: str
    environment: str = "production"


# =============================================================================
# Human Input Events
# =============================================================================


class HumanMessage(Event):
    """Emitted when a human sends a message via Telegram (non-command)."""

    user_id: str
    username: str | None = None
    message_text: str
    chat_id: str
    thread_id: str | None = None
    reply_to: str | None = None


class HumanCommand(Event):
    """Emitted when a human sends a command via Telegram (e.g., /analyze)."""

    user_id: str
    username: str | None = None
    command: str
    args: str = ""
    chat_id: str
    thread_id: str | None = None


class HumanUATResponse(Event):
    """Emitted when a human responds to a UAT prompt in Telegram."""

    ticket_id: str
    user_id: str
    response_text: str
    approved: bool | None = None


# =============================================================================
# Agent Telemetry Events
# =============================================================================


class AgentHeartbeat(Event):
    """Periodic heartbeat from every agent."""

    agent_id: str
    agent_type: str
    skills: list[dict[str, Any]] = Field(default_factory=list)
    current_load: int = 0
    max_concurrent: int = 1
    status: str = Field(
        default="healthy", pattern="^(healthy|busy|degraded|unhealthy)$"
    )
    version: str = "0.1.0"


class AgentTaskAssigned(Event):
    """Emitted by Orchestrator when a task is assigned to an agent."""

    task_id: str
    agent_id: str
    event_type: str
    event_data: dict[str, Any] = Field(default_factory=dict)
    deadline: datetime | None = None
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")


class AgentError(Event):
    """Emitted when an agent encounters an unrecoverable error."""

    agent_id: str
    task_id: str | None = None
    error_type: str
    error_message: str
    retry_count: int = 0
    max_retries: int = 3
    fatal: bool = False


# =============================================================================
# Memory Events
# =============================================================================


class MemoryEpisode(Event):
    """Emitted when an agent stores an episode in shared memory."""

    agent_id: str
    episode_type: str = Field(pattern="^(decision|success|failure|insight)$")
    context: str
    outcome: str
    embedding: list[float] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryQuery(Event):
    """Emitted when an agent queries shared memory."""

    agent_id: str
    query: str
    query_embedding: list[float] | None = None
    top_k: int = 5
    filters: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Support Events
# =============================================================================


class SupportTicketCreated(Event):
    """Emitted when a user submits a support inquiry."""

    ticket_id: str
    user_id: str
    category: str = Field(pattern="^(billing|technical|feature_request|bug)$")
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    subject: str | None = None
    body: str
    user_tier: str = "free"
    user_context: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Clarification Events
# =============================================================================


class ClarificationNeeded(Event):
    """Emitted by Analyst when requirements are ambiguous."""

    original_message: str
    ambiguity_reason: str
    suggested_questions: list[str] = Field(default_factory=list)
    route_to_human: bool = True
