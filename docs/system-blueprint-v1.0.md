# Technical Specification & Design Document
## Bartender AI Assistant — Full System Blueprint
**Version:** 1.0 | **Date:** 2026-05-11 | **Status:** Draft for Review

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

1. **The Builder** — A multi-agent AI development team (Analyst, Developer, QA/Tester, Project Manager) that builds and ships software via a feature-branch/TDD/CI-CD workflow, with all human-agent and agent-agent communication routed through Telegram.
2. **The Product** — A web-based personal AI assistant for bartenders, with tiered subscriptions, a RAG-backed knowledge base, a feedback-driven taste metric, and a physical realizability layer.

---

---

# PART 0 — MULTI-AGENT DEVELOPMENT SYSTEM

## 0.1 Agent Roles & Responsibilities

### Analyst
- **Trigger:** New feature request message sent to the Telegram group or directly to the Analyst bot.
- **Inputs:** Raw user story / PM directive / bug report.
- **Outputs:** Structured ticket set (JSON) committed to a `tickets/` directory in the repo, and a summary posted back to Telegram.
- **Behaviors:**
  - Clarifies ambiguous requirements by posting follow-up questions to the Telegram thread.
  - Decomposes large features into atomic, testable tickets (Acceptance Criteria format).
  - Tags tickets: `feature`, `bug`, `chore`, `spike`.
  - Assigns estimated complexity (S/M/L/XL) and priority.
- **Tools (Claude tool-use functions):**
  - `git_create_branch(ticket_id)` — creates `feature/<ticket_id>` branch off `dev`
  - `write_ticket(ticket)` — commits ticket JSON to repo
  - `telegram_post(chat_id, message)` — sends formatted summary

### Developer
- **Trigger:** New ticket committed by Analyst (watched via GitHub webhook → webhook handler notifies Developer bot).
- **Inputs:** Ticket JSON, codebase access.
- **Outputs:** Commits on `dev` branch; pushes and notifies QA when work is complete.
- **Behaviors:**
  - Works **exclusively on `dev` branch** (or `feature/<ticket_id>` sub-branches merged to dev).
  - Follows TDD: writes failing test first, then implementation, then refactors.
  - Makes small, logically scoped commits with conventional commit messages.
  - Proactively asks Analyst for clarification via Telegram if a requirement is ambiguous.
  - Does **not** merge to `main` independently — awaits PM instruction.
- **Tools:**
  - `read_file(path)`, `write_file(path, content)`, `run_tests()`, `git_commit(msg)`, `git_push(branch)`
  - `telegram_post(chat_id, message)`

### QA / Tester
- **Trigger:** Developer posts "ready for QA" message to Telegram with branch name.
- **Inputs:** `dev` branch, ticket acceptance criteria.
- **Outputs:** Formal **Test Summary Report** (JSON + human-readable) posted to Telegram.
- **Behaviors:**
  - Checks out `dev`, runs full test suite.
  - Maps each acceptance criterion to a specific test or manual check.
  - Reports: ✅ pass / ❌ fail / ⚠️ partial, with line-level evidence.
  - Calculates code coverage delta.
  - Posts UAT notification to Telegram group when ready for human testing.
  - Can open GitHub Issues tagging Developer for blockers.
- **Tools:**
  - `run_tests()`, `get_coverage()`, `read_file(path)`
  - `telegram_post(chat_id, message)`, `github_create_issue(title, body)`

### Project Manager (PM)
- **Trigger:** QA posts Test Summary Report to Telegram.
- **Inputs:** Test Summary, ticket backlog, sprint goals.
- **Outputs:** Release decision posted to Telegram; merge instruction to Developer or loop-back to Analyst/Developer.
- **Behaviors:**
  - Evaluates pass/fail against acceptance criteria.
  - If **approved**: instructs Developer to merge `dev` → `main`, tags a release.
  - If **rejected**: annotates which criteria failed, routes back to Developer (code fix) or Analyst (requirement clarification) with specific action items.
  - Maintains a sprint velocity log in `pm/velocity.json`.
- **Tools:**
  - `telegram_post(chat_id, message)`, `github_merge_pr(pr_number)`, `write_file(path, content)`

---

## 0.2 Agent Communication Architecture

### Telegram Bot Integration

Each agent is a standalone Python service (`agent-analyst/`, `agent-developer/`, `agent-qa/`, `agent-pm/`) built on:
- `python-telegram-bot` (async, v21+)
- `anthropic` Python SDK (Claude claude-sonnet-4-6 or claude-opus-4-7 depending on task complexity)
- Tool-use function calling mapped to local executor functions

**Bot setup:**
- Each bot is registered via BotFather with its own API token.
- All four bots are added to a **shared Telegram group** (the "war room").
- Bots use `/command` prefixes to direct messages (e.g., `@AnalystBot /analyze <story>`).
- Agent-to-agent messages are sent via the group using `@mentions`, so all participants see the full conversation thread — full auditability.
- For private escalation (e.g., PM → Developer with sensitive context), bots support direct 1:1 Telegram DM as well.

**Human UAT flow:**
- QA posts a message in the group: `🧪 UAT ready: [feature name] deployed to staging. Test URL: https://staging.bartender-ai.app`
- Human testers interact with staging and reply in-thread.
- QA bot reads replies (via `getUpdates` or webhook), synthesizes feedback, and appends it to the Test Summary.

### Webhook & Event Architecture

```
GitHub Webhook (push, PR events)
        │
        ▼
Webhook Dispatcher Service (FastAPI)
        │
   ┌────┴────────────────┐
   │                     │
Analyst Bot          Developer Bot
(ticket events)     (CI/PR events)
        │
   QA Bot ◄──── GitHub Actions (test results posted as webhook)
        │
   PM Bot
```

- GitHub Actions posts test results as a webhook payload to the Dispatcher.
- The Dispatcher routes events to the appropriate agent bot.

---

## 0.3 Agent Interaction Flow (Sequence Diagram)

```
Human/PM          Analyst          Developer          QA/Tester          PM Bot         CI/CD
    │                 │                │                   │               │               │
    │─ /analyze ─────►│                │                   │               │               │
    │                 │ (decompose)     │                   │               │               │
    │◄─ tickets ──────│                │                   │               │               │
    │                 │─ new ticket ──►│                   │               │               │
    │                 │                │ (write tests)      │               │               │
    │                 │                │ (implement)        │               │               │
    │                 │                │─── push dev ──────────────────────────────────────►│
    │                 │                │                   │               │   (run CI)    │
    │                 │                │◄──────────────────────────────────────── result ──│
    │                 │                │─ "ready for QA" ─►│               │               │
    │                 │                │                   │ (checkout dev)│               │
    │                 │                │                   │ (run tests)   │               │
    │                 │                │                   │ (UAT notify)  │               │
    │◄── UAT URL ─────────────────────────────────────────│               │               │
    │ (test staging)  │                │                   │               │               │
    │─ feedback ──────────────────────────────────────────►│               │               │
    │                 │                │                   │─ Test Summary ►│               │
    │                 │                │                   │               │ (evaluate)    │
    │                 │                │                   │               │               │
    │                 │           [APPROVED]               │               │               │
    │                 │                │◄── merge dev→main ─────────────── │               │
    │                 │                │────────────────────────────────────────────────── ►│
    │                 │                │                   │               │  (deploy)     │
    │                 │                │                   │               │               │
    │                 │           [REJECTED]               │               │               │
    │                 │◄── re-analyze ─────────────────────────────────── │               │
    │                 │   OR          │◄── fix & re-implement ────────────│               │
```

---

## 0.4 Supporting Tooling

| Tool | Purpose |
|------|---------|
| **Git / GitHub** | Source of truth; feature-branch workflow; PR-based merge gates |
| **GitHub Actions** | CI: lint, unit tests, integration tests, coverage report, Docker build |
| **Docker Compose** | Local dev environment; identical to staging |
| **pytest + coverage.py** | Python test runner with coverage enforcement (≥80% line coverage gate) |
| **Telegram Bot API** | Agent ↔ agent and agent ↔ human communication |
| **FastAPI Webhook Dispatcher** | Routes GitHub/CI events to correct agent bot |
| **Conventional Commits** | Enforced via `commitlint`; enables automated changelog generation |
| **semantic-release** | Automated versioning and release notes from commit history |

---

## 0.5 Quality & Velocity Mechanisms

- **TDD gate:** CI fails if new code lacks corresponding tests.
- **Coverage gate:** PRs blocked if coverage drops below threshold.
- **Commit size policy:** Agent (Developer) is prompted to keep commits under ~200 lines of diff; larger changes trigger a Telegram warning.
- **Sprint cadence:** PM agent tracks cycle time per ticket; posts weekly velocity digest to Telegram.
- **Agile ceremonies:** All handled in Telegram via scheduled messages (daily standup summary, sprint review at milestone completion).

---

---

# PART 1 — TARGET APPLICATION: BARTENDER AI ASSISTANT

## 1.1 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (Next.js 14)                       │
│  ┌──────────────┐   ┌──────────────────┐   ┌─────────────────────┐  │
│  │  Chat Window │   │ Instruction Panel│   │  Profile / Context  │  │
│  │  (slash cmds)│   │  (slash help)    │   │  Panel (paid only)  │  │
│  └──────┬───────┘   └──────────────────┘   └─────────────────────┘  │
└─────────┼───────────────────────────────────────────────────────────┘
          │ HTTPS / WebSocket
┌─────────▼───────────────────────────────────────────────────────────┐
│                        API GATEWAY (Nginx / Traefik)                 │
│         Auth middleware · Rate limiting · TLS termination            │
└────┬──────────────┬──────────────────┬───────────────────┬──────────┘
     │              │                  │                   │
┌────▼────┐  ┌──────▼──────┐  ┌────────▼────────┐  ┌─────▼────────┐
│  Auth   │  │  Chat /     │  │  User / Profile  │  │  Subscription│
│ Service │  │  AI Service │  │  Service         │  │  Service     │
│(FastAPI)│  │  (FastAPI)  │  │  (FastAPI)       │  │  (FastAPI)   │
└────┬────┘  └──────┬──────┘  └────────┬─────────┘  └─────┬────────┘
     │              │                  │                   │
     │         ┌────▼──────────────────▼───────────────────▼────────┐
     │         │                   PostgreSQL                         │
     │         │      users · subscriptions · chat_sessions ·        │
     │         │      messages · cocktails · feedback                 │
     │         └──────────────────────────────────────────────────────┘
     │              │
     │         ┌────▼────────────────────────────────────────────────┐
     │         │                  LLM GATEWAY SERVICE                  │
     │         │   Routes by tier · Rate limiter · Data isolation      │
     │         │                                                        │
     │         │  ┌──────────────┐        ┌────────────────────────┐  │
     │         │  │  Free Tier   │        │      Paid Tier         │  │
     │         │  │  Llama 3.1   │        │  Claude Sonnet / GPT-4o│  │
     │         │  │  (Groq API)  │        │  (Anthropic / OAI API) │  │
     │         │  └──────────────┘        └────────────────────────┘  │
     │         └────┬────────────────────────────────────────────────┘
     │              │
     │         ┌────▼────────────────────────────────────────────────┐
     │         │                    RAG SERVICE                        │
     │         │                                                        │
     │         │  ┌──────────────────────────────────────────────────┐ │
     │         │  │              Qdrant Vector Store                   │ │
     │         │  │  Collection: iba_cocktails (free + paid)           │ │
     │         │  │  Collection: extended_cocktails (paid only)        │ │
     │         │  │  Collection: ingredient_chemistry (all)            │ │
     │         │  │  Collection: user_bar_context (paid, per-user)     │ │
     │         │  └──────────────────────────────────────────────────┘ │
     │         └─────────────────────────────────────────────────────┘
     │
┌────▼──────────────────────────────────────────────────────────────┐
│                      Redis (Cache + Rate Limit)                     │
│        Session tokens · LLM response cache · Rate counters          │
└───────────────────────────────────────────────────────────────────┘
```

---

## 1.2 Frontend Design

### Technology
- **Framework:** Next.js 14 (App Router, React Server Components)
- **UI Library:** shadcn/ui + Tailwind CSS
- **State:** Zustand (global chat state), React Query (server state/caching)
- **Real-time:** WebSocket via `socket.io-client` (streaming LLM tokens)
- **Auth:** next-auth with JWT session (or Clerk for faster MVP)

### Main Screen Layout
```
┌─────────────────────────────────────────────────────────────┐
│  [Logo] BartenderAI          [Plan: Free ▾]  [Profile] [⚙️]  │
├───────────────────────────────────────┬─────────────────────┤
│                                       │  QUICK GUIDE        │
│   Chat Window                         │  ─────────────────  │
│   ─────────────────────────────────   │  /help              │
│   │ 🤖 Welcome! I'm your bartending  │  List all commands  │
│   │    AI assistant. Try:             │                     │
│   │    /create-cocktail               │  /create-cocktail   │
│   │    /cost                          │  Generate a recipe  │
│   │    /help                          │  from your prompt   │
│   ─────────────────────────────────   │                     │
│                                       │  /cost              │
│   [Message input + send button]       │  Calculate cost of  │
│   [Slash command autocomplete]        │  a recipe           │
│                                       │                     │
│                                       │  ✨ Upgrade for     │
│                                       │  premium models +   │
│                                       │  bar context        │
└───────────────────────────────────────┴─────────────────────┘
```

### Slash Command System
Commands are parsed client-side before sending:
- `/help` — returns available command list + brief description
- `/create-cocktail [prompt]` — cocktail generation flow
- `/cost [recipe or cocktail name]` — cost calculation
- `/menu-design [concept]` — (paid) full menu generation
- `/suggest [flavor profile]` — quick recommendation
- `/my-context` — (paid) view/edit bar context

Command parsing: `if (input.startsWith('/'))` → extract command + args → set `messageType` in payload.

---

## 1.3 Core Chat & AI Service

### Request Flow
1. Client sends `POST /api/chat/message` with `{ session_id, content, command?, user_id }`.
2. Chat Service authenticates, loads user subscription tier.
3. Calls **RAG Service** to retrieve relevant cocktail/chemistry context.
4. Constructs prompt (system prompt + retrieved context + conversation history).
5. Calls **LLM Gateway** with the assembled prompt.
6. Streams response back to client via WebSocket.
7. Persists message + response to `messages` table.

### System Prompt Template (base)
```
You are BartenderAI, a professional assistant for bartenders and bar managers.
You specialize in cocktail creation, menu design, and bar operations.

Rules:
- Never suggest recipes with unsafe ingredient combinations.
- Filter any toxic, profane, or inappropriate content.
- Always return cocktail suggestions in the specified JSON schema.
- For physical plausibility, apply the layering/density rules from the provided context.

Retrieved Knowledge:
{rag_context}

{user_bar_context_if_paid}

User subscription: {tier}
Conversation history: {history_summary}
```

---

## 1.4 LLM Gateway Service

### Routing Logic
```python
def route_llm(user_tier: str, prompt: TokenizedPrompt) -> LLMResponse:
    if user_tier == "free":
        model = "llama-3.1-70b-versatile"   # via Groq API
        max_tokens = 1024
        rate_limit_key = f"rl:free:{user_id}"
        rate_limit_rpm = 10
    elif user_tier == "paid":
        model = "claude-sonnet-4-6"          # via Anthropic API
        max_tokens = 4096
        rate_limit_key = f"rl:paid:{user_id}"
        rate_limit_rpm = 60
```

### Rate Limiting
- Implemented in Redis with sliding-window counters.
- Enforced at the Gateway level before calling any LLM provider.
- Quota exceeded → HTTP 429 with `Retry-After` header and upgrade prompt.

### Data Isolation
- Paid user bar context is **never injected** into free user prompts.
- Per-user Qdrant namespace/collection partitioning for user-uploaded documents.
- LLM providers receive no PII in prompts — user IDs are pseudonymized.

### Safety Filtering
- **Pre-generation:** Prompt is checked against an OpenAI Moderation API call (or Llama Guard for the free tier stack) before forwarding.
- **Post-generation:** Response is scanned for toxic content before returning to client.
- Flagged responses are logged, blocked, and a safe fallback is returned.

---

## 1.5 RAG Pipeline

### Knowledge Base Structure

| Collection | Contents | Access |
|------------|----------|--------|
| `iba_cocktails` | ~90 IBA official cocktail recipes (name, ingredients, method, garnish, glass) | Free + Paid |
| `extended_cocktails` | Community-generated cocktails with ≥4-star feedback rating | Paid only |
| `ingredient_chemistry` | Physical/chemical properties: density, ABV, miscibility, flavor pairings, aroma compounds | All tiers |
| `user_bar_context_{user_id}` | Uploaded menus (PDF/PNG parsed), bar concept text, inventory | Paid, per-user |

### Ingestion Pipeline

```
IBA Data Source (JSON/web scrape)
        │
        ▼
Ingestion Worker (Python)
  - Parse & normalize to CocktailSchema
  - Chunk: one document per cocktail
  - Embed: text-embedding-3-small (OpenAI) or
           all-MiniLM-L6-v2 (local, free tier)
        │
        ▼
Qdrant Upsert (collection: iba_cocktails)
        │
        ▼
Embedding index ready for retrieval
```

**PDF / Image Upload (Paid users):**
```
User uploads PDF/PNG
        │
        ▼
Upload Service (S3/MinIO storage)
        │
        ▼
Document Parser
  - PDF: PyMuPDF text extraction + table detection
  - Image: Tesseract OCR or GPT-4o Vision
        │
        ▼
Text chunked (512 tokens, 50-token overlap)
        │
        ▼
Embed + Upsert → user_bar_context_{user_id} collection
```

### Retrieval Strategy

1. **Query embedding** — embed the user's cocktail prompt.
2. **Multi-collection retrieval:**
   - Always query `iba_cocktails` (free users) or `iba_cocktails` + `extended_cocktails` (paid).
   - Always query `ingredient_chemistry` for plausibility constraints.
   - If paid: query `user_bar_context_{user_id}`.
3. **Reranking** — use a cross-encoder (ms-marco-MiniLM-L-6-v2) to rerank top-20 results to top-5.
4. **Context assembly** — inject top-5 passages into system prompt under `{rag_context}`.

---

## 1.6 Subscription & Tier System

### Subscription Service
- **Payment:** Stripe integration; webhooks update `subscriptions` table.
- **Tiers:**
  - `free` — default on registration
  - `paid` — monthly or annual; unlocks premium LLM, RAG extensions, bar context

### Feature Gate Enforcement
- JWT contains `tier` claim, re-issued on subscription change.
- Backend middleware validates `tier` on every protected endpoint.
- Frontend conditionally renders paid features with upgrade CTA for free users.

---

## 1.7 Response Format

All cocktail generation responses conform to this schema:

```json
{
  "suggestions": [
    {
      "name": "Midnight Smoke",
      "description": "A smoky, spirit-forward cocktail with a long finish.",
      "ingredients": [
        { "name": "Mezcal", "quantity": 45, "unit": "ml" },
        { "name": "Sweet Vermouth", "quantity": 20, "unit": "ml" },
        { "name": "Amaro Nonino", "quantity": 10, "unit": "ml" },
        { "name": "Orange Bitters", "quantity": 2, "unit": "dashes" }
      ],
      "method": "Stir with ice for 30 seconds. Strain into chilled coupe.",
      "glass": "Coupe",
      "garnish": "Orange peel twist",
      "tasting_notes": {
        "aroma": "Smoke, dried fruit, herbal bitterness",
        "palate": "Rich, smoky, bittersweet with earthy undertones",
        "finish": "Long, warming, slightly smoky"
      },
      "estimated_cost_per_serving": null
    }
  ],
  "count": 1,
  "safety_check": "passed"
}
```

The LLM is instructed to return 1–3 suggestions. The system parses, validates schema, and if `safety_check` fails, substitutes a safe fallback message.

---

---

# PART 2 — KNOWN CHALLENGES & SOLUTIONS

## 2.1 Measurable Taste Metric & Feedback Loop

### Problem
"Good" is subjective. Without a structured feedback mechanism, the system cannot improve and has no way to distinguish genuinely excellent suggestions from mediocre ones.

### Solution: Structured Taste Survey + Rating Pipeline

**After real-world test (post-serving, not immediately after generation):**
A follow-up message is sent (via app notification or Telegram) with a mini-survey:

```
How did the cocktail land?

Overall: ★ ★ ★ ★ ★
Balance (sweet/sour/bitter): ★ ★ ★ ★ ★
Aroma: ★ ★ ★ ★ ★
Appearance: ★ ★ ★ ★ ★
Guest reaction: 😞 😐 🙂 😄 🤩
Would you make it again? Yes / No / Modified
[Optional text note]
```

**Feedback Schema:**
```
cocktail_feedback {
  id, cocktail_id, user_id,
  overall_rating (1-5),
  balance_rating (1-5),
  aroma_rating (1-5),
  appearance_rating (1-5),
  guest_reaction (1-5),
  would_repeat (bool),
  notes (text),
  created_at
}
```

**Composite Taste Score:**
```
taste_score = 0.35 * overall + 0.25 * balance + 0.20 * aroma + 0.10 * appearance + 0.10 * guest_reaction
```

**Feedback Loop Actions:**
- `taste_score ≥ 4.0` → cocktail eligible for ingestion into `extended_cocktails` KB (paid tier sees it immediately).
- `taste_score 3.0–3.9` → cocktail flagged for review; prompt refinement via few-shot negative example injection.
- `taste_score < 3.0` → cocktail marked `deprecated`; used as negative example in prompt.
- **Incentive for free users:** "Contribute 5 high-rated cocktails → unlock 30 days of paid features." This drives feedback submission and serves as an upgrade funnel.

**Prompt Refinement (RLHF-lite):**
- Weekly batch job re-embeds top/bottom cocktails.
- Top cocktails → added as few-shot positive examples in the generation prompt.
- Bottom cocktails → added as explicit negative examples (`"Do not generate cocktails similar to: [...]"`).

---

## 2.2 Physical Realizability

### Problem
An LLM can hallucinate physically impossible cocktail recipes (e.g., a layered cocktail where the denser liquid is on top, or a combination of ingredients that curdles or denatures proteins).

### Solution: Ingredient Chemistry RAG + Post-Generation Validation

**Chemistry Knowledge Base (ingested once, maintained manually + via community):**
Each ingredient document contains:
```json
{
  "name": "Lime Juice",
  "density_g_per_ml": 1.03,
  "abv": 0.0,
  "ph": 2.3,
  "flavor_family": ["sour", "citrus"],
  "miscibility": ["water-based", "citrus acids"],
  "known_incompatibilities": ["cream", "dairy"],
  "aroma_compounds": ["limonene", "citral"],
  "layering_position": "top"
}
```

**Pre-generation retrieval:**
- All ingredients mentioned in the user prompt are resolved against the chemistry KB.
- Compatibility rules are injected into the system prompt.

**Post-generation validation (rule-based check):**
```python
def validate_recipe(ingredients: list[Ingredient]) -> ValidationResult:
    issues = []
    for a, b in combinations(ingredients, 2):
        if b.name in a.known_incompatibilities:
            issues.append(f"{a.name} and {b.name} are incompatible")
    if recipe.method == "layered":
        validate_density_order(ingredients, issues)
    return ValidationResult(valid=len(issues)==0, issues=issues)
```

If validation fails:
- The LLM is prompted to regenerate with the validation errors as constraints.
- Maximum 2 regeneration attempts; if still failing, return partial result with a warning note in the UI.

---

## 2.3 Local Bar Context for Paid Users (Zero-Shot Meta-Learning)

### Problem
Generic cocktail suggestions are less useful to a bartender at a Japanese whisky bar than to one at a tropical resort. Without local context, suggestions feel impersonal.

### Solution: Bar Context Profile + Per-User RAG Collection

**User Profile Panel (paid tier):**
- Text field: "Describe your bar concept" (e.g., "Speakeasy with focus on American whiskey, 1920s aesthetic, 40-seat room").
- Upload: Current menu PDF or PNG (parsed → chunked → embedded → `user_bar_context_{user_id}`).
- Inventory list: Free-text or structured ingredient list.

**Context Injection at Query Time:**
1. Retrieve top-5 passages from `user_bar_context_{user_id}` via semantic search.
2. Also query global `iba_cocktails` and `ingredient_chemistry` collections.
3. Merge and inject all context into system prompt under `{user_bar_context}` block.

**Zero-Shot Meta-Learning Mechanism:**
- The bar concept text is embedded and matched against the `extended_cocktails` collection using cosine similarity.
- Top-matched cocktails from similar bar concepts (anonymized) are surfaced as inspirational references.
- Prompt instructs the LLM: _"The following cocktails were popular in bars with similar concepts: [matches]. Use these as style inspiration, not as direct copies."_

**Inventory-Aware Generation:**
- If inventory is provided, generation is constrained: _"Only suggest cocktails that can be made using the bar's current inventory. Unavailable ingredients: [list]."_

---

---

# TECHNOLOGY STACK

## Backend
| Component | Technology | Rationale |
|-----------|------------|-----------|
| API Services | FastAPI (Python 3.12) | Async, type-safe, auto-docs; native Pydantic v2 |
| Database ORM | SQLAlchemy 2.0 + Alembic | Async ORM; migrations |
| Primary DB | PostgreSQL 16 | ACID, JSON support, proven |
| Cache / Rate Limit | Redis 7 | Sub-ms latency; atomic counters |
| Vector DB | Qdrant | Filtering by collection; Rust-based; self-hostable |
| Message Queue | Celery + Redis | Background jobs (ingestion, feedback batch) |
| Object Storage | MinIO (S3-compatible) | Self-hosted; PDF/image uploads |
| PDF Parsing | PyMuPDF + pdfplumber | Layout-aware extraction |
| OCR | Tesseract / GPT-4o Vision | Image menus |

## Frontend
| Component | Technology |
|-----------|------------|
| Framework | Next.js 14 (App Router) |
| UI | shadcn/ui + Tailwind CSS v4 |
| State (global) | Zustand |
| Server state | TanStack Query v5 |
| Real-time | socket.io-client |
| Auth | NextAuth.js v5 |
| Payments | Stripe.js |

## AI / ML
| Component | Technology |
|-----------|------------|
| Free tier LLM | Llama 3.1 70B via Groq API |
| Paid tier LLM | Claude claude-sonnet-4-6 (Anthropic) |
| Embedding model | text-embedding-3-small (OpenAI) / all-MiniLM-L6-v2 (local) |
| Reranker | ms-marco-MiniLM-L-6-v2 (local, via sentence-transformers) |
| RAG orchestration | LlamaIndex (for flexibility + multi-collection support) |
| Safety filter | Llama Guard 2 (local, free) / OpenAI Moderation (paid) |

## Multi-Agent System
| Component | Technology |
|-----------|------------|
| Agent framework | Anthropic Python SDK (tool use) |
| Telegram interface | python-telegram-bot v21 (async) |
| CI/CD | GitHub Actions |
| Container | Docker + Docker Compose |
| Versioning | semantic-release + conventional commits |

## Infra / Ops
| Component | Technology |
|-----------|------------|
| Container orchestration | Docker Compose (MVP) → Kubernetes (post-MVP) |
| Reverse proxy | Nginx or Traefik |
| Monitoring | Prometheus + Grafana |
| Logging | Loki + Grafana |
| Secrets | HashiCorp Vault or Doppler |

---

---

# DATA MODELS

## users
```sql
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) UNIQUE NOT NULL,
    name        VARCHAR(255),
    hashed_pw   VARCHAR(255) NOT NULL,
    tier        VARCHAR(20) NOT NULL DEFAULT 'free',   -- 'free' | 'paid'
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
    plan             VARCHAR(50) NOT NULL,             -- 'monthly' | 'annual'
    status           VARCHAR(50) NOT NULL,             -- 'active' | 'canceled' | 'past_due'
    current_period_start TIMESTAMPTZ,
    current_period_end   TIMESTAMPTZ,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);
```

## chat_sessions
```sql
CREATE TABLE chat_sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(255),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
```

## messages
```sql
CREATE TABLE messages (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id   UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role         VARCHAR(20) NOT NULL,                  -- 'user' | 'assistant'
    content      TEXT NOT NULL,
    command      VARCHAR(50),
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
```

## cocktails
```sql
CREATE TABLE cocktails (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    ingredients     JSONB NOT NULL,
    method          TEXT,
    glass           VARCHAR(100),
    garnish         VARCHAR(255),
    tasting_notes   JSONB,
    source          VARCHAR(50) NOT NULL,              -- 'iba' | 'generated' | 'user'
    created_by      UUID REFERENCES users(id),
    taste_score     DECIMAL(3,2),
    is_deprecated   BOOLEAN DEFAULT FALSE,
    embedding_id    VARCHAR(255),                      -- Qdrant point ID
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

## cocktail_feedback
```sql
CREATE TABLE cocktail_feedback (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cocktail_id      UUID REFERENCES cocktails(id),
    user_id          UUID REFERENCES users(id),
    overall_rating   SMALLINT CHECK (overall_rating BETWEEN 1 AND 5),
    balance_rating   SMALLINT CHECK (balance_rating BETWEEN 1 AND 5),
    aroma_rating     SMALLINT CHECK (aroma_rating BETWEEN 1 AND 5),
    appearance_rating SMALLINT CHECK (appearance_rating BETWEEN 1 AND 5),
    guest_reaction   SMALLINT CHECK (guest_reaction BETWEEN 1 AND 5),
    would_repeat     BOOLEAN,
    notes            TEXT,
    taste_score      DECIMAL(3,2) GENERATED ALWAYS AS (
        0.35 * overall_rating + 0.25 * balance_rating +
        0.20 * aroma_rating + 0.10 * appearance_rating +
        0.10 * guest_reaction
    ) STORED,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);
```

## user_bar_context
```sql
CREATE TABLE user_bar_context (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    concept_text    TEXT,
    inventory       JSONB,
    uploaded_docs   JSONB,                             -- [{filename, s3_key, parsed_at}]
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

---

# IMPLEMENTATION ROADMAP

## Phase 0: Foundation (Weeks 1–2)
**Goal:** Working skeleton; agent system bootstrapped.

- [ ] Repo setup (monorepo: `apps/web`, `apps/api`, `agents/`)
- [ ] Docker Compose for local dev (postgres, redis, qdrant, minio)
- [ ] GitHub Actions CI pipeline (lint, test, build)
- [ ] Database schema + Alembic migrations
- [ ] Auth service (register, login, JWT)
- [ ] Telegram bots registered; echo-bot baseline
- [ ] Analyst agent: basic ticket creation from Telegram message

**Milestone:** Developer can send a feature request to Telegram → Analyst creates a structured ticket.

---

## Phase 1: Core Chat MVP (Weeks 3–5)
**Goal:** Working chat with free-tier LLM and IBA knowledge base.

- [ ] FastAPI Chat Service with `POST /chat/message`
- [ ] Next.js frontend: chat window + instruction panel
- [ ] IBA cocktail data ingestion → Qdrant `iba_cocktails` collection
- [ ] RAG retrieval pipeline (basic cosine similarity, no reranking yet)
- [ ] LLM Gateway: Groq/Llama integration, basic routing
- [ ] `/create-cocktail` command end-to-end
- [ ] Response schema validation + safety filter (Llama Guard)
- [ ] WebSocket streaming for LLM responses
- [ ] Developer + QA agents operational; CI gate enforced

**Milestone:** Free user can chat, run `/create-cocktail`, receive a valid cocktail suggestion using IBA context.

---

## Phase 2: Paid Tier & Bar Context (Weeks 6–8)
**Goal:** Paid tier fully functional; bar context working.

- [ ] Stripe subscription integration
- [ ] LLM Gateway: Claude claude-sonnet-4-6 routing for paid users
- [ ] User profile panel (frontend)
- [ ] PDF/PNG upload → parse → embed → per-user Qdrant collection
- [ ] Bar concept text ingestion
- [ ] Multi-collection RAG retrieval (IBA + user context)
- [ ] Extended cocktails collection (seed with 50 high-quality community recipes)
- [ ] `/menu-design` command (paid)
- [ ] PM agent: release decision flow operational

**Milestone:** Paid user can upload their menu, describe their bar, and receive contextually relevant suggestions.

---

## Phase 3: Feedback Loop & Physical Validation (Weeks 9–11)
**Goal:** Self-improving system; physically plausible outputs.

- [ ] Feedback survey UI (post-generation prompt + deferred survey)
- [ ] `cocktail_feedback` table + feedback API endpoints
- [ ] Taste score calculation + `extended_cocktails` auto-promotion job
- [ ] Ingredient chemistry knowledge base (build initial dataset: ~200 common bar ingredients)
- [ ] Chemistry ingestion pipeline + Qdrant `ingredient_chemistry` collection
- [ ] Post-generation validation engine (incompatibility + layering checks)
- [ ] Regeneration loop on validation failure
- [ ] Free user incentive: feedback → upgrade unlock
- [ ] Negative example injection into prompts (weekly batch job)

**Milestone:** System rejects/repairs physically impossible recipes; high-rated cocktails enter the paid KB.

---

## Phase 4: Polish, Monitoring & UAT (Weeks 12–13)
**Goal:** Production-ready; full agent workflow operational.

- [ ] Prometheus + Grafana dashboards (latency, LLM usage, feedback scores)
- [ ] Loki log aggregation
- [ ] Error tracking (Sentry)
- [ ] Full Telegram UAT flow with human testers
- [ ] `/cost` command (ingredient cost calculation with user-defined price list)
- [ ] Chat history UI (search, session management)
- [ ] Rate limit UI feedback (upgrade prompt on quota hit)
- [ ] Accessibility pass (WCAG 2.1 AA)
- [ ] Security audit (OWASP Top 10 review)

**Milestone:** Production deployment on staging; UAT sign-off from real bartenders via Telegram; PM agent approves merge to main.

---

---

# RISKS & TRADE-OFFS

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 1 | LLM generates physically impossible recipes | High | Medium | Chemistry KB + post-generation validation (Part 2.2). Accept ~5% regeneration overhead. |
| 2 | RAG retrieval returns irrelevant context (hallucination amplification) | Medium | High | Cross-encoder reranking; keep retrieved context short (top-5); always include IBA as ground truth baseline. |
| 3 | PDF parsing fails on stylized menus / images | Medium | Medium | Fallback to GPT-4o Vision for images; surface parse errors to user with manual text input option. |
| 4 | Groq API rate limits disrupt free tier | Medium | Medium | Local Ollama fallback for Llama (slower but offline-capable); configurable fallback in LLM Gateway. |
| 5 | Low feedback submission rate undermines feedback loop | High | Medium | In-app nudges (deferred, not immediate); upgrade incentive for free users; make survey feel lightweight (5 stars, 15 seconds). |
| 6 | Agent Developer bot makes large destructive commits | Low | High | Commit-size lint hook; CI gate rejecting diffs >300 lines without explicit PM override. |
| 7 | Telegram as primary agent comms channel — downtime | Low | High | GitHub Issues as fallback communication; webhook dispatcher can log events and replay. |
| 8 | User bar context data privacy (uploaded menus) | Medium | High | Per-user Qdrant namespacing; S3 server-side encryption; data never crosses to other users' LLM calls; GDPR delete endpoint. |
| 9 | Cold start: no feedback data for extended KB | Certain | Medium | Seed `extended_cocktails` manually with 50–100 curated, vetted cocktail recipes before launch. |
| 10 | Agent cost overrun (Claude API costs per developer bot call) | Medium | Medium | Agent Developer bot uses Sonnet for implementation; switch to Haiku for simple tasks (file reads, test runs). Task-type classifier gate. |

---

## Key Design Decisions & Trade-offs

**Qdrant over pgvector:**
pgvector would simplify the stack (one less service), but Qdrant offers per-collection filtering, payload indexing, and superior ANN performance at scale — critical for multi-tenant bar context isolation. For very early MVP, pgvector is acceptable as a temporary simplification.

**LlamaIndex over LangChain:**
LlamaIndex has cleaner multi-index and multi-collection retrieval abstractions. LangChain is more opinionated but has a larger ecosystem. Trade-off: LlamaIndex requires more configuration upfront but is easier to extend for the multi-KB architecture described here.

**Groq for free tier (not local Ollama):**
Groq provides cloud-hosted Llama with sub-second TTFT — critical for a good UX. Local Ollama requires client-side or self-hosted GPU infrastructure. For MVP: Groq. Post-MVP: evaluate local hosting cost vs. API cost at scale.

**FastAPI over Django/Node:**
FastAPI's async model is ideal for streaming LLM responses. Django is synchronous by default (ASGI mode exists but is less ergonomic for streaming). Node/Express is viable but Python has better ML library support for the embedding/chemistry validation layer.

**Conventional Commits + semantic-release:**
Automated changelog and versioning from commit messages aligns perfectly with the multi-agent developer workflow — the Developer bot can produce structured commits; semantic-release handles the rest without human intervention.

---

## Assumptions

1. IBA official cocktail data is used under fair use for non-commercial MVP; legal review required before commercial launch.
2. Groq API will remain in free/affordable tier during MVP development.
3. Telegram is accessible to all team members and target testers.
4. Users will have modern browsers (no IE11 support needed).
5. The chemistry knowledge base will be bootstrapped manually by a domain expert (bartender or food scientist) — no automated ingestion source exists.
6. "Paid tier" pricing is TBD (not in scope for this design document).
