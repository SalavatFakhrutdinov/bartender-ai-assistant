"""SQLAlchemy 2.0 declarative models for the Bartender AI Assistant.

All models use async-compatible patterns and are shared across the API
service, agents, and background workers.
"""

from shared.models.base import Base, TimestampMixin, UUIDMixin
from shared.models.user import User, Subscription
from shared.models.chat import ChatSession, Message
from shared.models.cocktail import Cocktail, CocktailFeedback
from shared.models.support import SupportTicket
from shared.models.gamification import Quest, UserQuestProgress
from shared.models.mlops import MLExperiment, ValidationFailure
from shared.models.llm import Model, LLMUsage, UserBarContext, PendingCocktail

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDMixin",
    "User",
    "Subscription",
    "ChatSession",
    "Message",
    "Cocktail",
    "CocktailFeedback",
    "SupportTicket",
    "Quest",
    "UserQuestProgress",
    "MLExperiment",
    "ValidationFailure",
    "Model",
    "LLMUsage",
    "UserBarContext",
    "PendingCocktail",
]
