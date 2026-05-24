# Bartender AI Assistant — Agent Guide

## Project Overview

Multi-agent swarm system for building and operating a bartender AI assistant.

## Architecture

- **Monorepo**: `packages/` (shared code), `apps/` (web + api), `agents/` (swarm)
- **Event Bus**: NATS JetStream
- **Shared Protocol**: `packages/shared-py` for Python, `packages/shared-ts` for TypeScript

## Quick Start

```bash
# 1. Setup (one-time)
chmod +x scripts/setup.sh
./scripts/setup.sh

# 2. Start infrastructure
just dev-up

# 3. Run migrations
just migrate

# 4. Seed data
just seed

# 5. Run tests
just test
```

## Development Commands

```bash
just up          # Start all services
just down        # Stop all services
just build       # Build Docker images
just test        # Run all tests
just lint        # Run all linters
just migrate     # Run Alembic migrations
just seed        # Seed reference data
```

## Adding a New Agent

1. Create `agents/<name>/src/` directory
2. Extend `BaseAgent` from `agents/_base/base_agent/`
3. Implement `handle_task()` method
4. Define skills in `__init__()`
5. Add Dockerfile and pyproject.toml
6. Register in `docker-compose.yml`

## Event Conventions

- All events inherit from `Event` base class
- Use `meta.correlation_id` to track chains
- Publish via `self.publish(event)` in agents
- Subjects defined in `shared/events/subjects.py`

## Testing

- Python: `pytest` with `pytest-asyncio`
- Coverage gate: 85%
- Mock NATS for unit tests
- Use `testcontainers` for integration tests

## Phase 0 Status

✅ Monorepo structure
✅ Docker Compose infrastructure
✅ Shared packages (Python + TypeScript)
✅ Database schema + migrations
✅ API service foundation
✅ Topic Guardrail
✅ Orchestrator (skill registry, task router, correlator, health monitor)
✅ Telegram Gateway
✅ 4 core agents (Analyst, Developer, QA, PM)
✅ Frontend skeleton
⏳ Full JWT validation (Phase 1)
⏳ Socket.io streaming (Phase 1)
⏳ RAG pipeline (Phase 1)
⏳ LLM Gateway with real providers (Phase 1)
