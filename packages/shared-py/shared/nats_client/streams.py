"""NATS JetStream stream configuration definitions.

These configurations match the blueprint's event bus schema:
https://docs.nats.io/nats-concepts/jetstream/streams
"""

from enum import Enum


class StreamRetention(str, Enum):
    """NATS JetStream retention policies."""

    LIMITS = "limits"
    INTEREST = "interest"
    WORK_QUEUE = "workqueue"


class StreamConfig:
    """Configuration for a NATS JetStream stream."""

    def __init__(
        self,
        name: str,
        subjects: list[str],
        retention: StreamRetention = StreamRetention.LIMITS,
        max_msgs: int = -1,
        max_bytes: int = -1,
        max_age_seconds: int | None = None,
        max_msg_size: int = -1,
        storage: str = "file",
        replicas: int = 1,
        discard: str = "old",
        duplicates_window_seconds: int = 120,
    ):
        self.name = name
        self.subjects = subjects
        self.retention = retention
        self.max_msgs = max_msgs
        self.max_bytes = max_bytes
        self.max_age_seconds = max_age_seconds
        self.max_msg_size = max_msg_size
        self.storage = storage
        self.replicas = replicas
        self.discard = discard
        self.duplicates_window_seconds = duplicates_window_seconds

    def to_js_config(self) -> dict:
        """Convert to NATS-py JetStream add_stream config dict."""
        config: dict = {
            "name": self.name,
            "subjects": self.subjects,
            "retention": self.retention.value,
            "storage": self.storage,
            "replicas": self.replicas,
            "discard": self.discard,
            "duplicate_window": self.duplicates_window_seconds,
        }
        if self.max_msgs > 0:
            config["max_msgs"] = self.max_msgs
        if self.max_bytes > 0:
            config["max_bytes"] = self.max_bytes
        if self.max_age_seconds is not None:
            config["max_age"] = self.max_age_seconds
        if self.max_msg_size > 0:
            config["max_msg_size"] = self.max_msg_size
        return config


# =============================================================================
# Stream Definitions (matching blueprint)
# =============================================================================

TICKETS_STREAM = StreamConfig(
    name="tickets",
    subjects=["tickets.*"],
    retention=StreamRetention.WORK_QUEUE,
    max_msgs=10000,
    max_age_seconds=7 * 24 * 3600,  # 7 days
)

CODE_STREAM = StreamConfig(
    name="code",
    subjects=["code.*", "dev.*"],
    retention=StreamRetention.LIMITS,
    max_msgs=1000,
    max_age_seconds=30 * 24 * 3600,  # 30 days
)

QA_STREAM = StreamConfig(
    name="qa",
    subjects=["qa.*", "uat.*"],
    retention=StreamRetention.WORK_QUEUE,
    max_msgs=5000,
    max_age_seconds=7 * 24 * 3600,
)

RELEASE_STREAM = StreamConfig(
    name="release",
    subjects=["release.*"],
    retention=StreamRetention.LIMITS,
    max_msgs=500,
    max_age_seconds=90 * 24 * 3600,  # 90 days
)

HUMAN_STREAM = StreamConfig(
    name="human",
    subjects=["human.*"],
    retention=StreamRetention.LIMITS,
    max_msgs=5000,
    max_age_seconds=30 * 24 * 3600,
)

AGENT_STREAM = StreamConfig(
    name="agent",
    subjects=["agent.*"],
    retention=StreamRetention.LIMITS,
    max_msgs=10000,
    max_age_seconds=7 * 24 * 3600,
)

MEMORY_STREAM = StreamConfig(
    name="memory",
    subjects=["memory.*"],
    retention=StreamRetention.LIMITS,
    max_msgs=50000,
    max_age_seconds=365 * 24 * 3600,  # 1 year
)

SUPPORT_STREAM = StreamConfig(
    name="support",
    subjects=["support.*"],
    retention=StreamRetention.WORK_QUEUE,
    max_msgs=5000,
    max_age_seconds=30 * 24 * 3600,
)

CLARIFICATION_STREAM = StreamConfig(
    name="clarification",
    subjects=["clarification.*"],
    retention=StreamRetention.WORK_QUEUE,
    max_msgs=1000,
    max_age_seconds=7 * 24 * 3600,
)

ALL_STREAMS: list[StreamConfig] = [
    TICKETS_STREAM,
    CODE_STREAM,
    QA_STREAM,
    RELEASE_STREAM,
    HUMAN_STREAM,
    AGENT_STREAM,
    MEMORY_STREAM,
    SUPPORT_STREAM,
    CLARIFICATION_STREAM,
]
