#!/usr/bin/env python3
"""Seed the `models` table with LLM registry entries."""

import asyncio
import os

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import create_async_engine

from shared.models.llm import Model

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://bartender:changeme@localhost:5432/bartender_ai")

SEED_MODELS = [
    {
        "name": "llama-3.3-70b-versatile",
        "provider": "groq",
        "tier": "free",
        "max_tokens": 8192,
        "is_active": True,
        "metadata": {
            "cost_per_1k_input": 0.0,  # Free tier (Groq subsidized)
            "cost_per_1k_output": 0.0,
            "avg_latency_ms": 500,
            "description": "Meta Llama 3.3 70B via Groq API",
        },
    },
    {
        "name": "claude-sonnet-4-6",
        "provider": "anthropic",
        "tier": "paid",
        "max_tokens": 4096,
        "is_active": True,
        "metadata": {
            "cost_per_1k_input": 0.003,
            "cost_per_1k_output": 0.015,
            "avg_latency_ms": 1200,
            "description": "Anthropic Claude Sonnet 4.6",
        },
    },
    {
        "name": "gpt-4.1",
        "provider": "openai",
        "tier": "paid",
        "max_tokens": 4096,
        "is_active": True,
        "metadata": {
            "cost_per_1k_input": 0.005,
            "cost_per_1k_output": 0.015,
            "avg_latency_ms": 1000,
            "description": "OpenAI GPT-4.1",
        },
    },
    {
        "name": "llama3.2",
        "provider": "ollama",
        "tier": "fallback",
        "max_tokens": 4096,
        "is_active": True,
        "metadata": {
            "cost_per_1k_input": 0.0,
            "cost_per_1k_output": 0.0,
            "avg_latency_ms": 3000,
            "description": "Local Llama 3.2 via Ollama (fallback)",
        },
    },
]


async def seed() -> None:
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        for model_data in SEED_MODELS:
            await conn.execute(
                insert(Model).values(**model_data)
                .on_conflict_do_nothing(index_elements=["name"])
            )
            print(f"Seeded model: {model_data['name']}")
    await engine.dispose()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(seed())
