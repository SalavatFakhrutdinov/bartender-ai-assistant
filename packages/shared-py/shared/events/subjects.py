"""NATS JetStream subject constants.

All inter-service and inter-agent communication happens via typed events
on these subjects. This module is the single source of truth for subject
names, preventing typos and drift between services.
"""

from enum import Enum


class Subject(str, Enum):
    """NATS subject enumeration."""

    # Ticket lifecycle
    TICKETS_CREATED = "tickets.created"
    TICKETS_UPDATED = "tickets.updated"
    TICKETS_CLOSED = "tickets.closed"

    # Code events
    CODE_PUSH = "code.push"
    PR_READY = "code.pr.ready"

    # QA events
    DEV_READY_FOR_QA = "dev.ready_for_qa"
    QA_TEST_SUMMARY = "qa.test_summary"
    QA_BLOCKER = "qa.blocker"

    # UAT events
    UAT_READY = "uat.ready"
    UAT_FEEDBACK = "uat.feedback"

    # Release events
    RELEASE_APPROVED = "release.approved"
    RELEASE_REJECTED = "release.rejected"
    RELEASE_DEPLOYED = "release.deployed"

    # Human input
    HUMAN_MESSAGE = "human.message"
    HUMAN_COMMAND = "human.command"
    HUMAN_UAT_RESPONSE = "human.uat_response"

    # Agent telemetry
    AGENT_HEARTBEAT = "agent.heartbeat"
    AGENT_TASK_ASSIGNED = "agent.task_assigned"
    AGENT_ERROR = "agent.error"

    # Memory operations
    MEMORY_EPISODE = "memory.episode"
    MEMORY_QUERY = "memory.query"

    # Support
    SUPPORT_TICKET_CREATED = "support.ticket_created"

    # Clarification
    CLARIFICATION_NEEDED = "clarification.needed"


# Convenience exports (backward-compatible string constants)
TICKETS_CREATED = Subject.TICKETS_CREATED.value
TICKETS_UPDATED = Subject.TICKETS_UPDATED.value
TICKETS_CLOSED = Subject.TICKETS_CLOSED.value
CODE_PUSH = Subject.CODE_PUSH.value
PR_READY = Subject.PR_READY.value
DEV_READY_FOR_QA = Subject.DEV_READY_FOR_QA.value
QA_TEST_SUMMARY = Subject.QA_TEST_SUMMARY.value
QA_BLOCKER = Subject.QA_BLOCKER.value
UAT_READY = Subject.UAT_READY.value
UAT_FEEDBACK = Subject.UAT_FEEDBACK.value
RELEASE_APPROVED = Subject.RELEASE_APPROVED.value
RELEASE_REJECTED = Subject.RELEASE_REJECTED.value
RELEASE_DEPLOYED = Subject.RELEASE_DEPLOYED.value
HUMAN_MESSAGE = Subject.HUMAN_MESSAGE.value
HUMAN_COMMAND = Subject.HUMAN_COMMAND.value
HUMAN_UAT_RESPONSE = Subject.HUMAN_UAT_RESPONSE.value
AGENT_HEARTBEAT = Subject.AGENT_HEARTBEAT.value
AGENT_TASK_ASSIGNED = Subject.AGENT_TASK_ASSIGNED.value
AGENT_ERROR = Subject.AGENT_ERROR.value
MEMORY_EPISODE = Subject.MEMORY_EPISODE.value
MEMORY_QUERY = Subject.MEMORY_QUERY.value
SUPPORT_TICKET_CREATED = Subject.SUPPORT_TICKET_CREATED.value
CLARIFICATION_NEEDED = Subject.CLARIFICATION_NEEDED.value

# Mapping from event type (class name) to NATS subject
EVENT_TO_SUBJECT: dict[str, str] = {
    "TicketCreated": TICKETS_CREATED,
    "TicketUpdated": TICKETS_UPDATED,
    "TicketClosed": TICKETS_CLOSED,
    "CodePushed": CODE_PUSH,
    "PRReady": PR_READY,
    "DevReadyForQA": DEV_READY_FOR_QA,
    "QATestSummary": QA_TEST_SUMMARY,
    "QABlocker": QA_BLOCKER,
    "UATReady": UAT_READY,
    "UATFeedback": UAT_FEEDBACK,
    "ReleaseApproved": RELEASE_APPROVED,
    "ReleaseRejected": RELEASE_REJECTED,
    "ReleaseDeployed": RELEASE_DEPLOYED,
    "HumanMessage": HUMAN_MESSAGE,
    "HumanCommand": HUMAN_COMMAND,
    "HumanUATResponse": HUMAN_UAT_RESPONSE,
    "AgentHeartbeat": AGENT_HEARTBEAT,
    "AgentTaskAssigned": AGENT_TASK_ASSIGNED,
    "AgentError": AGENT_ERROR,
    "MemoryEpisode": MEMORY_EPISODE,
    "MemoryQuery": MEMORY_QUERY,
    "SupportTicketCreated": SUPPORT_TICKET_CREATED,
    "ClarificationNeeded": CLARIFICATION_NEEDED,
}
