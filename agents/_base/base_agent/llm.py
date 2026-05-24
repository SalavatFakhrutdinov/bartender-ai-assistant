"""LLM client wrapper for agent reasoning."""

import os
from typing import Any

from shared.logging import get_logger

logger = get_logger(__name__)


class LLMClient:
    """Lightweight LLM client for agent reasoning.

    In Phase 0, this is a stub. Full Anthropic SDK integration in Phase 1.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.token_budget = 4000
        self.tokens_used = 0

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 1024,
    ) -> str:
        """Generate a completion (stub for Phase 0).

        Returns a deterministic stub response for development and testing.
        """
        logger.debug("LLM completion requested", prompt_preview=prompt[:100])

        # Stub: return a simple response based on prompt keywords
        if "ticket" in prompt.lower():
            return "I have analyzed the request and created ticket T-001."
        elif "test" in prompt.lower():
            return "Tests passed: 15/15. Coverage: 87%."
        elif "release" in prompt.lower():
            return "Release approved. Risk level: low."
        elif "code" in prompt.lower():
            return "Code implemented and committed."
        else:
            return "Task completed successfully."

    def check_budget(self, estimated_tokens: int) -> bool:
        """Check if there's enough token budget remaining."""
        return (self.tokens_used + estimated_tokens) <= self.token_budget
