"""Topic Guardrail — lightweight rule-based off-topic detection.

Prevents general-purpose LLM abuse by rejecting non-bartending queries
before any LLM call is made. Uses keyword matching + heuristic scoring.

Target false-positive rate: <2%
"""

import re
from dataclasses import dataclass

from shared.logging import get_logger

logger = get_logger(__name__)

# ============================================================================
# Keyword Lists
# ============================================================================

WHITELIST_KEYWORDS = frozenset(
    {
        # Core bartending
        "cocktail",
        "cocktails",
        "drink",
        "drinks",
        "beverage",
        "beverages",
        "bar",
        "bartender",
        "bartending",
        "mixology",
        "mixologist",
        "recipe",
        "recipes",
        "ingredient",
        "ingredients",
        "spirit",
        "spirits",
        "liquor",
        "liqueur",
        "liqueurs",
        "gin",
        "vodka",
        "rum",
        "whiskey",
        "whisky",
        "bourbon",
        "tequila",
        "mezcal",
        "brandy",
        "cognac",
        "vermouth",
        "amaro",
        "aperitif",
        "digestif",
        "bitters",
        "syrup",
        "juice",
        "soda",
        "tonic",
        "wine",
        "beer",
        "champagne",
        "prosecco",
        # Techniques
        "shake",
        "shaken",
        "stir",
        "stirred",
        "muddle",
        "muddled",
        "strain",
        "strained",
        "build",
        "layer",
        "float",
        "rim",
        "garnish",
        "glassware",
        " coupe",
        "rocks",
        "highball",
        "martini",
        "old fashioned",
        "negroni",
        "manhattan",
        # Menu & business
        "menu",
        "menu design",
        "cocktail menu",
        "drink list",
        "pricing",
        "cost",
        "margin",
        "inventory",
        "stock",
        "bar management",
        "front of house",
        "service",
        # Flavor & chemistry
        "flavor",
        "flavour",
        "taste",
        "aroma",
        "palate",
        "finish",
        "balance",
        "sweet",
        "sour",
        "bitter",
        "umami",
        "salty",
        "citrus",
        "herbal",
        "floral",
        "spicy",
        "smoky",
        "fruity",
        "acid",
        "ph",
        "density",
        "viscosity",
        "layering",
        # Events & occasions
        "party",
        "wedding",
        "event",
        "tasting",
        "flight",
        "happy hour",
        "brunch",
        "dinner",
        "dessert",
    }
)

BLACKLIST_KEYWORDS = frozenset(
    {
        # Programming
        "python",
        "javascript",
        "java",
        "code",
        "coding",
        "program",
        "programming",
        "developer",
        "software",
        "app development",
        "debug",
        "compiler",
        "algorithm",
        "data structure",
        # Academic subjects
        "homework",
        "essay",
        "thesis",
        "dissertation",
        "exam",
        "math",
        "mathematics",
        "physics",
        "chemistry",
        "biology",
        "history",
        "geography",
        "literature",
        "philosophy",
        "quantum",
        "relativity",
        "calculus",
        "algebra",
        # General AI abuse
        "write a poem",
        "write a story",
        "write an essay",
        "solve this",
        "answer this question",
        "explain quantum",
        "explain relativity",
        "explain evolution",
        # Non-bartending professions
        "doctor",
        "lawyer",
        "engineer",
        "teacher",
        "accountant",
        "plumber",
        "electrician",
        "mechanic",
        # Malicious
        "hack",
        "exploit",
        "vulnerability",
        "bypass",
        "crack",
    }
)

# Regex patterns for common abuse patterns
ABUSE_PATTERNS = [
    re.compile(r"^(write|create|generate)\s+(me\s+)?(a\s+)?(python|code|script|program)", re.I),
    re.compile(r"^(solve|answer)\s+(this\s+)?(math|physics|equation|problem)", re.I),
    re.compile(r"^(explain|describe)\s+(quantum|relativity|string theory)", re.I),
    re.compile(r"^(write|compose)\s+(me\s+)?(an?\s+)?(essay|poem|story|email)", re.I),
    re.compile(r"^(help\s+me\s+)?(cheat|hack|exploit|bypass)", re.I),
]

# ============================================================================
# Result Types
# ============================================================================


@dataclass(frozen=True)
class GuardrailResult:
    """Result of topic guardrail evaluation."""

    allowed: bool
    score: float
    reason: str | None = None


# ============================================================================
# Guardrail Implementation
# ============================================================================


class TopicGuardrail:
    """Lightweight rule-based topic guardrail.

    Score function:
        +1 per whitelist keyword match
        -2 per blacklist keyword match
        -3 per abuse pattern match
        Threshold = 0 (must have at least one positive signal)
    """

    WHITELIST_BONUS = 1.0
    BLACKLIST_PENALTY = 2.0
    PATTERN_PENALTY = 3.0
    THRESHOLD = 0.0

    def evaluate(self, text: str) -> GuardrailResult:
        """Evaluate whether a query is bartending-relevant.

        Args:
            text: The user's query text

        Returns:
            GuardrailResult with allowed flag, score, and reason
        """
        if not text or not text.strip():
            return GuardrailResult(
                allowed=False,
                score=-10.0,
                reason="Empty query",
            )

        normalized = text.lower()
        words = set(re.findall(r"\b\w+\b", normalized))

        score = 0.0
        matched_whitelist = words & WHITELIST_KEYWORDS
        matched_blacklist = words & BLACKLIST_KEYWORDS

        score += len(matched_whitelist) * self.WHITELIST_BONUS
        score -= len(matched_blacklist) * self.BLACKLIST_PENALTY

        # Check regex patterns
        pattern_hits = []
        for pattern in ABUSE_PATTERNS:
            if pattern.search(normalized):
                score -= self.PATTERN_PENALTY
                pattern_hits.append(pattern.pattern[:30])

        allowed = score > self.THRESHOLD

        reason = None
        if not allowed:
            if matched_blacklist:
                reason = f"Detected off-topic keywords: {', '.join(sorted(matched_blacklist)[:3])}"
            elif pattern_hits:
                reason = "Detected potential abuse pattern"
            else:
                reason = "Query does not appear to be bartending-related"

        logger.info(
            "Topic guardrail evaluation",
            allowed=allowed,
            score=score,
            text_preview=text[:100],
            whitelist_hits=len(matched_whitelist),
            blacklist_hits=len(matched_blacklist),
        )

        return GuardrailResult(allowed=allowed, score=score, reason=reason)


# Singleton instance
guardrail = TopicGuardrail()


def check_topic(text: str) -> GuardrailResult:
    """Convenience function for direct guardrail evaluation."""
    return guardrail.evaluate(text)
