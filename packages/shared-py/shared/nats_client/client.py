"""Async NATS JetStream client wrapper with typed publish/subscribe."""

import json
from collections.abc import Callable, Coroutine
from typing import Any

import nats
from nats.aio.client import Client as NatsConnection
from nats.js import JetStreamContext
from nats.js.api import ConsumerConfig

from shared.events.schemas import Event
from shared.logging.logger import get_logger
from shared.nats_client.streams import ALL_STREAMS

logger = get_logger(__name__)

SubscriptionCallback = Callable[[Event], Coroutine[Any, Any, None]]


class NatsClient:
    """High-level async NATS JetStream client.

    Handles connection management, stream initialization, typed event
    publishing, and durable subscription setup.
    """

    def __init__(self, nats_url: str = "nats://localhost:4222"):
        self.nats_url = nats_url
        self._nc: NatsConnection | None = None
        self._js: JetStreamContext | None = None

    @property
    def is_connected(self) -> bool:
        return self._nc is not None and self._nc.is_connected

    async def connect(self) -> None:
        """Establish connection to NATS server and initialize JetStream."""
        logger.info("Connecting to NATS", url=self.nats_url)
        self._nc = await nats.connect(self.nats_url)
        self._js = self._nc.jetstream()
        logger.info("Connected to NATS")

    async def disconnect(self) -> None:
        """Gracefully close NATS connection."""
        if self._nc:
            await self._nc.close()
            self._nc = None
            self._js = None
            logger.info("Disconnected from NATS")

    async def initialize_streams(self) -> None:
        """Create or update all JetStream streams defined in streams.py."""
        if not self._js:
            raise RuntimeError("NATS not connected. Call connect() first.")

        for stream in ALL_STREAMS:
            try:
                await self._js.add_stream(**stream.to_js_config())
                logger.info("Created stream", stream=stream.name)
            except nats.js.errors.StreamNameAlreadyInUseError:  # type: ignore[attr-defined]
                logger.debug("Stream already exists", stream=stream.name)
            except Exception as e:
                logger.error(
                    "Failed to create stream", stream=stream.name, error=str(e)
                )
                raise

    async def publish(self, event: Event) -> None:
        """Publish a typed event to its NATS subject.

        Args:
            event: Typed event instance (must inherit from Event)
        """
        if not self._js:
            raise RuntimeError("NATS not connected. Call connect() first.")

        subject = event.nats_subject()
        payload = event.model_dump_json().encode()

        ack = await self._js.publish(subject, payload)
        logger.debug(
            "Published event",
            subject=subject,
            event_type=type(event).__name__,
            event_id=event.meta.event_id,
            seq=ack.seq,
        )

    async def subscribe(
        self,
        subject: str,
        callback: SubscriptionCallback,
        durable: str | None = None,
        deliver_group: str | None = None,
        queue: str | None = None,
    ) -> Any:
        """Subscribe to a NATS subject with a typed callback.

        Args:
            subject: NATS subject pattern (e.g., "tickets.created" or "tickets.*")
            callback: Async function that receives deserialized Event instances
            durable: Durable consumer name for resume capability
            deliver_group: Consumer group for load-balanced processing
            queue: Queue group name (deprecated, use deliver_group)

        Returns:
            NATS subscription object
        """
        if not self._js:
            raise RuntimeError("NATS not connected. Call connect() first.")

        async def _wrapper(msg: Any) -> None:
            try:
                data = json.loads(msg.data.decode())
                # Determine event type from subject and reconstruct
                event = self._deserialize_event(data)
                await callback(event)
                await msg.ack()
            except Exception as e:
                logger.error(
                    "Message processing failed",
                    subject=subject,
                    error=str(e),
                    exc_info=True,
                )
                await msg.nak()

        consumer_config = None
        if durable or deliver_group:
            consumer_config = ConsumerConfig(
                durable_name=durable,
                deliver_group=deliver_group,
            )

        sub = await self._js.subscribe(
            subject,
            cb=_wrapper,
            config=consumer_config,
            queue=queue or deliver_group,
        )
        logger.info(
            "Subscribed to subject",
            subject=subject,
            durable=durable,
            deliver_group=deliver_group,
        )
        return sub

    def _deserialize_event(self, data: dict[str, Any]) -> Event:
        """Deserialize raw message data into the appropriate Event subclass.

        Uses a simple dispatch based on the presence of type-specific fields.
        For production, consider a formal type registry.
        """
        # Import all event types for dispatch
        from shared.events import schemas as evt

        # Simple field-based dispatch
        if "ticket_id" in data and "title" in data:
            return evt.TicketCreated(**data)
        elif "commit_sha" in data and "diff_lines" in data:
            return evt.CodePushed(**data)
        elif "ci_status" in data:
            return evt.DevReadyForQA(**data)
        elif "overall_status" in data and "coverage_delta" in data:
            return evt.QATestSummary(**data)
        elif "severity" in data and "reproduction_steps" in data:
            return evt.QABlocker(**data)
        elif "staging_url" in data:
            return evt.UATReady(**data)
        elif "tester_id" in data:
            return evt.UATFeedback(**data)
        elif "approved_by" in data:
            return evt.ReleaseApproved(**data)
        elif "rejected_by" in data:
            return evt.ReleaseRejected(**data)
        elif "message_text" in data:
            return evt.HumanMessage(**data)
        elif "command" in data:
            return evt.HumanCommand(**data)
        elif "agent_id" in data and "status" in data:
            return evt.AgentHeartbeat(**data)
        elif "task_id" in data and "agent_id" in data and "event_type" in data:
            return evt.AgentTaskAssigned(**data)
        elif "error_type" in data:
            return evt.AgentError(**data)
        elif "episode_type" in data:
            return evt.MemoryEpisode(**data)
        elif "query" in data and "top_k" in data:
            return evt.MemoryQuery(**data)
        elif "category" in data and "user_tier" in data:
            return evt.SupportTicketCreated(**data)
        elif "ambiguity_reason" in data:
            return evt.ClarificationNeeded(**data)
        else:
            # Fallback: try generic Event
            return Event(**data)
