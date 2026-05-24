#!/usr/bin/env python3
"""Seed gamification quest definitions."""

import asyncio
import os

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import create_async_engine

from shared.models.gamification import Quest

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://bartender:changeme@localhost:5432/bartender_ai")

SEED_QUESTS = [
    {
        "name": "First Feedback",
        "description": "Submit your first cocktail taste survey",
        "quest_type": "feedback",
        "target_count": 1,
        "reward_days": 3,
        "is_active": True,
    },
    {
        "name": "Feedback Streak",
        "description": "Submit 5 detailed feedback surveys",
        "quest_type": "feedback",
        "target_count": 5,
        "reward_days": 7,
        "is_active": True,
    },
    {
        "name": "Recipe Validator",
        "description": "Validate 2 AI-generated recipes for physical plausibility",
        "quest_type": "validation",
        "target_count": 2,
        "reward_days": 7,
        "is_active": True,
    },
    {
        "name": "Ingredient Tagger",
        "description": "Tag 5 ingredients with flavor families",
        "quest_type": "tagging",
        "target_count": 5,
        "reward_days": 3,
        "is_active": True,
    },
    {
        "name": "Bar Context Setup",
        "description": "Complete your bar concept and inventory",
        "quest_type": "onboarding",
        "target_count": 1,
        "reward_days": 7,
        "is_active": True,
    },
    {
        "name": "Menu Designer",
        "description": "Generate and save your first menu design",
        "quest_type": "onboarding",
        "target_count": 1,
        "reward_days": 7,
        "is_active": True,
    },
]


async def seed() -> None:
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        for quest_data in SEED_QUESTS:
            await conn.execute(
                insert(Quest).values(**quest_data)
                .on_conflict_do_nothing(index_elements=["name"])
            )
            print(f"Seeded quest: {quest_data['name']}")
    await engine.dispose()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(seed())
