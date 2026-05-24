# 🍸 Bartender AI Assistant

> **Phase 0: Foundation & Swarm Bootstrap** — A multi-agent AI development swarm building a web-based personal bartender assistant.

[![CI](https://github.com/your-org/bartender-ai-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/bartender-ai-assistant/actions)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Node](https://img.shields.io/badge/Node-20-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## What is this?

This is a **dual-system project**:

1. **The Product** — A web-based AI assistant for bartenders that creates cocktail recipes, designs menus, and optimizes bar operations using a hybrid RAG system (vector search + knowledge graph).

2. **The Builder** — A self-organizing multi-agent development swarm (Analyst, Developer, QA, PM) that builds software via an event-driven workflow, with all communication routed through NATS JetStream and surfaced via Telegram.

**Current phase:** Foundation & infrastructure bootstrap. The agent swarm skeleton is operational, the database schema is complete, and all services are containerized.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         HUMAN LAYER (Telegram)                       │
│                  Human PM sends /analyze "feature"                   │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
┌──────────────────────────────────▼───────────────────────────────────┐
│                    TELEGRAM GATEWAY SERVICE                          │
│              Normalizes Telegram messages → NATS events              │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
┌──────────────────────────────────▼───────────────────────────────────┐
│                    NATS JETSTREAM EVENT BUS                          │
│   tickets.* │ code.* │ qa.* │ release.* │ human.* │ agent.*          │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
┌──────────────────────────────────▼───────────────────────────────────┐
│                 AGENT SWARM ORCHESTRATOR                             │
│    Skill Registry │ Task Router │ Correlator │ Health Monitor       │
└──────────┬──────────────┬──────────────┬─────────────────────────────┘
           │              │              │
    ┌──────▼──────┐ ┌────▼──────┐ ┌────▼──────┐
    │  Analyst    │ │ Developer │ │  QA/PM    │
    │   Agent     │ │   Agent   │ │  Agents   │
    └─────────────┘ └───────────┘ └───────────┘
```

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 15, Tailwind CSS, Zustand, Socket.io |
| **API** | FastAPI, Pydantic v2, SQLAlchemy 2.0 |
| **Database** | PostgreSQL 16 + pgvector |
| **Cache** | Redis 7 |
| **Vector DB** | Qdrant |
| **Event Bus** | NATS JetStream |
| **Object Storage** | MinIO |
| **Agents** | Python 3.12, Anthropic SDK (Claude) |
| **Reverse Proxy** | Traefik v3 |
| **Infra** | Docker Compose |

---

## Project Structure

```
.
├── apps/
│   ├── api/              # FastAPI backend (chat, auth, subscriptions, support)
│   └── web/              # Next.js 15 frontend (chat UI, admin dashboard)
├── agents/
│   ├── _base/            # Shared BaseAgent class (heartbeat, NATS, LLM stub)
│   ├── orchestrator/     # Skill registry, task router, correlator, health monitor
│   ├── telegram-gateway/ # Telegram ↔ NATS bidirectional bridge
│   ├── analyst/          # Requirement analysis → ticket creation
│   ├── developer/        # TDD implementation → code push
│   ├── qa/               # Test execution → quality summary
│   └── pm/               # Release decision → approve/reject
├── packages/
│   ├── shared-py/        # Event schemas, models, NATS client, config, logging
│   └── shared-ts/        # TypeScript types for frontend
├── infra/
│   ├── nats/             # JetStream server configuration
│   └── qdrant/           # Vector DB configuration
├── scripts/
│   ├── setup.sh          # One-time dev environment setup
│   ├── seed_models.py    # Seed LLM registry
│   └── seed_quests.py    # Seed gamification quests
├── docker-compose.yml    # Full local dev stack
└── justfile              # Task runner (make replacement)
```

---

## Implemented Features

### ✅ Phase 0 — Foundation & Swarm Bootstrap

#### Infrastructure
- [x] Docker Compose local dev environment (PostgreSQL, Redis, Qdrant, NATS, MinIO, Traefik)
- [x] Dockerfiles for all services and agents
- [x] `justfile` task runner with 15+ commands

#### Shared Packages
- [x] **Event schemas** — 15+ typed Pydantic v2 events (`TicketCreated`, `CodePushed`, `QATestSummary`, etc.)
- [x] **NATS JetStream client** — Async wrapper with typed publish/subscribe, stream initialization
- [x] **SQLAlchemy models** — All 15 database tables (users, cocktails, feedback, support tickets, quests, etc.)
- [x] **Configuration** — Pydantic-Settings with env var loading
- [x] **Structured logging** — JSON logs via structlog
- [x] **Health checks** — Standardized health endpoint format

#### Database
- [x] Alembic async migrations (single initial migration for all tables)
- [x] `models` table with seed data (Llama 3.3 70B, Claude Sonnet, GPT-4.1, Ollama)
- [x] `quests` table with 6 gamification quest definitions
- [x] pgvector extension for embeddings

#### API Service
- [x] FastAPI app factory with lifespan management
- [x] Health endpoint with Redis/NATS dependency checks
- [x] Clerk webhook stub (`/auth/webhook/clerk`)
- [x] CORS, auth, and rate-limit middleware (stubs for Phase 1)
- [x] **Topic Guardrail** — Rule-based off-topic detection with whitelist/blacklist heuristic

#### Agent Swarm
- [x] **BaseAgent** — Abstract class with heartbeat loop (30s), NATS subscribe, task handling, retry logic
- [x] **Orchestrator** — Skill registry, task router with load-based scoring, event chain correlator, health monitor with circuit breaker
- [x] **Telegram Gateway** — Bidirectional bridge: Telegram commands ↔ NATS events
- [x] **Analyst Agent** — Decomposes `/analyze` into `TicketCreated` events
- [x] **Developer Agent** — Stub: code push → `DevReadyForQA`
- [x] **QA Agent** — Stub: test execution → `QATestSummary`
- [x] **PM Agent** — Evaluates QA results → `ReleaseApproved`/`ReleaseRejected`

#### Frontend
- [x] Next.js 15 app with Tailwind CSS
- [x] Chat UI skeleton with message bubbles and input
- [x] Zustand store for chat state
- [x] Socket.io client stub

#### CI/CD
- [x] GitHub Actions workflow (Python lint/test, Node.js lint, security scan, Docker build)

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- [Just](https://github.com/casey/just) task runner (`brew install just`)
- [Poetry](https://python-poetry.org/) (`pip install poetry`)
- [pnpm](https://pnpm.io/) (`npm install -g pnpm`)

### Setup

```bash
# Clone and enter repository
git clone <repo-url>
cd bartender-ai-assistant

# One-time setup (creates .env, installs dependencies)
./scripts/setup.sh

# Or manual setup:
cp .env.example .env
# Edit .env with your API keys
```

### Development

```bash
# Start all infrastructure services
just dev-up

# Run database migrations
just migrate

# Seed reference data
just seed

# Run tests
just test

# Run linters
just lint

# View logs
just logs

# Stop everything
just dev-down
```

### Services (after `just dev-up`)

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Next.js app |
| API | http://localhost:8000 | FastAPI backend |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Orchestrator | http://localhost:8001 | Agent swarm admin |
| Traefik Dashboard | http://localhost:8080 | Reverse proxy UI |
| NATS Monitor | http://localhost:8222 | JetStream stats |
| Qdrant | http://localhost:6333 | Vector DB |
| MinIO Console | http://localhost:9001 | Object storage |

---

## Agent Swarm Usage

### Via Telegram

1. Add your bot to a Telegram group
2. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`
3. Send commands:
   - `/start` — Show available commands
   - `/analyze <feature description>` — Create a development ticket
   - `/status` — Show agent swarm status

### Event Flow

```
Human: /analyze "Add a cost calculator command"
  → Telegram Gateway
    → NATS: human.command
      → Orchestrator
        → Skill Registry: finds Analyst
          → NATS: agent.task_assigned
            → Analyst Agent
              → NATS: tickets.created
                → Orchestrator
                  → Skill Registry: finds Developer
                    → NATS: agent.task_assigned
                      → Developer Agent
                        → NATS: code.push → dev.ready_for_qa
                          → Orchestrator
                            → Skill Registry: finds QA
                              → NATS: agent.task_assigned
                                → QA Agent
                                  → NATS: qa.test_summary
                                    → Orchestrator
                                      → Skill Registry: finds PM
                                        → NATS: agent.task_assigned
                                          → PM Agent
                                            → NATS: release.approved/rejected
                                              → Telegram Gateway
                                                → Human: "🚀 Release Approved"
```

---

## Testing

```bash
# All tests
just test

# Python only
just test-python

# Node.js only
just test-node
```

| Layer | Tool | Target Coverage |
|-------|------|-----------------|
| Unit (Python) | pytest + pytest-asyncio | 90% |
| Unit (TS) | Vitest | 80% |
| Integration | pytest + testcontainers | 85% |
| Security | bandit, semgrep | — |

---

## Roadmap

| Phase | Timeline | Goal |
|-------|----------|------|
| **0** | Weeks 1–2 ✅ | Foundation: swarm skeleton, event bus, DB schema |
| **1** | Weeks 3–5 | Core Chat MVP: Socket.io streaming, RAG, LLM Gateway v1 |
| **2** | Weeks 6–8 | Paid Tier: Stripe, Claude/GPT routing, bar context, knowledge graph |
| **3** | Weeks 9–11 | Feedback Loop: taste surveys, physical validation, MLOps pipeline |
| **4** | Weeks 12–13 | Production: monitoring, UAT, load testing, security audit |
| **5** | Post-MVP | Scale: Kubernetes, auto-scaling agents, business tier |

See [`docs/system-blueprint-v2.0.md`](docs/system-blueprint-v2.0.md) for the full technical specification.

---

## Contributing

This project uses a **multi-agent development workflow**:

1. Human PM sends feature requests via Telegram `/analyze`
2. Analyst agent creates structured tickets
3. Developer agent implements with TDD
4. QA agent runs test matrix
5. PM agent approves or rejects releases

For manual contributions, follow [Conventional Commits](https://www.conventionalcommits.org/) and ensure CI passes.

---

## License

MIT
