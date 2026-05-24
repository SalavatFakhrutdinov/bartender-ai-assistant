# Technical Specification & Design Document
## Bartender AI Assistant — Full System Blueprint
**Version:** 2.0 | **Date:** 2026-05-22 | **Status:** Draft for Review

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Part 0 — Multi-Agent Development System](#part-0--multi-agent-development-system)
3. [Part 1 — Target Application: Bartender AI Assistant](#part-1--target-application-bartender-ai-assistant)
4. [Part 2 — Known Challenges & Solutions](#part-2--known-challenges--solutions)
5. [Technology Stack](#technology-stack)
6. [Data Models](#data-models)
7. [Implementation Roadmap](#implementation-roadmap)
8. [Risks & Trade-offs](#risks--trade-offs)

---

## Executive Summary

This document is the authoritative blueprint for two interconnected systems:

1. **The Builder** — A self-organizing multi-agent AI development swarm (Analyst, Developer, QA/Tester, Project Manager, plus auxiliary agents) that builds and ships software via a feature-branch/TDD/CI-CD workflow, with all human-agent and agent-agent communication routed through an event-driven message bus and surfaced via Telegram.
2. **The Product** — A web-based personal AI assistant for bartenders, with tiered subscriptions, a hybrid RAG-backed knowledge base combining vector search and structured knowledge graphs, a feedback-driven taste metric with an MLOps fine-tuning pipeline, and a physical realizability validation engine.

**Key architectural upgrade over v1.0:** The agent system has been re-architected from four isolated Telegram bots into a **swarm-capable, event-driven agent mesh** with a central orchestrator, shared memory, skill registry, and self-healing capabilities. This enables parallel task execution, dynamic agent spawning, cross-agent learning, and resilient human-in-the-loop workflows.

---

---

# PART 0 — MULTI-AGENT DEVELOPMENT SYSTEM

## 0.1 Design Philosophy: From Bots to Swarm

The v1.0 architecture treated each agent as an independent Telegram bot with point-to-point webhook communication. While functional, this design lacks:
- **Parallelism:** Agents cannot work on the same ticket simultaneously.
- **Resilience:** No automatic recovery if an agent crashes mid-task.
- **Scalability:** Adding new agent types requires rewiring the webhook dispatcher.
- **Collective Intelligence:** Agents cannot learn from each other's past decisions.

The v2.0 swarm architecture solves these by introducing:
1. **Agent Swarm Orchestrator** — central coordinator for lifecycle, routing, and state.
2. **Event Bus (NATS JetStream)** — durable, ordered, replayable messaging backbone.
3. **Shared Agent Memory (Vector + Graph)** — episodic memory of past decisions, failures, and successes.
4. **Skill Registry** — dynamic capability discovery; tasks route to agents by skill, not by name.
5. **Health Monitor & Self-Healer** — watches agent liveness, restarts, and circuit-breaks failing agents.

---

## 0.2 Agent Roles, Skills & Responsibilities

Each agent is a stateless worker container that boots with a system prompt, skill manifest, and API credentials. The Orchestrator assigns tasks based on skill matching.

### Analyst
- **Skills:** `requirements_analysis`, `ticket_creation`, `ambiguity_resolution`, `domain_modeling`
- **Trigger:** `feature_request` event on the event bus (from human PM via Telegram, or from PM agent via bus).
- **Inputs:** Raw user story, PM directive, bug report, or `rejected_ticket` event with annotations.
- **Outputs:**
  - `ticket.created` event with structured ticket JSON.
  - `clarification_needed` event if requirements are ambiguous (routed to human PM on Telegram).
- **Behaviors:**
  - Decomposes epics into atomic, testable tickets (Given/When/Then acceptance criteria).
  - Tags tickets: `feature`, `bug`, `chore`, `spike`, `security`, `refactor`.
  - Assigns estimated complexity (S/M/L/XL) using historical velocity data from Agent Memory.
  - Proactively cross-references past similar tickets in Agent Memory to avoid duplicate analysis.
- **Parallel Capability:** Can spawn `Analyst-Sub` agents for parallel analysis of independent ticket sub-components.

### Developer
- **Skills:** `tdd_implementation`, `code_review`, `refactoring`, `test_writing`, `docs_update`
- **Trigger:** `ticket.assigned` event with `assignee_skill: tdd_implementation`.
- **Inputs:** Ticket JSON, codebase access (via GitHub API), agent memory of similar past implementations.
- **Outputs:**
  - Commits on `dev` branch (or `feature/<ticket_id>`).
  - `code.push` event.
  - `dev.ready_for_qa` event when CI passes.
- **Behaviors:**
  - Works exclusively on `dev` or feature branches; never touches `main`.
  - Follows strict TDD: red → green → refactor. Commit sequence must show failing test first.
  - Uses Agent Memory to look up "how did we solve X last time?" before implementation.
  - Small commits enforced by pre-commit hook (<200 lines diff); larger changes require a `spike` ticket first.
  - Can request `pair_programming` event to collaborate with another Developer agent instance on complex tasks.
- **Parallel Capability:** Can spawn `Developer-Test` sub-agent to write tests in parallel while `Developer-Impl` writes implementation.

### QA / Tester
- **Skills:** `test_execution`, `coverage_analysis`, `security_scan`, `uat_coordination`, `regression_detection`
- **Trigger:** `dev.ready_for_qa` event.
- **Inputs:** `dev` branch SHA, ticket acceptance criteria, previous test reports from Agent Memory.
- **Outputs:**
  - Formal `qa.test_summary` event (JSON + human-readable).
  - `qa.blocker` event if critical failures found.
  - `uat.ready` event with staging URL posted to Telegram.
- **Behaviors:**
  - Runs full test matrix: unit, integration, e2e, security scan (bandit, semgrep), dependency audit.
  - Uses differential coverage (compares to `main` baseline); reports delta, not just absolute.
  - Regression detection: compares current output against golden snapshots stored in Agent Memory.
  - Can spawn parallel `QA-Sub` agents for different test categories (security, performance, accessibility).
  - Synthesizes human UAT feedback from Telegram thread into structured `uat.feedback` events.

### Project Manager (PM)
- **Skills:** `release_decision`, `sprint_planning`, `velocity_tracking`, `risk_assessment`, `stakeholder_communication`
- **Trigger:** `qa.test_summary` event.
- **Inputs:** Test summary, ticket backlog state, sprint goals, risk register from Agent Memory.
- **Outputs:**
  - `release.approved` → triggers Developer merge + deployment.
  - `release.rejected` → routes back to Analyst (requirement issue) or Developer (code issue) with annotated action items.
  - `sprint.digest` → weekly velocity and burn-down posted to Telegram.
- **Behaviors:**
  - Evaluates test summary against risk tolerance matrix (e.g., security findings = automatic reject).
  - Maintains velocity log and sprint burndown in Agent Memory.
  - Can escalate to human stakeholders via Telegram for high-impact decisions.

### Auxiliary Agents (Swarm-Spawned on Demand)

| Agent | Skill | Spawned By | Purpose |
|-------|-------|------------|---------|
| **Security Auditor** | `security_audit` | Developer (pre-push) or QA | Deep static analysis, dependency vulnerability scan, secrets leak detection |
| **Docs Writer** | `documentation` | Developer | Auto-generates API docs, README updates, ADRs |
| **Migration Bot** | `db_migration` | Developer | Generates Alembic/SQL migrations from model changes |
| **Performance Profiler** | `perf_analysis` | QA | Runs load tests, profiles hot paths, reports latency regressions |
| **Revert Bot** | `emergency_revert` | PM (or auto-triggered by monitor) | Instantly reverts `main` to last known good SHA if production error spike detected |
| **Knowledge Curator** | `kb_curation` | Analyst | Maintains Agent Memory vector index, prunes stale context, summarizes long threads |

---

## 0.3 Swarm Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         HUMAN LAYER (Telegram Group)                         │
│    Human PM ──┬── Human Bartender (UAT) ──┬── Human DevOps ──┬── Stakeholders│
│               │                             │                  │               │
│               ▼                             ▼                  ▼               │
│    ┌─────────────────────────────────────────────────────────────────────┐   │
│    │              TELEGRAM GATEWAY SERVICE (FastAPI)                     │   │
│    │   • Normalizes human messages into `human.*` events                 │   │
│    │   • Surfaces agent events as human-readable Telegram messages       │   │
│    │   • Thread-aware: maintains mapping between Telegram thread IDs     │   │
│    │     and event correlation IDs                                       │   │
│    └────────────────────────┬────────────────────────────────────────────┘   │
│                             │                                                │
│                             ▼                                                │
│    ┌─────────────────────────────────────────────────────────────────────┐   │
│    │              EVENT BUS — NATS JetStream                             │   │
│    │   Topics: `tickets.*`, `code.*`, `qa.*`, `release.*`, `human.*`     │   │
│    │   • Durable streams with replay capability                          │   │
│    │   • Consumer groups for load-balanced agent pools                   │   │
│    │   • Exactly-once processing for critical events (ticket creation)   │   │
│    └────────────────────────┬────────────────────────────────────────────┘   │
│                             │                                                │
│                             ▼                                                │
│    ┌─────────────────────────────────────────────────────────────────────┐   │
│    │              AGENT SWARM ORCHESTRATOR                               │   │
│    │   • Skill Registry: dynamic lookup of which agents can do what      │   │
│    │   • Task Router: publishes tasks to NATS topics based on skill      │   │
│    │   • Lifecycle Manager: starts/stops agent containers via Docker API │   │
│    │   • Load Balancer: distributes tasks across agent replica pools     │   │
│    │   • Correlator: tracks event chains (ticket → code → qa → release)  │   │
│    └──────────┬──────────────┬──────────────┬─────────────────────────────┘   │
│               │              │              │                                  │
│               ▼              ▼              ▼                                  │
│    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                         │
│    │   Analyst    │ │  Developer   │ │   QA/Tester  │  ... (auxiliary agents) │
│    │   Pool (1-3) │ │   Pool (1-5) │ │   Pool (1-3) │                         │
│    └──────────────┘ └──────────────┘ └──────────────┘                         │
│                                                                               │
│    ┌─────────────────────────────────────────────────────────────────────┐   │
│    │              SHARED AGENT MEMORY                                    │   │
│    │   • Qdrant Vector Store: episodic memory of past decisions          │   │
│    │   • Redis Graph (or Neo4j): causal links between events             │   │
│    │   • Object Store (MinIO): artifact storage (logs, snapshots, code)  │   │
│    └─────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│    ┌─────────────────────────────────────────────────────────────────────┐   │
│    │              HEALTH MONITOR & SELF-HEALER                           │   │
│    │   • Heartbeat pings from all agents every 30s                       │   │
│    │   • Circuit breaker: agent failing 3x in 5m is paused & restarted   │   │
│    │   • Auto-rollback: production error rate spike → Revert Bot trigger │   │
│    └─────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Event Bus Schema (NATS JetStream)

All inter-agent communication happens via typed events on the bus. Telegram is only a human-facing surface, not the backbone.

| Stream | Subjects | Retention | Description |
|--------|----------|-----------|-------------|
| `tickets` | `tickets.created`, `tickets.updated`, `tickets.closed` | Work queue | Ticket lifecycle |
| `code` | `code.push`, `code.pr.opened`, `code.pr.merged` | Limits (1000) | Code events |
| `qa` | `qa.test_summary`, `qa.blocker`, `uat.ready`, `uat.feedback` | Work queue | Quality events |
| `release` | `release.approved`, `release.rejected`, `release.deployed` | Limits (500) | Release decisions |
| `human` | `human.message`, `human.command`, `human.uat_response` | Limits (5000) | Human input |
| `agent` | `agent.heartbeat`, `agent.task_assigned`, `agent.error` | Limits (10000) | Agent telemetry |
| `memory` | `memory.episode`, `memory.query` | Limits (50000) | Agent memory ops |

### Skill Registry & Dynamic Routing

When a new event is published, the Orchestrator evaluates required skills and routes to the best available agent:

```python
# Pseudo-code for Orchestrator routing
class Orchestrator:
    def on_event(self, event: Event):
        required_skills = self.skill_resolver.resolve(event)
        candidates = self.registry.find_agents_with_skills(required_skills)
        # Score candidates by: current load, past success rate on similar tasks,
        # recency of last heartbeat, specialization depth
        best_agent = self.scorer.rank(candidates, event)[0]
        self.dispatch(event, best_agent)
```

Agents self-register on boot with a JSON manifest:
```json
{
  "agent_id": "dev-7f3a",
  "type": "Developer",
  "skills": [
    {"name": "tdd_implementation", "proficiency": 0.95},
    {"name": "test_writing", "proficiency": 0.90},
    {"name": "refactoring", "proficiency": 0.85}
  ],
  "max_concurrent_tasks": 2,
  "current_load": 1
}
```

---

## 0.4 Agent Interaction Flow (Sequence Diagram)

```
Human/PM        Telegram GW       NATS Bus       Orchestrator      Analyst      Developer      QA Pool        PM Bot       CI/CD      GitHub
    │                │                │                │              │              │              │             │            │          │
    │─ /analyze ────►│                │                │              │              │              │             │            │          │
    │                │─ human.command ►│                │              │              │              │             │            │          │
    │                │                │─ route ───────►│              │              │              │             │            │          │
    │                │                │                │─ assign ────►│              │              │             │            │          │
    │                │                │                │              │ (decompose)   │              │             │            │          │
    │                │                │                │              │              │              │             │            │          │
    │                │◄─ tickets.summary ──────────────│              │              │              │             │            │          │
    │◄─ summary ─────│                │                │              │              │              │             │            │          │
    │                │                │                │              │─ tickets.created ►           │             │            │          │
    │                │                │                │              │              │              │             │            │          │
    │                │                │                │              │              │─ route ─────►│             │            │          │
    │                │                │                │              │              │              │             │            │          │
    │                │                │                │              │              │              │─ assign ───►│            │          │
    │                │                │                │              │              │              │             │            │          │
    │                │                │                │              │              │              │             │(write tests)│          │
    │                │                │                │              │              │              │             │(implement)  │          │
    │                │                │                │              │              │              │             │            │          │
    │                │                │                │              │              │              │             │─ git push ►│          │
    │                │                │                │              │              │              │             │            │─ webhook ►│
    │                │                │                │              │              │              │             │            │◄─────────│
    │                │                │                │              │              │              │             │◄─ CI result│          │
    │                │                │                │              │              │              │             │            │          │
    │                │                │                │              │              │─ code.push ─►│             │            │          │
    │                │                │                │              │              │              │             │            │          │
    │                │                │                │              │              │              │─ dev.ready_for_qa ►       │          │
    │                │                │                │              │              │              │             │            │          │
    │                │                │                │              │              │              │             │─ route ───►│          │
    │                │                │                │              │              │              │             │            │          │
    │                │                │                │              │              │              │             │            │checkout  │
    │                │                │                │              │              │              │             │            │run tests │
    │                │                │                │              │              │              │             │            │          │
    │                │                │                │              │              │              │             │            │          │
    │                │◄─ uat.ready ──────────────────────────────────────────────────────────────────│             │            │          │
    │◄─ UAT URL ─────│                │                │              │              │              │             │            │          │
    │ (human tests)  │                │                │              │              │              │             │            │          │
    │─ feedback ─────►│                │                │              │              │              │             │            │          │
    │                │─ human.uat_response ►           │              │              │              │             │            │          │
    │                │                │                │              │              │              │             │            │          │
    │                │                │                │              │              │              │─ qa.test_summary ►        │          │
    │                │                │                │              │              │              │             │            │          │
    │                │                │                │              │              │              │             │─ route ───►│          │
    │                │                │                │              │              │              │             │            │          │
    │                │                │                │              │              │              │             │            │(evaluate)│
    │                │                │                │              │              │              │             │            │          │
    │                │                │                │              │              │              │             │            │          │
    │           [APPROVED]            │                │              │              │              │             │            │          │
    │                │                │                │              │              │◄─ release.approved ────────│            │          │
    │                │                │                │              │              │              │             │            │          │
    │                │                │                │              │              │─ merge dev→main ────────────────────────►│          │
    │                │                │                │              │              │              │             │            │          │
    │                │                │                │              │              │              │             │            │deploy prod│
    │                │                │                │              │              │              │             │            │          │
    │           [REJECTED]            │                │              │              │              │             │            │          │
    │                │                │                │              │              │              │             │            │          │
    │                │                │                │              │◄─ release.rejected (req) ───│             │            │          │
    │                │                │                │              │              │◄─ release.rejected (code) ──│             │            │          │
    │                │                │                │              │ (re-analyze) │ (fix & re-impl)│             │            │          │
```

---

## 0.5 Supporting Tooling

| Tool | Purpose |
|------|---------|
| **Git / GitHub** | Source of truth; feature-branch workflow; PR-based merge gates |
| **GitHub Actions** | CI: lint, type check, unit tests, integration tests, coverage, security scan, Docker build |
| **NATS JetStream** | Event bus: durable streams, consumer groups, exactly-once processing, replay |
| **Docker + Docker Compose** | Local dev environment; agent containers; identical to staging |
| **pytest + coverage.py + pytest-xdist** | Python test runner with coverage enforcement (≥85% line coverage gate) and parallel execution |
| **Telegram Bot API** | Human-facing layer for agent ↔ human communication |
| **FastAPI Telegram Gateway** | Normalizes Telegram messages to NATS events and vice versa |
| **Conventional Commits** | Enforced via `commitlint`; enables automated changelog generation |
| **semantic-release** | Automated versioning and release notes from commit history |
| **Qdrant** | Agent episodic memory store (vector search over past decisions) |
| **Redis** | Agent state cache, session tokens, rate limit counters |
| **MinIO** | Artifact storage for agent logs, test snapshots, code diffs |
| **Prometheus + Grafana** | Agent health metrics, task throughput, latency distributions |
| **Loki** | Centralized agent log aggregation |

---

## 0.6 Quality & Velocity Mechanisms

- **TDD gate:** CI fails if new code lacks corresponding tests. Developer agent must produce at minimum 1 test file per implementation file.
- **Coverage gate:** PRs blocked if line coverage drops below 85% or if diff coverage is <90%.
- **Commit size policy:** Pre-commit hook rejects diffs >200 lines. If a change is inherently large, Developer must split into a chain of dependent tickets.
- **Agent Memory learning:** Analyst queries Agent Memory before decomposing a ticket — "have we built something similar before?" This reduces analysis time and improves estimation accuracy over sprints.
- **Sprint cadence:** PM agent tracks cycle time per ticket; posts weekly velocity digest to Telegram. Uses historical data from Agent Memory to predict sprint capacity.
- **Self-healing:** Health Monitor restarts crashed agents within 30s. If an agent fails the same task 3 times, the Orchestrator routes to a different agent instance and flags the failing agent for review.
- **Regression prevention:** QA agent maintains golden snapshot tests. Any output change (e.g., LLM prompt tweak) that alters generated cocktail schema triggers a human review.
- **Security gate:** Every PR triggers Security Auditor agent scan. Critical findings auto-reject the release.

---

---

# PART 1 — TARGET APPLICATION: BARTENDER AI ASSISTANT

## 1.1 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (Next.js 15, App Router)                           │
│  ┌──────────────┐   ┌──────────────────┐   ┌─────────────────────┐   ┌───────────┐  │
│  │  Chat Window │   │ Instruction Panel│   │  Profile / Context  │   │ Feedback  │  │
│  │  (slash cmds)│   │  (slash help)    │   │  Panel (paid only)  │   │  Panel    │  │
│  └──────┬───────┘   └──────────────────┘   └─────────────────────┘   └─────┬─────┘  │
└─────────┼──────────────────────────────────────────────────────────────────┼────────┘
          │ HTTPS / WebSocket (Socket.io v4)                                │
┌─────────▼──────────────────────────────────────────────────────────────────▼────────┐
│                        API GATEWAY (Traefik v3)                                      │
│         Auth middleware · Rate limiting · TLS termination · Geo-blocking             │
└────┬──────────────┬──────────────────┬───────────────────┬─────────────────┬─────────┘
     │              │                  │                   │                 │
┌────▼────┐  ┌──────▼──────┐  ┌────────▼────────┐  ┌─────▼────────┐  ┌─────▼─────────┐
│  Auth   │  │  Chat /     │  │  User / Profile  │  │  Subscription│  │  Feedback &   │
│ Service │  │  AI Service │  │  Service         │  │  Service     │  │  MLOps Service│
│(FastAPI)│  │  (FastAPI)  │  │  (FastAPI)       │  │  (FastAPI)   │  │  (FastAPI)    │
└────┬────┘  └──────┬──────┘  └────────┬─────────┘  └─────┬────────┘  └─────┬─────────┘
     │              │                  │                   │                 │
     │         ┌────▼──────────────────▼───────────────────┴─────────────────▼────────┐
     │         │                   PostgreSQL 16                                        │
     │         │      users · subscriptions · chat_sessions · messages · cocktails ·   │
     │         │      feedback · user_bar_context · taste_embeddings · ml_experiments  │
     │         └────────────────────────────────────────────────────────────────────────┘
     │              │
     │         ┌────▼───────────────────────────────────────────────────────────────────┐
     │         │                  LLM GATEWAY SERVICE (v2)                              │
     │         │   Smart Router · Circuit Breaker · Cost Tracker · Prompt Cache · A/B   │
     │         │                                                                        │
     │         │  ┌────────────────────┐        ┌────────────────────────────────────┐  │
     │         │  │  Free Tier         │        │      Paid Tier                     │  │
     │         │  │  Llama 3.3 70B     │        │  Claude Sonnet 4.6 / GPT-4.1       │  │
     │         │  │  (Groq API)        │        │  (Anthropic / OpenAI API)          │  │
     │         │  │  Fallback: Ollama  │        │  Fallback: Claude Haiku / GPT-4o   │  │
     │         │  └────────────────────┘        └────────────────────────────────────┘  │
     │         └────┬───────────────────────────────────────────────────────────────────┘
     │              │
     │         ┌────▼───────────────────────────────────────────────────────────────────┐
     │         │                    RAG SERVICE (Hybrid Architecture)                   │
     │         │                                                                        │
     │         │  ┌──────────────────────────────────────────────────────────────────┐  │
     │         │  │              Qdrant Vector Store                                  │  │
     │         │  │  Collection: iba_cocktails (free + paid)                          │  │
     │         │  │  Collection: extended_cocktails (paid only, taste_score ≥ 4.0)    │  │
     │         │  │  Collection: ingredient_chemistry (all tiers)                     │  │
     │         │  │  Collection: user_bar_context (paid, per-user namespace)          │  │
     │         │  │  Collection: taste_feedback_embeddings (all tiers)                │  │
     │         │  └──────────────────────────────────────────────────────────────────┘  │
     │         │                              │                                       │
     │         │  ┌───────────────────────────▼──────────────────────────────────────┐  │
     │         │  │           Knowledge Graph (Neo4j or KùzuDB)                       │  │
     │         │  │  Nodes: Ingredient, Cocktail, FlavorFamily, BarConcept            │  │
     │         │  │  Edges: CONTAINS, PAIRS_WITH, INCOMPATIBLE_WITH, SIMILAR_TO      │  │
     │         │  └──────────────────────────────────────────────────────────────────┘  │
     │         └──────────────────────────────────────────────────────────────────────┘
     │
┌────▼────────────────────────────────────────────────────────────────────────────────┐
│                      Redis Cluster (Cache + Rate Limit + Sessions)                   │
│        JWT session store · LLM response cache · Rate limit counters · Pub/Sub        │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1.2 Frontend Design

### Technology
- **Framework:** Next.js 15 (App Router, React Server Components, Partial Prerendering)
- **UI Library:** shadcn/ui + Tailwind CSS v4 + Radix UI primitives
- **State:** Zustand (global chat state, offline-first with localStorage sync), TanStack Query v5 (server state)
- **Real-time:** Socket.io v4 (streaming LLM tokens, typing indicators, presence)
- **Auth:** Clerk (faster MVP than NextAuth; built-in MFA, session management, org support)
- **Payments:** Stripe Elements + Stripe Checkout
- **Forms:** React Hook Form + Zod validation
- **Accessibility:** Radix primitives ensure WCAG 2.1 AA compliance out of the box

### Main Screen Layout
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [Logo] BartenderAI          [Plan: Free ▾]  [🔔] [Profile] [⚙️]            │
├───────────────────────────────────────┬─────────────────────────────────────┤
│                                       │  QUICK GUIDE                        │
│   Chat Window                         │  ─────────────────────────────────  │
│   ─────────────────────────────────   │  /help                              │
│   │ 🤖 Welcome! I'm your bartending  │  List all commands                  │
│   │    AI assistant. Try:             │                                     │
│   │    /create-cocktail               │  /create-cocktail <description>     │
│   │    /cost <recipe>                 │  Generate 1-3 cocktail recipes      │
│   │    /help                          │                                     │
│   │    /menu-design <concept>         │  /cost <recipe or cocktail>         │
│   │    /suggest <flavor>              │  Calculate cost per serving         │
│   │    /my-context                    │                                     │
│   │    /feedback                      │  /menu-design <concept> ⭐          │
│   ─────────────────────────────────   │  Design a full cocktail menu        │
│                                       │                                     │
│   [Message input + send button]       │  /suggest <flavor profile>          │
│   [Slash command autocomplete]        │  Quick recommendation               │
│   [Attachment dropzone - paid]        │                                     │
│                                       │  ✨ Upgrade for premium models +    │
│                                       │  bar context + menu upload          │
└───────────────────────────────────────┴─────────────────────────────────────┘
```

### Slash Command System
Commands are parsed client-side with a fuzzy-matching autocomplete engine:
- `/help` — Interactive command explorer with examples
- `/create-cocktail [prompt]` — Cocktail generation flow; shows loading skeleton with streaming tokens
- `/cost [recipe or cocktail name]` — Cost calculation with real-time price lookup
- `/menu-design [concept]` — (paid) Full menu generation with section grouping
- `/suggest [flavor profile]` — Quick recommendation with one-click "make it"
- `/my-context` — (paid) View/edit bar concept, inventory, uploaded menus
- `/feedback` — (all tiers) Submit taste survey for previously generated cocktails
- `/compare [cocktail A] vs [cocktail B]` — (paid) Side-by-side ingredient and cost comparison

Command parsing: fuzzy match on `/` prefix → extract command + args → validate with Zod schema → set `messageType` + `payload` in Socket.io event.

---

## 1.3 Core Chat & AI Service

### Request Flow
1. Client emits `chat:message` via Socket.io with `{ session_id, content, command?, user_id, request_id }`.
2. Chat Service authenticates via Clerk JWT, loads user subscription tier from Redis cache (fallback to PostgreSQL).
3. Calls **RAG Service** with query planning enabled (see 1.5).
4. Constructs prompt: system prompt + RAG context + conversation history (last 10 turns, summarized beyond that).
5. Calls **LLM Gateway v2** with the assembled prompt, streaming tokens back via Socket.io.
6. Parses LLM output through JSON schema validator (Pydantic v2); if invalid, triggers regeneration with stricter prompt.
7. Persists message + validated response to `messages` table; caches LLM response in Redis (TTL=1h for identical queries).
8. If command is `/create-cocktail`, schedules deferred feedback survey (24h later via Celery beat).

### System Prompt Template (Multi-Tier)
```
You are BartenderAI, a professional assistant for bartenders and bar managers.
You specialize in cocktail creation, menu design, bar operations, and cost optimization.

RULES:
1. Never suggest recipes with unsafe or incompatible ingredient combinations.
2. Filter any toxic, profane, or inappropriate content.
3. Always return cocktail suggestions in the specified JSON schema.
4. For physical plausibility, apply layering/density rules from the chemistry context.
5. Respect the user's bar concept, inventory constraints, and current menu style.
6. Suggest 1–3 options. Each must include: name, ingredients (qualitative + quantitative),
   method, glass, garnish, tasting notes (aroma/palate/finish), and estimated cost.

RETRIEVED KNOWLEDGE:
{iba_cocktails_context}
{extended_cocktails_context}
{ingredient_chemistry_context}
{user_bar_context}

SIMILAR HIGH-RATED CREATIONS (inspiration only):
{top_rated_similar_cocktails}

AVOID (negative examples from low-rated feedback):
{negative_examples}

USER CONTEXT:
Subscription: {tier}
Bar concept: {bar_concept}
Inventory constraints: {inventory_list}
Conversation history (last 10 turns): {history_summary}
```

---

## 1.4 LLM Gateway Service (v2)

The v2 gateway adds circuit breakers, cost tracking, A/B testing, and intelligent fallback chains.

### Routing Logic
```python
class LLMGateway:
    def route(self, user_tier: str, prompt: Prompt, complexity_score: float) -> LLMResponse:
        # Complexity score (0-1) derived from prompt length, RAG context size, and command type
        
        if user_tier == "free":
            primary = ModelConfig("llama-3.3-70b-versatile", provider="groq", max_tokens=1024)
            fallback_chain = [
                ModelConfig("llama-3.1-70b-versatile", provider="groq"),
                ModelConfig("mixtral-8x7b", provider="groq"),
                ModelConfig("llama3.2", provider="ollama_local")  # local fallback
            ]
            rate_limit = RateLimit(rpm=10, rpd=100, window="sliding")
        
        elif user_tier == "paid":
            # A/B test: 50% Claude Sonnet, 50% GPT-4.1
            primary = self.ab_test_select("paid_generation", [
                ModelConfig("claude-sonnet-4-6", provider="anthropic", max_tokens=4096),
                ModelConfig("gpt-4.1", provider="openai", max_tokens=4096)
            ])
            fallback_chain = [
                ModelConfig("claude-haiku-4", provider="anthropic"),
                ModelConfig("gpt-4o-mini", provider="openai")
            ]
            rate_limit = RateLimit(rpm=60, rpd=1000, window="sliding")
        
        return self.execute_with_fallback(primary, fallback_chain, prompt, rate_limit)
```

### Advanced Features
- **Circuit Breaker:** If a provider fails 5x in 2 minutes, traffic is routed away for 5 minutes.
- **Cost Tracker:** Every LLM call logs tokens in/out, cost, latency, and model name to `llm_usage` table. Monthly cost alerts for paid tier operations.
- **Prompt Cache:** Semantic cache in Redis — identical or near-identical prompts (cosine similarity >0.97) return cached response, saving ~30% of LLM calls.
- **Streaming:** All responses stream via Server-Sent Events (SSE) over Socket.io; gateway handles backpressure.
- **Response Validation:** JSON schema validation + safety filter (Llama Guard 3 for free, OpenAI Moderation + Llama Guard for paid). Failed validation triggers one auto-regeneration with tightened constraints.

---

## 1.5 RAG Pipeline (Hybrid: Vector + Knowledge Graph)

### Knowledge Base Structure

| Collection / Graph | Contents | Access | Update Frequency |
|--------------------|----------|--------|-----------------|
| `iba_cocktails` (vector) | ~100 IBA official cocktail recipes | Free + Paid | Static |
| `extended_cocktails` (vector) | Community-generated cocktails with taste_score ≥ 4.0 | Paid only | Weekly batch |
| `ingredient_chemistry` (vector) | Physical/chemical properties of ~300 ingredients | All tiers | Monthly manual curation |
| `user_bar_context_{user_id}` (vector) | Uploaded menus, bar concept, inventory | Paid, per-user namespace | On user action |
| `taste_feedback_embeddings` (vector) | Embedding of user feedback notes for semantic similarity | All tiers | Real-time |
| **Knowledge Graph** (Neo4j) | Ingredient nodes, cocktail nodes, flavor families, pairing rules, incompatibilities | All tiers | Weekly from feedback + manual curation |

### Ingestion Pipeline

```
Data Source (IBA JSON / PDF / Image / Feedback)
        │
        ▼
Ingestion Worker (Celery Task)
  ├─ Parse & normalize to CocktailSchema (Pydantic v2)
  ├─ Extract entities: ingredients, flavors, glassware, methods
  ├─ Build graph relationships: (Cocktail)-[:CONTAINS]->(Ingredient)
  │                            (Ingredient)-[:PAIRS_WITH]->(Ingredient)
  │                            (Ingredient)-[:INCOMPATIBLE_WITH]->(Ingredient)
  ├─ Chunk: one document per cocktail OR per-ingredient chemistry doc
  ├─ Embed: text-embedding-3-small (OpenAI) for production
  │          all-MiniLM-L6-v2 (local) for free-tier fallback
  └─ Hybrid index: dense vector + sparse BM25 (via Qdrant sparse vectors)
        │
        ▼
Qdrant Upsert + Neo4j Merge
        │
        ▼
Embedding index + Knowledge Graph ready for retrieval
```

**PDF / Image Upload (Paid users):**
```
User uploads PDF/PNG
        │
        ▼
Upload Service (MinIO S3-compatible storage)
        │
        ▼
Document Parser Pipeline
  ├─ PDF: marker (state-of-the-art layout-aware extraction) OR PyMuPDF fallback
  ├─ Image: GPT-4o Vision for menu OCR + structure extraction
  ├─ Table detection: extract drink names, ingredients, prices
  └─ Deduplication: check if menu already parsed (hash-based)
        │
        ▼
Text chunked (512 tokens, 50-token overlap) + metadata (page number, section)
        │
        ▼
Embed (dense + sparse) + Upsert → user_bar_context_{user_id} collection
        │
        ▼
Graph update: (BarConcept)-[:HAS_MENU_ITEM]->(ExtractedCocktail)
```

### Retrieval Strategy (Multi-Hop + Hybrid)

1. **Query Planning:** The RAG Service first analyzes the user prompt to determine:
   - What information is needed? (recipe inspiration, chemistry constraints, bar context, cost data)
   - Which collections to query?
   - Should we do multi-hop retrieval? (e.g., "something like an Old Fashioned but with tequila" → hop 1: find Old Fashioned → hop 2: find tequila-based cocktails with similar profiles)

2. **Hybrid Search:** For each target collection:
   - Dense retrieval (vector similarity) for semantic matching
   - Sparse retrieval (BM25) for exact keyword matching (ingredient names, cocktail names)
   - Fusion: Reciprocal Rank Fusion (RRF) to combine dense + sparse rankings

3. **Knowledge Graph Augmentation:**
   - Query Neo4j for ingredient pairings, incompatibilities, and "similar cocktails" graph paths.
   - Example Cypher: `MATCH (i:Ingredient {name: 'Mezcal'})-[:PAIRS_WITH]->(j:Ingredient) RETURN j.name, j.confidence LIMIT 10`

4. **Reranking:** Cross-encoder (ms-marco-MiniLM-L-6-v2) reranks top-30 fused results to top-8.

5. **Context Assembly:** Injects top-8 passages + graph-derived rules into system prompt under `{rag_context}` block.

6. **Query Rewriting (paid tier):** If initial retrieval is low-confidence, the gateway uses a lightweight LLM (Claude Haiku) to rewrite the query for better retrieval, then re-runs the pipeline (max 1 rewrite).

---

## 1.6 Subscription & Tier System

### Subscription Service
- **Payment:** Stripe Checkout + Customer Portal; webhooks update `subscriptions` table.
- **Tiers:**
  - `free` — default on registration; Llama via Groq; IBA KB only; basic chat history.
  - `paid_monthly` / `paid_annual` — premium LLMs (Claude/GPT-4); extended KB; bar context; menu upload; `/menu-design`; advanced RAG with query rewriting.
  - `team` (post-MVP) — shared bar context across bar staff, admin dashboard, analytics.

### Feature Gate Enforcement
- Clerk JWT contains `tier` claim, refreshed on every session token rotation.
- Backend middleware validates `tier` on every protected endpoint; rejects with `403` + upgrade CTA payload.
- Frontend conditionally renders paid features; free users see blurred preview + one-click upgrade.
- **Trial Mode:** New paid sign-ups get 7-day free trial with full feature access; no charge until trial ends.

---

## 1.7 Response Format & Safety

All cocktail generation responses conform to this validated schema:

```json
{
  "suggestions": [
    {
      "name": "Midnight Smoke",
      "description": "A smoky, spirit-forward cocktail with a long finish.",
      "ingredients": [
        { "name": "Mezcal", "quantity": 45, "unit": "ml", "estimated_cost_usd": 2.50 },
        { "name": "Sweet Vermouth", "quantity": 20, "unit": "ml", "estimated_cost_usd": 0.80 },
        { "name": "Amaro Nonino", "quantity": 10, "unit": "ml", "estimated_cost_usd": 1.20 },
        { "name": "Orange Bitters", "quantity": 2, "unit": "dashes", "estimated_cost_usd": 0.10 }
      ],
      "method": "Stir with ice for 30 seconds. Strain into chilled coupe.",
      "glass": "Coupe",
      "garnish": "Flamed orange peel twist",
      "tasting_notes": {
        "aroma": "Smoke, dried fruit, herbal bitterness",
        "palate": "Rich, smoky, bittersweet with earthy undertones",
        "finish": "Long, warming, slightly smoky"
      },
      "estimated_cost_per_serving": 4.60,
      "physical_validation": {
        "status": "passed",
        "checks": ["density_order", "miscibility", "ph_balance"]
      },
      "safety_check": "passed"
    }
  ],
  "count": 1,
  "metadata": {
    "model_used": "claude-sonnet-4-6",
    "rag_sources": ["iba_cocktails", "ingredient_chemistry", "user_bar_context"],
    "generation_time_ms": 1450
  }
}
```

**Safety Pipeline:**
1. **Pre-generation:** Prompt scanned by Llama Guard 3 (free) or OpenAI Moderation + Llama Guard (paid). Blocked prompts return a safe fallback message and are logged.
2. **Post-generation:** Response scanned for toxic content, profanity, and unsafe ingredient combinations (e.g., excessive alcohol concentration).
3. **Physical Validation:** Recipe run through the validation engine (see Part 2.2). Failures trigger up to 2 regeneration attempts with error context injected.
4. **Schema Validation:** Pydantic v2 strict validation. Schema failures trigger regeneration with the validation error as a constraint.

---

---

# PART 2 — KNOWN CHALLENGES & SOLUTIONS

## 2.1 Measurable Taste Metric & Feedback Loop (with MLOps)

### Problem
"Good" is subjective. Without structured feedback, the system cannot learn or distinguish excellent suggestions from mediocre ones.

### Solution: Structured Taste Survey + Feedback-Driven Fine-Tuning Pipeline

**Deferred Survey (24h after generation, via in-app notification + optional Telegram):**
```
How did the cocktail land with your guests?

Overall impression:    ★ ★ ★ ★ ★
Balance (sweet/sour):  ★ ★ ★ ★ ★
Aroma complexity:      ★ ★ ★ ★ ★
Appearance:            ★ ★ ★ ★ ★
Guest reaction:        😞 😐 🙂 😄 🤩
Would you make it again?  [Yes] [No] [With modifications]
What would you change? [Optional text]
```

**Feedback Schema:**
```sql
CREATE TABLE cocktail_feedback (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cocktail_id       UUID REFERENCES cocktails(id),
    user_id           UUID REFERENCES users(id),
    overall_rating    SMALLINT CHECK (overall_rating BETWEEN 1 AND 5),
    balance_rating    SMALLINT CHECK (balance_rating BETWEEN 1 AND 5),
    aroma_rating      SMALLINT CHECK (aroma_rating BETWEEN 1 AND 5),
    appearance_rating SMALLINT CHECK (appearance_rating BETWEEN 1 AND 5),
    guest_reaction    SMALLINT CHECK (guest_reaction BETWEEN 1 AND 5),
    would_repeat      VARCHAR(20),  -- 'yes' | 'no' | 'modified'
    modification_note TEXT,
    notes             TEXT,
    taste_score       DECIMAL(3,2) GENERATED ALWAYS AS (
        0.30 * overall_rating + 0.25 * balance_rating +
        0.20 * aroma_rating + 0.15 * appearance_rating +
        0.10 * guest_reaction
    ) STORED,
    embedding         VECTOR(1536),  -- embedding of feedback text for semantic analysis
    created_at        TIMESTAMPTZ DEFAULT NOW()
);
```

**Composite Taste Score v2:**
```
taste_score = 0.30 * overall + 0.25 * balance + 0.20 * aroma + 0.15 * appearance + 0.10 * guest_reaction
```
*(Weights adjusted based on bartender interviews: overall and balance matter most)*

**Feedback Loop Actions:**
- `taste_score ≥ 4.2` → cocktail eligible for ingestion into `extended_cocktails` KB (paid tier sees it immediately; free tier sees a "community pick" label).
- `taste_score 3.5–4.1` → flagged for prompt refinement; used as neutral example.
- `taste_score < 3.5` → marked `deprecated`; used as explicit negative example in future prompts.
- **Free user incentive:** "Submit 5 detailed feedback surveys → unlock 14 days of paid features." Drives engagement and upgrade conversion.

**MLOps Fine-Tuning Pipeline (Monthly):**
```
Feedback data (30-day batch)
        │
        ▼
Data Preparation Worker
  ├─ Filter: only feedback with text notes OR taste_score ≥ 4.0 OR < 2.5
  ├─ Create training pairs: (prompt + context) → (high-rated cocktail JSON)
  ├─ Create DPO pairs: preferred (high-rated) vs rejected (low-rated) for same prompt
  └─ Format: Alpaca / ShareGPT / Anthropic message format
        │
        ▼
Fine-Tuning Job (via Fireworks AI or Together AI for cost efficiency)
  ├─ Base model: Llama 3.3 70B (free tier) or Mistral Large (paid tier candidate)
  ├─ Method: LoRA / QLoRA for parameter-efficient fine-tuning
  ├─ Evaluation: hold-out test set with human bartender review
  └─ A/B test: 10% traffic to fine-tuned model, 90% to base
        │
        ▼
Model Registry (MLflow)
  ├─ Track: loss curves, eval metrics, taste_score correlation
  ├─ If A/B test shows +0.3 taste_score improvement → promote to production
  └─ If regression → rollback to previous model
        │
        ▼
Deployment
  ├─ New LoRA adapter loaded into LLM Gateway
  └─ Old adapter kept as hot-rollback target
```

**Prompt Refinement (RLHF-lite, Weekly):**
- Re-embed top-20 and bottom-20 cocktails from the past week.
- Top cocktails → injected as few-shot positive examples in generation prompt.
- Bottom cocktails → injected as negative examples with specific reasons ("avoid overly sweet profiles").
- Feedback text embeddings added to `taste_feedback_embeddings` collection for semantic retrieval ("find cocktails similar to what this user liked before").

---

## 2.2 Physical Realizability

### Problem
LLMs can hallucinate physically impossible recipes (e.g., denser liquid layered on top, incompatible ingredients that curdle, pH extremes that denature proteins).

### Solution: Chemistry RAG + Knowledge Graph Rules + Post-Generation Validation Engine

**Chemistry Knowledge Base (vector + graph):**
Each ingredient document (vector) + graph node contains:
```json
{
  "name": "Lime Juice",
  "density_g_per_ml": 1.03,
  "abv": 0.0,
  "ph": 2.3,
  "brix": 6.5,
  "flavor_family": ["sour", "citrus", "bright"],
  "miscibility": ["water-based", "acidic"],
  "known_incompatibilities": [
    {"ingredient": "Cream", "reaction": "curdling", "severity": "critical"},
    {"ingredient": "Egg White", "reaction": "denaturation", "severity": "warning"}
  ],
  "aroma_compounds": ["limonene", "citral", "gamma-terpinene"],
  "layering_position": "top",
  "viscosity_cp": 1.5,
  "surface_tension_mn_m": 72.8
}
```

Graph relationships enable rule inference:
```cypher
// Find all ingredients incompatible with any ingredient in a proposed recipe
MATCH (c:Cocktail {name: $proposed_name})-[:CONTAINS]->(i:Ingredient)
MATCH (i)-[:INCOMPATIBLE_WITH]->(j:Ingredient)
WHERE EXISTS { MATCH (c)-[:CONTAINS]->(j) }
RETURN i.name, j.name, i.incompatibility_reason
```

**Pre-generation retrieval:**
- All ingredients mentioned or implied in the user prompt are resolved against the chemistry KB.
- Compatibility rules, density ranges, and pH constraints are injected into the system prompt.
- The prompt explicitly instructs the LLM to respect these constraints.

**Post-generation Validation Engine (Python service):**
```python
class PhysicalValidator:
    def validate(self, recipe: Recipe) -> ValidationResult:
        issues = []
        
        # 1. Incompatibility check
        for a, b in combinations(recipe.ingredients, 2):
            if self.graph.has_incompatibility(a.name, b.name):
                issues.append(IncompatibilityIssue(a, b, severity="critical"))
        
        # 2. Layering order check (if method is "layered" or "float")
        if recipe.method in ("layered", "float"):
            sorted_by_density = sorted(recipe.ingredients, key=lambda x: x.density, reverse=True)
            if recipe.ingredient_order != [i.name for i in sorted_by_density]:
                issues.append(LayeringIssue(expected=sorted_by_density, actual=recipe.ingredient_order))
        
        # 3. pH balance check (cocktail pH should be 2.8–5.5 for palatability and safety)
        estimated_ph = self.estimate_ph(recipe.ingredients)
        if estimated_ph < 2.5 or estimated_ph > 6.0:
            issues.append(PhBalanceIssue(estimated_ph, acceptable_range=(2.8, 5.5)))
        
        # 4. ABV sanity check (cocktail ABV typically 15–35%; warn if >40%)
        estimated_abv = self.estimate_abv(recipe.ingredients)
        if estimated_abv > 40:
            issues.append(AbvIssue(estimated_abv, warning_threshold=40))
        
        # 5. Viscosity/mouthfeel plausibility
        if len([i for i in recipe.ingredients if i.viscosity > 100]) > 2:
            issues.append(ViscosityIssue("Too many viscous ingredients; result may be syrupy"))
        
        return ValidationResult(valid=len([i for i in issues if i.severity == "critical"]) == 0, issues=issues)
```

**Regeneration Protocol:**
- If validation fails with critical issues: LLM is prompted to regenerate with validation errors as explicit constraints.
- Maximum 2 regeneration attempts.
- If still failing after 2 attempts: return the best-effort result with prominent UI warnings ("⚠️ This recipe has physical compatibility concerns: [issues]") and flag for human review.
- All validation failures are logged to `validation_failures` table for MLOps analysis (used to improve the base model).

---

## 2.3 Local Bar Context for Paid Users (Zero-Shot Meta-Learning)

### Problem
Generic suggestions are less useful to a bartender at a Japanese whisky bar than to one at a tropical resort. Without local context, outputs feel impersonal.

### Solution: Bar Context Profile + Per-User RAG + Graph-Based Meta-Learning

**User Profile Panel (paid tier):**
- **Bar Concept:** Free-text description (e.g., "Speakeasy, 1920s aesthetic, 40 seats, focus on American whiskey and amaro").
- **Current Menu Upload:** PDF or PNG (parsed → chunked → embedded → `user_bar_context_{user_id}` + graph nodes for each menu item).
- **Inventory:** Structured list (ingredient name, in-stock quantity, cost per unit) OR free-text.
- **Style Preferences:** Slider inputs for sweetness, sourness, bitterness, spirit-forward vs refreshing.
- **Target Price Range:** Per-cocktail target cost (affects `/cost` and generation suggestions).

**Context Injection at Query Time:**
1. **Semantic retrieval:** Top-5 passages from `user_bar_context_{user_id}` via hybrid search (dense + BM25).
2. **Graph retrieval:** Query Neo4j for cocktails that share ingredients with the user's current menu ("menu coherence" — suggest drinks that reuse existing inventory).
3. **Global context:** Query `iba_cocktails` + `ingredient_chemistry` + `extended_cocktails` (paid).
4. **Merge & rank:** RRF fusion across all sources, then rerank with cross-encoder.
5. **Inject:** All context into system prompt under `{user_bar_context}` block.

**Zero-Shot Meta-Learning Mechanism (Graph-based):**
```cypher
// Find cocktails from the extended KB that are popular in bars with similar concepts
MATCH (user_bar:BarConcept {user_id: $user_id})
MATCH (other_bar:BarConcept)
WHERE other_bar.user_id <> $user_id
WITH user_bar, other_bar,
     gds.similarity.cosine(user_bar.embedding, other_bar.embedding) AS concept_similarity
WHERE concept_similarity > 0.75
MATCH (other_bar)<-[:SERVED_AT]-(c:Cocktail)
WHERE c.taste_score >= 4.2
RETURN c.name, c.ingredients, c.taste_score, concept_similarity
ORDER BY concept_similarity DESC, c.taste_score DESC
LIMIT 5
```

- These "style-match" cocktails are anonymized and surfaced as inspirational references.
- Prompt instruction: *"The following cocktails were highly rated in bars with similar concepts. Use them as style inspiration, not as direct copies. Ensure your suggestions fit the user's specific inventory and concept."*

**Inventory-Aware Generation:**
- If inventory is provided, the system builds a "virtual constraint solver":
  - Primary constraint: suggest cocktails using ≥70% in-stock ingredients.
  - Secondary constraint: suggest cocktails that reuse ingredients already on the current menu (reduces waste, improves bar efficiency).
  - Tertiary constraint: respect target price per serving.
- Missing ingredients are listed in the UI with a "⚠️ You need to source: [ingredient]" note.

**Menu Coherence Scoring (paid feature):**
- After generating suggestions, the system scores each cocktail for "menu fit":
  - Ingredient overlap with current menu (+)
  - Flavor profile diversity vs existing menu (+)
  - Glassware already in use (+)
  - Duplication of existing menu item (-)
- Menu fit score displayed to user as a badge ("★★★★☆ Great menu fit").

---

---

# TECHNOLOGY STACK

## Backend
| Component | Technology | Rationale |
|-----------|------------|-----------|
| API Services | FastAPI (Python 3.12) | Async, type-safe, auto-docs; native Pydantic v2; streaming SSE support |
| Database ORM | SQLAlchemy 2.0 + Alembic | Async ORM; robust migrations; PostgreSQL dialect optimized |
| Primary DB | PostgreSQL 16 + pgvector extension | ACID, JSON support, pgvector for ad-hoc vector ops (Qdrant handles primary ANN) |
| Cache / Sessions / Pub-Sub | Redis 7 (Cluster mode) | Sub-ms latency; atomic counters; Socket.io adapter; session store |
| Vector DB | Qdrant 1.10+ | Multi-collection filtering, sparse vectors (BM25), Rust-based, self-hostable |
| Knowledge Graph | Neo4j Community or KùzuDB | Graph traversal for ingredient relationships; Cypher query language |
| Message Queue / Event Bus | NATS JetStream | Durable streams, consumer groups, exactly-once, replay, ordered delivery |
| Background Jobs | Celery + Redis | Periodic tasks (feedback surveys, MLOps batch jobs, KB updates) |
| Object Storage | MinIO | S3-compatible; PDF/image uploads; agent artifact storage |
| PDF Parsing | marker (primary) + PyMuPDF (fallback) | `marker` is state-of-the-art for layout-aware PDF extraction |
| OCR | GPT-4o Vision (primary) + Tesseract (fallback) | Vision model handles stylized menus; Tesseract for simple text-on-image |
| WebSocket | Socket.io v4 (python-socketio) | Room-based namespaces, automatic reconnection, Redis adapter for horizontal scaling |

## Frontend
| Component | Technology |
|-----------|------------|
| Framework | Next.js 15 (App Router, Partial Prerendering) |
| UI | shadcn/ui + Tailwind CSS v4 + Radix UI |
| State (global) | Zustand (with persist middleware for offline chat history) |
| Server state | TanStack Query v5 |
| Real-time | Socket.io-client v4 |
| Auth | Clerk |
| Payments | Stripe.js + Stripe Checkout |
| Forms | React Hook Form + Zod |
| Charts | Tremor / Recharts (for feedback analytics dashboard) |

## AI / ML
| Component | Technology |
|-----------|------------|
| Free tier LLM | Llama 3.3 70B via Groq API |
| Paid tier LLM | Claude Sonnet 4.6 (Anthropic) / GPT-4.1 (OpenAI) — A/B tested |
| Embedding model | text-embedding-3-small (OpenAI) for production; all-MiniLM-L6-v2 (local) for free-tier fallback |
| Sparse retrieval | Qdrant built-in sparse vectors (SPLADE or BM25) |
| Reranker | ms-marco-MiniLM-L-6-v2 (local, via sentence-transformers) |
| RAG orchestration | Custom orchestration layer (Query Planner + Hybrid Retriever + Graph Augmenter) — LlamaIndex as optional integration layer |
| Safety filter | Llama Guard 3 (local, free tier) / OpenAI Moderation + Llama Guard 3 (paid tier) |
| Fine-tuning infra | Fireworks AI or Together AI (LoRA/QLoRA training) |
| Model registry | MLflow (self-hosted) |
| Knowledge graph | Neo4j (self-hosted) or KùzuDB (embedded, easier for MVP) |

## Multi-Agent System
| Component | Technology |
|-----------|------------|
| Agent framework | Anthropic Python SDK (Claude tool use) + custom Orchestrator |
| Agent containers | Docker (each agent is a container) |
| Event bus | NATS JetStream |
| Telegram interface | python-telegram-bot v21 (async) + FastAPI Gateway |
| CI/CD | GitHub Actions |
| Agent memory | Qdrant (vector) + Redis (state) + MinIO (artifacts) |
| Health monitor | Custom Python service + Prometheus metrics |

## Infra / Ops
| Component | Technology |
|-----------|------------|
| Container orchestration | Docker Compose (MVP weeks 1–10) → Kubernetes (post-MVP) |
| Reverse proxy / ingress | Traefik v3 (automatic Let's Encrypt, middleware chains) |
| Monitoring | Prometheus + Grafana |
| Logging | Loki + Grafana |
| Error tracking | Sentry |
| Secrets | Doppler (easier than Vault for small teams) or HashiCorp Vault |
| Load testing | Locust or k6 |

---

---

# DATA MODELS

## users
```sql
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) UNIQUE NOT NULL,
    name        VARCHAR(255),
    clerk_id    VARCHAR(255) UNIQUE NOT NULL,
    tier        VARCHAR(20) NOT NULL DEFAULT 'free',   -- 'free' | 'paid_monthly' | 'paid_annual' | 'team'
    trial_ends_at TIMESTAMPTZ,
    preferences JSONB DEFAULT '{}',                     -- UI preferences, notification settings
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
```

## subscriptions
```sql
CREATE TABLE subscriptions (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID REFERENCES users(id) ON DELETE CASCADE,
    stripe_sub_id    VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255),
    plan             VARCHAR(50) NOT NULL,             -- 'monthly' | 'annual'
    status           VARCHAR(50) NOT NULL,             -- 'active' | 'canceled' | 'past_due' | 'trialing'
    current_period_start TIMESTAMPTZ,
    current_period_end   TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);
```

## chat_sessions
```sql
CREATE TABLE chat_sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(255) GENERATED ALWAYS AS (left(first_message, 50)) STORED,
    first_message TEXT,
    model_used  VARCHAR(100),                          -- for analytics
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
```

## messages
```sql
CREATE TABLE messages (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id   UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role         VARCHAR(20) NOT NULL,                  -- 'user' | 'assistant' | 'system'
    content      TEXT NOT NULL,
    command      VARCHAR(50),
    command_args JSONB,
    model_used   VARCHAR(100),
    latency_ms   INTEGER,
    token_count_input INTEGER,
    token_count_output INTEGER,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
```

## cocktails
```sql
CREATE TABLE cocktails (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    ingredients     JSONB NOT NULL,                     -- [{name, quantity, unit, cost_usd}]
    method          TEXT,
    glass           VARCHAR(100),
    garnish         VARCHAR(255),
    tasting_notes   JSONB,                              -- {aroma, palate, finish}
    source          VARCHAR(50) NOT NULL,              -- 'iba' | 'generated' | 'user' | 'community'
    created_by      UUID REFERENCES users(id),
    taste_score     DECIMAL(3,2),
    feedback_count  INTEGER DEFAULT 0,
    is_deprecated   BOOLEAN DEFAULT FALSE,
    is_promoted     BOOLEAN DEFAULT FALSE,             -- in extended KB
    physical_validation_status VARCHAR(20),            -- 'passed' | 'failed' | 'warning'
    qdrant_point_id VARCHAR(255),                      -- Qdrant point ID
    neo4j_node_id   VARCHAR(255),                      -- Neo4j node ID
    generation_metadata JSONB,                         -- {model, rag_sources, generation_time_ms}
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

## cocktail_feedback
```sql
CREATE TABLE cocktail_feedback (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cocktail_id       UUID REFERENCES cocktails(id),
    user_id           UUID REFERENCES users(id),
    overall_rating    SMALLINT CHECK (overall_rating BETWEEN 1 AND 5),
    balance_rating    SMALLINT CHECK (balance_rating BETWEEN 1 AND 5),
    aroma_rating      SMALLINT CHECK (aroma_rating BETWEEN 1 AND 5),
    appearance_rating SMALLINT CHECK (appearance_rating BETWEEN 1 AND 5),
    guest_reaction    SMALLINT CHECK (guest_reaction BETWEEN 1 AND 5),
    would_repeat      VARCHAR(20),                     -- 'yes' | 'no' | 'modified'
    modification_note TEXT,
    notes             TEXT,
    taste_score       DECIMAL(3,2) GENERATED ALWAYS AS (
        0.30 * overall_rating + 0.25 * balance_rating +
        0.20 * aroma_rating + 0.15 * appearance_rating +
        0.10 * guest_reaction
    ) STORED,
    embedding         VECTOR(1536),
    created_at        TIMESTAMPTZ DEFAULT NOW()
);
```

## user_bar_context
```sql
CREATE TABLE user_bar_context (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    concept_text    TEXT,
    inventory       JSONB,                             -- [{ingredient, quantity, unit, cost_per_unit}]
    style_preferences JSONB,                           -- {sweetness, sourness, bitterness, spirit_forward}
    target_price_range DECIMAL(5,2),                   -- target cost per cocktail in USD
    uploaded_docs   JSONB,                             -- [{filename, s3_key, parsed_text_hash, parsed_at}]
    qdrant_namespace  VARCHAR(100),                    -- user-specific Qdrant collection name
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

## llm_usage
```sql
CREATE TABLE llm_usage (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID REFERENCES users(id),
    session_id    UUID REFERENCES chat_sessions(id),
    model         VARCHAR(100) NOT NULL,
    provider      VARCHAR(50) NOT NULL,
    tokens_input  INTEGER NOT NULL,
    tokens_output INTEGER NOT NULL,
    cost_usd      DECIMAL(8,6),
    latency_ms    INTEGER,
    cached        BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
```

## validation_failures
```sql
CREATE TABLE validation_failures (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cocktail_id   UUID REFERENCES cocktails(id),
    recipe_json   JSONB NOT NULL,
    issues        JSONB NOT NULL,                      -- [{type, severity, description}]
    regeneration_attempts INTEGER DEFAULT 0,
    final_status  VARCHAR(20),                         -- 'resolved' | 'unresolved_with_warning' | 'abandoned'
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
```

## ml_experiments
```sql
CREATE TABLE ml_experiments (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_name VARCHAR(255) NOT NULL,
    model_base    VARCHAR(100) NOT NULL,
    training_data_period TIMESTAMPTZ RANGE,
    hyperparams   JSONB,
    eval_metrics  JSONB,                               -- {loss, val_loss, taste_score_correlation}
    ab_test_traffic_percent INTEGER,
    ab_test_result JSONB,                              -- {improvement, statistical_significance}
    status        VARCHAR(50),                         -- 'training' | 'evaluating' | 'promoted' | 'rolled_back'
    mlflow_run_id VARCHAR(100),
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
```

---

---

# IMPLEMENTATION ROADMAP

## Phase 0: Foundation & Swarm Bootstrap (Weeks 1–2)
**Goal:** Working skeleton; agent swarm bootstrapped; event bus operational.

- [ ] Monorepo setup (`apps/web`, `apps/api`, `agents/`, `infra/`)
- [ ] Docker Compose for local dev (postgres, redis, qdrant, neo4j, nats, minio)
- [ ] NATS JetStream configuration (streams, consumers, replay policies)
- [ ] GitHub Actions CI pipeline (lint, type check, test, security scan, build)
- [ ] Database schema + Alembic migrations
- [ ] Auth service (Clerk webhook integration, JWT validation middleware)
- [ ] Agent Swarm Orchestrator baseline (skill registry, task router, container lifecycle)
- [ ] Telegram Gateway Service (bidirectional Telegram ↔ NATS normalization)
- [ ] Analyst agent: basic ticket creation from Telegram message
- [ ] Developer agent: basic file read/write + git commit + push
- [ ] QA agent: basic test execution + summary generation
- [ ] PM agent: basic release decision flow (approve/reject)
- [ ] Agent Memory baseline: Qdrant collection for episodic memory
- [ ] Health Monitor: heartbeat collection, auto-restart on failure

**Milestone:** Human PM sends feature request via Telegram → Analyst creates ticket → Developer implements stub → QA runs tests → PM approves mock release. Full swarm loop demonstrated.

---

## Phase 1: Core Chat MVP (Weeks 3–5)
**Goal:** Working chat with free-tier LLM, IBA knowledge base, and basic RAG.

- [ ] FastAPI Chat Service with Socket.io streaming
- [ ] Next.js 15 frontend: chat window + instruction panel + slash command autocomplete
- [ ] IBA cocktail data ingestion → Qdrant `iba_cocktails` collection
- [ ] Ingredient chemistry seed dataset (~100 common ingredients) → Qdrant + Neo4j
- [ ] Basic RAG retrieval pipeline (dense vector search, top-5, no reranking yet)
- [ ] LLM Gateway v1: Groq/Llama integration, basic routing, rate limiting
- [ ] `/create-cocktail` command end-to-end with JSON schema validation
- [ ] Safety filter: Llama Guard 3 baseline
- [ ] Response streaming via Socket.io with typing indicators
- [ ] Chat history persistence + session management
- [ ] Developer + QA swarm agents operational on real tickets; CI gate enforced

**Milestone:** Free user can chat, run `/create-cocktail`, receive a valid, safe cocktail suggestion using IBA context. Agent swarm has shipped at least 3 tickets end-to-end.

---

## Phase 2: Paid Tier & Bar Context (Weeks 6–8)
**Goal:** Paid tier functional; bar context working; knowledge graph operational.

- [ ] Stripe subscription integration (Checkout + Customer Portal + webhooks)
- [ ] LLM Gateway v2: Claude Sonnet + GPT-4.1 routing, circuit breakers, cost tracking
- [ ] User profile panel (frontend): concept text, inventory, style sliders, target price
- [ ] PDF/PNG upload → marker parser → chunk → embed → per-user Qdrant namespace
- [ ] Bar concept text ingestion + embedding
- [ ] Neo4j knowledge graph: ingredient nodes, pairing edges, incompatibility edges
- [ ] Multi-collection RAG retrieval (IBA + user context + chemistry)
- [ ] Hybrid search (dense + BM25 sparse vectors in Qdrant)
- [ ] Cross-encoder reranker integration
- [ ] Extended cocktails collection (seed with 50 curated high-quality recipes)
- [ ] `/menu-design` command (paid) with section grouping
- [ ] PM agent: full release decision flow with risk assessment

**Milestone:** Paid user can upload their menu, describe their bar, and receive contextually relevant suggestions with menu fit scoring. Agent swarm has shipped paid-tier features autonomously.

---

## Phase 3: Feedback Loop, Physical Validation & MLOps (Weeks 9–11)
**Goal:** Self-improving system; physically plausible outputs; fine-tuning pipeline ready.

- [ ] Deferred feedback survey UI (24h after generation, in-app + Telegram)
- [ ] `cocktail_feedback` table + feedback API endpoints
- [ ] Taste score calculation + `extended_cocktails` auto-promotion Celery beat job
- [ ] Ingredient chemistry knowledge base expansion (~300 ingredients)
- [ ] Physical validation engine: incompatibility, layering, pH, ABV, viscosity checks
- [ ] Regeneration loop on validation failure (max 2 attempts)
- [ ] Free user incentive: feedback → 14-day paid trial unlock
- [ ] Negative example injection into prompts (weekly batch job)
- [ ] MLOps pipeline: data prep → LoRA fine-tuning on Fireworks AI → MLflow tracking
- [ ] A/B test framework for model variants (10% traffic to fine-tuned model)
- [ ] Feedback text embeddings → `taste_feedback_embeddings` collection

**Milestone:** System rejects/repairs physically impossible recipes; high-rated cocktails enter the paid KB; first fine-tuned model trained and evaluated.

---

## Phase 4: Polish, Monitoring & Human UAT (Weeks 12–13)
**Goal:** Production-ready; full swarm workflow operational; real bartender UAT.

- [ ] Prometheus + Grafana dashboards (API latency, LLM usage/cost, feedback scores, agent task throughput)
- [ ] Loki log aggregation (application + agent logs)
- [ ] Sentry error tracking
- [ ] Full Telegram UAT flow with real bartender testers in group chat
- [ ] `/cost` command with user-defined price list + real-time cost lookup
- [ ] Chat history search + session management UI
- [ ] Rate limit UI feedback with upgrade prompt on quota hit
- [ ] Accessibility pass (WCAG 2.1 AA)
- [ ] Security audit (OWASP Top 10 review, penetration testing)
- [ ] Load testing with Locust/k6 (target: 100 concurrent users, p95 < 2s)
- [ ] Documentation: API docs (auto-generated from FastAPI), runbooks, agent skill registry

**Milestone:** Production deployment to staging; UAT sign-off from 5+ real bartenders via Telegram; PM agent approves merge to `main`; system handles 100+ daily active users.

---

## Phase 5: Swarm Intelligence & Scale (Post-MVP)
**Goal:** Agent swarm becomes self-improving; system scales to 1000+ users.

- [ ] Agent swarm auto-scaling: Orchestrator spins up additional Developer/QA replicas during high ticket volume
- [ ] Cross-agent learning: Developer agents share "best practice" snippets via Agent Memory
- [ ] Automated refactoring bot: periodically scans codebase for tech debt and proposes cleanup tickets
- [ ] Team tier: multi-user bar accounts, shared context, role-based permissions
- [ ] Kubernetes migration (Helm charts, HPA, ingress)
- [ ] CDN + edge caching for static assets
- [ ] Advanced analytics dashboard for bar managers (popularity trends, cost optimization)

---

---

# RISKS & TRADE-OFFS

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 1 | LLM generates physically impossible recipes | High | Medium | Chemistry KB + Knowledge Graph + post-generation validation (Part 2.2). Accept ~5% regeneration overhead. Fallback to human-reviewed recipe database for critical cases. |
| 2 | RAG retrieval returns irrelevant context (hallucination amplification) | Medium | High | Hybrid search (dense + BM25); cross-encoder reranker; query planning; knowledge graph constraints. Keep retrieved context concise (top-8). |
| 3 | PDF parsing fails on stylized menus / images | Medium | Medium | Primary: `marker` for layout-aware extraction. Fallback: GPT-4o Vision. Tertiary: manual text input with structured form. Surface parse confidence to user. |
| 4 | Groq API rate limits or downtime disrupt free tier | Medium | High | Circuit breaker → local Ollama fallback (slower but functional). Cache hit rate target: 30%+. Graceful degradation message in UI. |
| 5 | Low feedback submission rate undermines feedback loop | High | Medium | Deferred surveys (not immediate); 14-day trial incentive for free users; make survey feel lightweight (5 stars + 1 optional field); Telegram reminder bot. |
| 6 | Agent Developer makes large destructive commits | Low | High | Commit-size lint hook (<200 lines); CI gate rejecting diffs >300 lines without PM override; Agent Memory lookup before implementation to reduce exploration. |
| 7 | NATS / Telegram downtime breaks agent communication | Low | High | NATS: clustered deployment with replication. Telegram: GitHub Issues as fallback comms channel; Orchestrator persists event log and replays on recovery. |
| 8 | User bar context data privacy (uploaded menus) | Medium | High | Per-user Qdrant namespace; S3 server-side encryption; data never crosses to other users' LLM calls; GDPR delete endpoint; data processing agreement. |
| 9 | Cold start: no feedback data for extended KB | Certain | Medium | Seed `extended_cocktails` with 100 curated, vetted recipes + known high-rated classics. Use IBA as strong baseline. |
| 10 | Agent cost overrun (Claude API per agent call) | Medium | Medium | Task-type classifier: Haiku for simple tasks (file reads, test runs), Sonnet for implementation only. Token budget per agent task. |
| 11 | Fine-tuning pipeline produces degraded model | Medium | High | A/B test with 10% traffic; MLflow tracking; automatic rollback if taste_score drops; human bartender review gate before promotion. |
| 12 | Neo4j complexity exceeds MVP bandwidth | Medium | Medium | Start with KùzuDB (embedded, simpler) for MVP. Migrate to Neo4j only if graph query complexity demands it. |
| 13 | Socket.io scaling issues at 100+ concurrent users | Low | Medium | Redis adapter for Socket.io; horizontal scaling of Chat Service; connection limits per user. |

---

## Key Design Decisions & Trade-offs

**Qdrant + Neo4j over pgvector alone:**
pgvector would simplify the stack (one less service), but Qdrant offers sparse vectors (BM25), payload indexing, and superior ANN performance. Neo4j adds graph reasoning for ingredient relationships that vectors alone cannot express (e.g., transitive pairings). Trade-off: two additional services to operate, but significantly better retrieval quality and physical plausibility.

**NATS JetStream over Redis Pub/Sub or RabbitMQ:**
Redis Pub/Sub is ephemeral (messages lost on disconnect). RabbitMQ is powerful but complex. NATS JetStream provides durability, replay, consumer groups, and exactly-once semantics with minimal operational overhead. Trade-off: less ecosystem familiarity than Redis, but purpose-built for event-driven swarms.

**Custom RAG Orchestration over LlamaIndex/LangChain:**
LlamaIndex and LangChain are excellent for rapid prototyping but become rigid at scale. A custom orchestration layer (Query Planner → Hybrid Retriever → Graph Augmenter → Reranker → Context Assembler) provides full control over the retrieval pipeline, latency budgets, and cost tracking. Trade-off: more initial development; long-term flexibility and debuggability.

**Groq for free tier (not local Ollama):**
Groq provides cloud-hosted Llama with sub-second TTFT — critical for UX. Local Ollama requires GPU infrastructure. For MVP: Groq with Ollama as circuit-breaker fallback. Post-MVP: evaluate self-hosted vLLM on GPU instances vs. API cost at scale.

**Clerk over NextAuth.js:**
Clerk provides MFA, session management, organization support, and webhook infrastructure out of the box. NextAuth.js is more flexible but requires more custom code for the same features. Trade-off: vendor lock-in vs. faster MVP delivery.

**KùzuDB over Neo4j for MVP:**
KùzuDB is an embedded graph database (like SQLite for graphs) with Cypher support. It eliminates the operational overhead of Neo4j for MVP. If the knowledge graph grows beyond Kùzu's limits (millions of nodes), migrate to Neo4j. Trade-off: single-node only; no distributed queries.

**Conventional Commits + semantic-release:**
Automated changelog and versioning from commit messages aligns perfectly with the multi-agent developer workflow. The Developer agent produces structured commits; semantic-release handles versioning without human intervention. Enables fully automated releases once PM approves.

---

## Assumptions

1. IBA official cocktail data is used under fair use for non-commercial MVP; legal review required before commercial launch.
2. Groq API will remain in free/affordable tier during MVP development; Ollama fallback is tested and ready.
3. Telegram is accessible to all team members and target UAT testers; NATS cluster provides sufficient resilience.
4. Users will have modern browsers (Chrome, Firefox, Safari, Edge — last 2 versions); no IE11 support.
5. The chemistry knowledge base will be bootstrapped manually by a domain expert (bartender or food scientist) for the first ~200 ingredients — no automated ingestion source exists.
6. "Paid tier" pricing is TBD (not in scope for this design document); Stripe integration supports flexible price IDs.
7. At least one GPU-enabled machine is available for Ollama fallback and local embedding inference (even a consumer RTX 4090 is sufficient for 7B models).
8. Real bartenders for UAT are recruited before Phase 4 begins; their feedback is critical for taste score calibration.
