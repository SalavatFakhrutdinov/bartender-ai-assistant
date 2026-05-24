"""Agent Swarm Orchestrator — FastAPI app + NATS consumer."""

import asyncio

from fastapi import FastAPI

from shared.logging import configure_logging, get_logger
from shared.config import get_settings
from shared.nats_client import NatsClient
from shared.events.schemas import (
    Event,
    AgentHeartbeat,
    HumanCommand,
    TicketCreated,
    DevReadyForQA,
    QATestSummary,
)
from shared.events.subjects import (
    HUMAN_COMMAND,
    AGENT_HEARTBEAT,
    TICKETS_CREATED,
    DEV_READY_FOR_QA,
    QA_TEST_SUMMARY,
)
from shared.health import health_endpoint

from agents.orchestrator.src.skill_registry import SkillRegistry, AgentManifest
from agents.orchestrator.src.task_router import TaskRouter
from agents.orchestrator.src.correlator import EventCorrelator
from agents.orchestrator.src.health_monitor import HealthMonitor

logger = get_logger(__name__)

# Global state (simplified for Phase 0)
registry = SkillRegistry()
router = TaskRouter(registry)
correlator = EventCorrelator()
health_monitor = HealthMonitor(registry)


async def handle_human_command(event: Event) -> None:
    """Handle incoming human command events."""
    assert isinstance(event, HumanCommand)
    logger.info("Received human command", command=event.command, args=event.args)

    # Start a new event chain
    correlator.start_chain(
        event.meta.correlation_id,
        {"event_type": "HumanCommand", "command": event.command},
    )

    # Route to Analyst agent
    agent = router.select_agent(event)
    if agent:
        task = router.create_task(event, agent.agent_id)
        logger.info("Routed to agent", agent_id=agent.agent_id, task_id=task.task_id)
        # TODO: Publish task to NATS


async def handle_heartbeat(event: Event) -> None:
    """Handle agent heartbeat events."""
    assert isinstance(event, AgentHeartbeat)
    health_monitor.record_heartbeat(event.agent_id)
    registry.update_load(event.agent_id, event.current_load)


async def handle_ticket_created(event: Event) -> None:
    """Handle ticket created events — route to Developer."""
    assert isinstance(event, TicketCreated)
    correlator.add_event(
        event.meta.correlation_id,
        {"event_type": "TicketCreated", "ticket_id": event.ticket_id},
    )
    agent = router.select_agent(event)
    if agent:
        task = router.create_task(event, agent.agent_id)
        logger.info("Routed ticket to developer", agent_id=agent.agent_id)


async def handle_dev_ready(event: Event) -> None:
    """Handle dev ready for QA events — route to QA."""
    assert isinstance(event, DevReadyForQA)
    correlator.add_event(
        event.meta.correlation_id,
        {"event_type": "DevReadyForQA", "ticket_id": event.ticket_id},
    )
    agent = router.select_agent(event)
    if agent:
        task = router.create_task(event, agent.agent_id)


async def handle_qa_summary(event: Event) -> None:
    """Handle QA test summary events — route to PM."""
    assert isinstance(event, QATestSummary)
    correlator.add_event(
        event.meta.correlation_id,
        {"event_type": "QATestSummary", "ticket_id": event.ticket_id},
    )
    agent = router.select_agent(event)
    if agent:
        task = router.create_task(event, agent.agent_id)


async def start_nats_consumer() -> None:
    """Start NATS consumer for all relevant subjects."""
    settings = get_settings()
    client = NatsClient(nats_url=settings.nats.url)
    await client.connect()

    await client.subscribe(HUMAN_COMMAND, handle_human_command, durable="orchestrator")
    await client.subscribe(AGENT_HEARTBEAT, handle_heartbeat, durable="orchestrator-hb")
    await client.subscribe(TICKETS_CREATED, handle_ticket_created, durable="orchestrator-tickets")
    await client.subscribe(DEV_READY_FOR_QA, handle_dev_ready, durable="orchestrator-qa")
    await client.subscribe(QA_TEST_SUMMARY, handle_qa_summary, durable="orchestrator-pm")

    logger.info("NATS consumer started")


app = FastAPI(title="Agent Swarm Orchestrator", version="0.1.0")


@app.on_event("startup")
async def startup() -> None:
    configure_logging()
    logger.info("Orchestrator starting")
    # Start NATS consumer in background
    asyncio.create_task(start_nats_consumer())
    # Register some stub agents for testing
    registry.register(AgentManifest(
        agent_id="analyst-1",
        agent_type="Analyst",
        skills=[{"name": "requirements_analysis", "proficiency": 0.9}],
    ))
    registry.register(AgentManifest(
        agent_id="developer-1",
        agent_type="Developer",
        skills=[{"name": "tdd_implementation", "proficiency": 0.85}],
    ))
    registry.register(AgentManifest(
        agent_id="qa-1",
        agent_type="QA",
        skills=[{"name": "test_execution", "proficiency": 0.9}],
    ))
    registry.register(AgentManifest(
        agent_id="pm-1",
        agent_type="PM",
        skills=[{"name": "release_decision", "proficiency": 0.8}],
    ))


@app.get("/health")
async def health() -> dict:
    agents = registry.get_all_agents()
    health_checks = health_monitor.check_all_agents()
    return {
        "status": "ok",
        "agents_registered": len(agents),
        "agents_healthy": len([h for h in health_checks if h.status == "healthy"]),
    }


@app.get("/agents")
async def list_agents() -> list[dict]:
    return [
        {
            "agent_id": a.agent_id,
            "agent_type": a.agent_type,
            "skills": a.skills,
            "current_load": a.current_load,
            "last_heartbeat": a.last_heartbeat.isoformat() if a.last_heartbeat else None,
        }
        for a in registry.get_all_agents()
    ]


@app.get("/chains/{correlation_id}")
async def get_chain(correlation_id: str) -> dict | None:
    chain = correlator.get_chain(correlation_id)
    if not chain:
        return None
    return {
        "correlation_id": chain.correlation_id,
        "state": chain.state.value,
        "event_count": len(chain.events),
        "created_at": chain.created_at.isoformat(),
        "updated_at": chain.updated_at.isoformat(),
        "events": chain.events,
    }


@app.post("/agents/{agent_id}/restart")
async def restart_agent(agent_id: str) -> dict:
    """Request restart of an agent (stub for Phase 0)."""
    logger.info("Agent restart requested", agent_id=agent_id)
    return {"status": "restart_requested", "agent_id": agent_id}
