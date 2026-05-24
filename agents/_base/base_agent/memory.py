"""Agent Memory — episodic memory using Qdrant + short-term Redis cache."""

from typing import Any

from shared.logging import get_logger

logger = get_logger(__name__)


class AgentMemory:
    """Agent episodic memory interface.

    In Phase 0, uses in-memory storage. Full Qdrant integration in Phase 1.
    """

    def __init__(self):
        self._episodes: list[dict[str, Any]] = []

    async def remember(
        self,
        event_type: str,
        context: str,
        outcome: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store an episode in memory."""
        episode = {
            "type": event_type,
            "context": context,
            "outcome": outcome,
            "metadata": metadata or {},
        }
        self._episodes.append(episode)
        logger.debug("Episode stored", event_type=event_type)

    async def recall(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        """Retrieve relevant episodes (stub: simple keyword match)."""
        query_words = set(query.lower().split())
        scored = []
        for ep in self._episodes:
            text = f"{ep['context']} {ep['outcome']}".lower()
            score = len(query_words & set(text.split()))
            if score > 0:
                scored.append((score, ep))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [ep for _, ep in scored[:k]]
