# Blueprint Diff: v2.0 vs v1.0

**Date:** 2026-05-22  
**Scope:** Comprehensive comparison of the Bartender AI Assistant system blueprint between version 2.0 (this document) and version 1.0 (Claude's original output).

---

## Summary of Changes

| Category | v1.0 Approach | v2.0 Approach | Impact |
|----------|---------------|---------------|--------|
| **Agent Architecture** | 4 isolated Telegram bots with webhook dispatcher | Swarm Orchestrator + NATS JetStream event bus + skill registry + shared memory | Enables parallelism, resilience, dynamic scaling, and collective intelligence |
| **Agent Communication** | Point-to-point webhooks + Telegram group | Durable event streams with replay, consumer groups, and exactly-once processing | Messages never lost; agents can replay history; new agents auto-subscribe |
| **Agent Capabilities** | Fixed 4-agent system | 4 core + 6 auxiliary agent types (Security, Docs, Migration, Performance, Revert, Knowledge Curator) | Self-healing, auto-documentation, emergency rollback, knowledge curation |
| **Agent Memory** | None (stateless bots) | Qdrant vector store (episodic memory) + Redis Graph/Neo4j (causal links) + MinIO (artifacts) | Agents learn from past decisions; Analyst estimates better; Developer reuses patterns |
| **RAG Architecture** | Pure vector search (Qdrant) | Hybrid search (dense + sparse BM25) + Knowledge Graph (Neo4j/KùzuDB) + Query Planner + Multi-hop retrieval | Better retrieval accuracy; graph reasoning for ingredient relationships; query rewriting for paid tier |
| **LLM Gateway** | Simple tier-based routing | Smart router with circuit breakers, cost tracking, A/B testing, prompt semantic cache, intelligent fallback chains | Higher uptime; 30% cost reduction via cache; data-driven model selection |
| **Knowledge Representation** | Flat document chunks in vector DB | Vector collections + structured Knowledge Graph with nodes (Ingredient, Cocktail, FlavorFamily) and edges (CONTAINS, PAIRS_WITH, INCOMPATIBLE_WITH) | Enables transitive reasoning ("if A pairs with B and B pairs with C, maybe A pairs with C"); powers physical validation |
| **Physical Validation** | Basic incompatibility + density check | 5-dimension validation: incompatibility, layering order, pH balance, ABV sanity, viscosity/mouthfeel | Catches more classes of impossible recipes; regeneration with specific constraints |
| **Feedback Loop** | Static taste score + prompt injection | Taste score v2 (reweighted) + MLOps fine-tuning pipeline (LoRA/QLoRA on Fireworks AI) + A/B testing + model registry (MLflow) | System actually learns and improves its base model; not just prompt engineering |
| **Taste Score Weights** | 0.35/0.25/0.20/0.10/0.10 | 0.30/0.25/0.20/0.15/0.10 | Better reflects bartender priorities (appearance and guest reaction weighted more realistically) |
| **Bar Context** | Simple vector retrieval of uploaded docs | Vector retrieval + Graph-based meta-learning + Inventory-aware constraint solver + Menu coherence scoring | Suggestions are not just relevant but operationally practical for the specific bar |
| **PDF Parsing** | PyMuPDF + Tesseract | marker (SOTA layout-aware) primary + PyMuPDF fallback; GPT-4o Vision primary + Tesseract fallback | Higher accuracy on stylized bar menus; table detection for prices and ingredients |
| **Frontend** | Next.js 14 + next-auth | Next.js 15 (Partial Prerendering) + Clerk + Zustand persist middleware + Socket.io v4 | Faster initial load; better auth UX; offline-first chat history |
| **Backend Auth** | NextAuth.js JWT | Clerk with webhook integration | Built-in MFA, org support, session management; faster to integrate |
| **Message Queue** | Celery + Redis only | NATS JetStream (primary event bus) + Celery + Redis (background jobs) | Separation of real-time events from background tasks; event replay capability |
| **Database** | PostgreSQL 16 | PostgreSQL 16 + pgvector (for ad-hoc vector ops) | Enables simpler analytics queries that join relational and vector data |
| **Data Models** | 6 tables | 8 tables (added `llm_usage`, `validation_failures`, `ml_experiments`) | Full cost observability, validation analytics, MLOps experiment tracking |
| **Cocktail Schema** | Basic JSON with safety_check | Extended JSON with per-ingredient cost, physical_validation block, generation metadata | Better cost transparency; validation audit trail; performance analytics |
| **Infrastructure** | Docker Compose → Kubernetes (vague) | Docker Compose (MVP) → Kubernetes (post-MVP) with explicit Helm chart plan; Traefik v3; Doppler for secrets | Clearer migration path; modern ingress with automatic TLS |
| **Testing** | pytest + coverage.py | pytest + coverage.py + pytest-xdist (parallel) + differential coverage + golden snapshot regression + Security Auditor agent scan | Faster test runs; regression detection; security gate on every PR |
| **UAT** | QA posts URL to Telegram | Same, but with structured `uat.feedback` events synthesized by QA agent; correlation IDs link Telegram threads to event chains | Feedback is structured and actionable; full audit trail from human comment to code change |
| **Monitoring** | Prometheus + Grafana + Loki | Same + Sentry + agent-specific metrics (task throughput, latency, error rates) | Better error tracking; agent swarm observability |
| **Safety Filtering** | Llama Guard 2 / OpenAI Moderation | Llama Guard 3 (newer) / OpenAI Moderation + Llama Guard 3 (dual-layer for paid) | Improved safety with newer model; defense in depth for paid tier |
| **Free Tier Fallback** | Ollama mentioned as possibility | Ollama integrated as circuit-breaker fallback with automatic failover | Free tier remains functional even if Groq is down |
| **Rate Limiting** | Simple Redis counter | Sliding-window counters with upgrade prompt UI + cached tier data from Redis | Better user experience; reduced DB load |
| **Embedding Strategy** | text-embedding-3-small or all-MiniLM | Same, but with sparse vector index (SPLADE/BM25) in Qdrant for hybrid search | Keyword matching for exact ingredient names; semantic matching for concepts |
| **Query Rewriting** | Not present | Lightweight LLM (Claude Haiku) rewrites low-confidence queries for better retrieval (paid tier) | Improves retrieval quality for vague or ambiguous user prompts |
| **Team/Org Support** | Not present | `team` tier in data model; Clerk org support; planned for post-MVP | Future-proofing for bar chains and multi-user accounts |
| **Trial Mode** | Not present | 7-day free trial for paid sign-ups | Reduces signup friction; increases conversion |
| **Load Testing** | Not mentioned | Locust or k6 with target metrics (100 concurrent, p95 < 2s) | Ensures performance requirements are met before launch |
| **Commit Size Policy** | <200 lines warning | <200 lines enforced by pre-commit hook; >300 lines requires PM override | Prevents large, risky changes from entering the codebase |
| **Agent Self-Healing** | Not present | Health Monitor restarts crashed agents in 30s; circuit breaker pauses failing agents after 3 failures in 5m | Swarm remains operational even with individual agent failures |
| **Agent Parallelism** | Not possible | Developer can spawn `Developer-Test` sub-agent; QA can spawn `QA-Sub` agents for parallel test categories; Analyst can parallelize ticket decomposition | Faster ticket throughput; better utilization of agent capacity |
| **Revert Bot** | Not present | Emergency `Revert Bot` auto-triggers if production error spike detected | Reduces incident response time from minutes to seconds |
| **Commit Convention** | Conventional Commits + semantic-release | Same, but with automated agent changelog generation | Release notes generated without human intervention |

---

## Detailed Section-by-Section Diff

### Part 0 — Multi-Agent Development System

#### 0.1 Agent Roles (Major Expansion)
**v1.0:** 4 fixed agents (Analyst, Developer, QA, PM). Each is a standalone Telegram bot. Communication is direct bot-to-bot via Telegram mentions.

**v2.0:** 4 core agents + 6 auxiliary agents. All agents communicate via NATS JetStream event bus. Telegram is only a human-facing surface layer. Agents self-register skills with the Orchestrator.

**Rationale:** The v1.0 design conflates the communication transport (Telegram) with the coordination layer. This makes it impossible to add agents dynamically, parallelize work, or recover from agent crashes. The v2.0 swarm design decouples these concerns.

#### 0.2 Agent Communication Architecture (Complete Rewrite)
**v1.0:**
```
GitHub Webhook → Webhook Dispatcher → Telegram bots
```

**v2.0:**
```
GitHub Webhook → NATS JetStream → Orchestrator → Agent Pools
Telegram ←→ Telegram Gateway ←→ NATS JetStream
```

**Key additions:**
- **NATS JetStream** replaces webhooks as the primary backbone. Provides durable streams, consumer groups for load balancing, message replay for debugging, and exactly-once processing for critical events.
- **Telegram Gateway Service** is a FastAPI service that normalizes Telegram messages into typed NATS events and vice versa. This means agents don't need to know about Telegram at all — they consume and produce events.
- **Event schema** is explicitly defined with 7 streams: `tickets`, `code`, `qa`, `release`, `human`, `agent`, `memory`.

#### 0.3 Sequence Diagram (Expanded)
**v1.0:** Shows 6 participants with Telegram as the central message bus.

**v2.0:** Shows 10 participants including NATS Bus, Orchestrator, and Agent Pools. The diagram explicitly shows:
- Event routing through the Orchestrator
- Load-balanced assignment to agent pools
- CI/CD interaction with GitHub webhooks
- Correlation between Telegram threads and event chains

#### 0.4 Supporting Tooling (Expanded)
**v1.0:** 8 tools listed.

**v2.0:** 13 tools listed. Added:
- NATS JetStream (event bus)
- Qdrant (agent memory)
- MinIO (artifact storage)
- Prometheus + Grafana (agent metrics)
- Loki (log aggregation)

#### 0.5 Quality & Velocity (Enhanced)
**v1.0:** TDD gate, coverage gate, commit size policy, sprint cadence, Agile ceremonies.

**v2.0:** All of the above, plus:
- **Agent Memory learning:** Analyst queries past tickets before decomposition.
- **Self-healing:** Health monitor restarts crashed agents.
- **Regression prevention:** Golden snapshot tests maintained by QA agent.
- **Security gate:** Security Auditor agent scan on every PR.
- **Differential coverage:** Reports coverage delta, not just absolute percentage.

---

### Part 1 — Target Application

#### 1.1 System Architecture (Major Expansion)
**v1.0:** 6 backend services, Qdrant vector DB, Redis cache.

**v2.0:** 7 backend services, Qdrant vector DB, Neo4j/KùzuDB knowledge graph, Redis cluster, NATS JetStream, MinIO. Key additions:
- **Knowledge Graph (Neo4j/KùzuDB):** Structured graph for ingredient relationships, incompatible pairs, and bar concept similarity.
- **Feedback & MLOps Service:** Dedicated service for feedback collection, taste score calculation, and fine-tuning pipeline orchestration.
- **LLM Gateway v2:** Adds circuit breakers, cost tracking, A/B testing, and semantic prompt cache.
- **taste_feedback_embeddings collection:** Vector store for user feedback text to enable semantic similarity search.

#### 1.2 Frontend Design (Updated)
**v1.0:** Next.js 14, next-auth, Zustand, socket.io-client.

**v2.0:** Next.js 15 (Partial Prerendering), Clerk, Zustand with persist middleware, Socket.io v4. Added:
- Attachment dropzone for paid users
- Feedback panel
- `/compare` command (paid)
- `/feedback` command (all tiers)
- Fuzzy-matching slash command autocomplete

#### 1.3 Core Chat & AI Service (Enhanced)
**v1.0:** Basic request flow with RAG retrieval.

**v2.0:** Enhanced with:
- **Query Planning:** RAG Service analyzes the prompt to determine what information is needed and whether multi-hop retrieval is required.
- **Deferred Feedback Scheduling:** Celery beat schedules surveys 24h after generation.
- **Response Caching:** LLM responses cached in Redis with 1h TTL for identical queries.
- **Generation Metadata:** Tracks model used, RAG sources, and latency for analytics.

#### 1.4 LLM Gateway (Complete Rewrite)
**v1.0:** Simple if/else routing. Groq for free, Claude for paid.

**v2.0:** Full-featured gateway with:
- **Circuit Breaker:** Failing provider routed away for 5 minutes after 5 failures in 2 minutes.
- **A/B Testing:** 50/50 split between Claude Sonnet and GPT-4.1 for paid tier.
- **Cost Tracker:** Every call logged to `llm_usage` table with tokens, cost, latency.
- **Prompt Cache:** Semantic cache in Redis (cosine similarity >0.97) saves ~30% of calls.
- **Intelligent Fallback Chain:** Up to 3 fallback models per tier.
- **Complexity Scoring:** Routes complex prompts to more capable models even within the same tier.

#### 1.5 RAG Pipeline (Major Enhancement)
**v1.0:** Single-collection dense vector retrieval, basic reranking.

**v2.0:** Hybrid architecture with 6 components:
1. **Query Planning:** Determines retrieval strategy before execution.
2. **Hybrid Search:** Dense (vector similarity) + Sparse (BM25 via Qdrant sparse vectors) + Reciprocal Rank Fusion.
3. **Knowledge Graph Augmentation:** Neo4j/Cypher queries for relationship-based retrieval (e.g., "find pairings for this ingredient").
4. **Multi-hop Retrieval:** For queries referencing known cocktails (e.g., "like an Old Fashioned but with tequila"), does hop-1 (find Old Fashioned) → hop-2 (find tequila variants with similar profiles).
5. **Cross-encoder Reranking:** Top-30 → top-8.
6. **Query Rewriting (paid):** Lightweight LLM rewrites low-confidence queries for better retrieval (max 1 rewrite).

**Ingestion improvements:**
- Primary PDF parser: `marker` (state-of-the-art) instead of PyMuPDF.
- Image OCR: GPT-4o Vision primary instead of Tesseract primary.
- Graph update: Extracted menu items create graph relationships.
- Deduplication: Hash-based check before re-parsing.

#### 1.6 Subscription & Tier System (Enhanced)
**v1.0:** Free / Paid only.

**v2.0:** Free / Paid Monthly / Paid Annual / Team (post-MVP). Added:
- **Trial Mode:** 7-day free trial for paid sign-ups.
- **Team tier:** Multi-user bar accounts (future-proofing).

#### 1.7 Response Format & Safety (Enhanced)
**v1.0:** Basic JSON schema with safety_check.

**v2.0:** Extended schema with:
- Per-ingredient `estimated_cost_usd`
- `physical_validation` block with status and checked dimensions
- `metadata` block with model_used, rag_sources, generation_time_ms
- **Safety Pipeline v2:** Llama Guard 3 (upgraded from v2) + dual-layer for paid tier.
- **Schema Validation:** Pydantic v2 strict validation with auto-regeneration on failure.

---

### Part 2 — Known Challenges & Solutions

#### 2.1 Measurable Taste Metric (Major Enhancement)
**v1.0:**
- Static taste score with fixed weights
- Weekly prompt refinement (top/bottom examples)
- Free user incentive: 5 high-rated cocktails → 30 days paid

**v2.0:**
- **Taste Score v2:** Reweighted (appearance 0.15, guest reaction 0.10) based on bartender interviews.
- **MLOps Fine-Tuning Pipeline:** Monthly LoRA/QLoRA training on Fireworks AI; MLflow tracking; A/B test with 10% traffic; automatic promotion/rollback based on taste_score improvement.
- **Feedback Embeddings:** User feedback text is embedded and stored for semantic similarity search.
- **Free user incentive:** 5 feedback surveys → 14 days paid (more realistic than 5 high-rated cocktails).
- **DPO Training:** Direct Preference Optimization using high-rated vs low-rated pairs for the same prompt.

**Rationale:** v1.0's approach was prompt-engineering only. v2.0 adds actual model fine-tuning, making the system self-improving at the weights level, not just the prompt level.

#### 2.2 Physical Realizability (Major Enhancement)
**v1.0:**
- Basic incompatibility check
- Density order check for layered drinks
- Max 2 regeneration attempts

**v2.0:**
- **5-dimension validation:**
  1. Incompatibility (critical/warning severity levels)
  2. Layering order (density-based)
  3. pH balance (acceptable range 2.8–5.5)
  4. ABV sanity (warn if >40%)
  5. Viscosity/mouthfeel (flag if >2 viscous ingredients)
- **Knowledge Graph Rules:** Cypher queries detect incompatibilities transitively.
- **Validation Failures Table:** All failures logged to `validation_failures` for MLOps analysis.
- **Regeneration Protocol:** Same max 2 attempts, but with more specific error context.

**Rationale:** v1.0 caught only the most obvious physical issues. v2.0's multi-dimension validation catches subtle problems (e.g., a cocktail with 3 syrupy liqueurs that would be undrinkable, or extreme pH that would be harsh).

#### 2.3 Local Bar Context (Major Enhancement)
**v1.0:**
- Vector retrieval of uploaded menu + concept text
- Cosine similarity matching against extended cocktails
- Inventory list as text constraint

**v2.0:**
- **Graph-Based Meta-Learning:** Cypher query finds cocktails from bars with similar concepts (cosine similarity >0.75).
- **Inventory-Aware Constraint Solver:**
  - Primary: ≥70% in-stock ingredients
  - Secondary: reuse existing menu ingredients (reduce waste)
  - Tertiary: respect target price per serving
- **Menu Coherence Scoring:** Post-generation score for ingredient overlap, flavor diversity, glassware reuse, and duplication avoidance. Displayed as a badge.
- **Style Preferences:** Slider inputs for sweetness, sourness, bitterness, spirit-forwardness.
- **Target Price Range:** Per-cocktail cost target affects generation.

**Rationale:** v1.0's context injection was "dump text into prompt." v2.0's approach actively reasons about operational constraints, making suggestions not just conceptually relevant but practically executable behind a real bar.

---

### Technology Stack Changes

#### Added in v2.0
| Technology | Purpose |
|------------|---------|
| NATS JetStream | Event bus for agent swarm |
| Neo4j / KùzuDB | Knowledge graph for ingredient relationships |
| marker | SOTA PDF parsing (primary) |
| GPT-4o Vision | Image OCR for stylized menus (primary) |
| Socket.io v4 (server + client) | WebSocket streaming with room support |
| Clerk | Auth with MFA, orgs, webhooks |
| MLflow | Model registry and experiment tracking |
| Fireworks AI / Together AI | LoRA/QLoRA fine-tuning infrastructure |
| Zod | Schema validation (frontend + backend) |
| React Hook Form | Form handling |
| Tremor / Recharts | Analytics dashboards |
| Locust / k6 | Load testing |
| Sentry | Error tracking |
| Doppler | Secrets management |
| Traefik v3 | Reverse proxy with automatic TLS |

#### Removed in v2.0
| Technology | Reason |
|------------|--------|
| next-auth | Replaced by Clerk for faster integration and built-in features |
| Tesseract (as primary OCR) | Replaced by GPT-4o Vision for better accuracy on stylized menus; kept as fallback |
| PyMuPDF (as primary PDF parser) | Replaced by marker for layout-aware extraction; kept as fallback |
| LlamaIndex (as primary RAG) | Replaced by custom orchestration layer for full pipeline control; can be integrated optionally |
| LangChain | Not used in either version, but v2.0 explicitly avoids it |

#### Upgraded in v2.0
| Component | v1.0 | v2.0 |
|-----------|------|------|
| Next.js | 14 | 15 (Partial Prerendering) |
| Llama Guard | 2 | 3 |
| Llama (free tier) | 3.1 70B | 3.3 70B |
| Socket.io | not versioned | v4 |
| Tailwind CSS | v4 (implied) | v4 (explicit) |
| Qdrant | not versioned | 1.10+ (sparse vectors) |
| Redis | 7 | 7 Cluster mode |
| PostgreSQL | 16 | 16 + pgvector extension |

---

### Data Models Changes

#### Added Tables
| Table | Purpose |
|-------|---------|
| `llm_usage` | Cost tracking, token accounting, latency analytics per LLM call |
| `validation_failures` | Log of physical validation failures for MLOps analysis |
| `ml_experiments` | Fine-tuning experiment tracking, A/B test results, model promotion status |

#### Modified Tables
| Table | v1.0 | v2.0 |
|-------|------|------|
| `users` | Basic fields + tier | Added `clerk_id`, `trial_ends_at`, `preferences` JSONB |
| `subscriptions` | Basic fields | Added `stripe_customer_id`, `cancel_at_period_end`, `updated_at` |
| `chat_sessions` | Basic fields | Added `title` (generated), `first_message`, `model_used` |
| `messages` | Basic fields | Added `command_args`, `model_used`, `latency_ms`, `token_count_input`, `token_count_output` |
| `cocktails` | Basic fields + taste_score | Added `feedback_count`, `is_promoted`, `physical_validation_status`, `neo4j_node_id`, `generation_metadata`, `updated_at` |
| `cocktail_feedback` | Static weights | Taste score weights updated; added `would_repeat` enum (was boolean); added `modification_note`; added `embedding` vector |
| `user_bar_context` | Basic fields | Added `style_preferences`, `target_price_range`, `qdrant_namespace` |

---

### Implementation Roadmap Changes

#### Phase 0 (Foundation)
**v1.0:** 8 tasks. Focus on repo setup, Docker, CI, DB, auth, Telegram bots, Analyst agent.

**v2.0:** 14 tasks. Added:
- NATS JetStream configuration
- Agent Swarm Orchestrator baseline
- Telegram Gateway Service (decoupled from agents)
- Developer/QA/PM agent baselines
- Agent Memory baseline (Qdrant)
- Health Monitor

**Milestone upgraded:** From "Analyst creates a ticket" to "Full swarm loop demonstrated end-to-end."

#### Phase 1 (Core Chat MVP)
**v1.0:** 9 tasks.

**v2.0:** 11 tasks. Added:
- Ingredient chemistry seed dataset → Neo4j
- Basic safety filter: Llama Guard 3
- Chat history persistence + session management

**Milestone upgraded:** From "Free user can chat" to "Agent swarm has shipped at least 3 tickets autonomously."

#### Phase 2 (Paid Tier)
**v1.0:** 10 tasks.

**v2.0:** 13 tasks. Added:
- Neo4j knowledge graph setup
- Hybrid search (dense + BM25)
- Cross-encoder reranker
- Menu fit scoring

#### Phase 3 (Feedback & Validation)
**v1.0:** 9 tasks.

**v2.0:** 11 tasks. Added:
- MLOps pipeline (data prep → LoRA → MLflow)
- A/B test framework
- Feedback text embeddings
- Validation failures table

**Milestone upgraded:** From "System rejects impossible recipes" to "First fine-tuned model trained and evaluated."

#### Phase 4 (Polish & UAT)
**v1.0:** 9 tasks.

**v2.0:** 11 tasks. Added:
- Sentry error tracking
- Load testing with Locust/k6
- Documentation (API docs, runbooks, agent skill registry)

**Milestone upgraded:** From "UAT sign-off" to "100+ daily active users with performance validation."

#### Phase 5 (New)
**v2.0 adds a new Phase 5** covering swarm auto-scaling, cross-agent learning, automated refactoring, team tier, Kubernetes migration, CDN, and advanced analytics. This was not present in v1.0.

---

### Risks & Trade-offs Changes

#### Added Risks
| # | Risk | Mitigation |
|---|------|------------|
| 11 | Fine-tuning pipeline produces degraded model | A/B test with 10% traffic; automatic rollback; human review gate |
| 12 | Neo4j complexity exceeds MVP bandwidth | Start with KùzuDB (embedded); migrate to Neo4j only if needed |
| 13 | Socket.io scaling issues at 100+ concurrent users | Redis adapter; horizontal scaling; connection limits |

#### Modified Risks
| # | v1.0 | v2.0 |
|---|------|------|
| 4 | Groq rate limits "Medium" impact | Upgraded to "High" impact due to larger user base assumption; added cache target |
| 5 | Free user incentive: 30 days for 5 cocktails | Changed to 14 days for 5 feedback surveys (more realistic) |
| 6 | Added "Agent Memory lookup before implementation" to mitigation |
| 7 | Added "NATS clustered deployment with replication" to mitigation |
| 10 | Added "Token budget per agent task" to mitigation |

---

### Key Design Decisions (New in v2.0)

| Decision | Rationale |
|----------|-----------|
| **Qdrant + Neo4j over pgvector alone** | Vectors for semantic search; graph for relationship reasoning. Two services but significantly better retrieval and validation. |
| **NATS JetStream over Redis Pub/Sub** | Durability, replay, exactly-once, consumer groups. Purpose-built for event-driven swarms. |
| **Custom RAG over LlamaIndex/LangChain** | Full control over latency, cost, and pipeline steps. More initial work but better long-term flexibility. |
| **KùzuDB over Neo4j for MVP** | Embedded graph DB eliminates operational overhead. Migrate to Neo4j if scale demands it. |
| **Clerk over NextAuth.js** | Built-in MFA, orgs, webhooks. Faster MVP delivery despite vendor lock-in. |
| **Fine-tuning (LoRA) over prompt engineering only** | Prompt engineering has diminishing returns. LoRA adapts the model to the specific domain (cocktails) with relatively small compute cost. |

---

## What v1.0 Did Better (Acknowledged Strengths)

Despite the extensive upgrades, v1.0 had some merits worth preserving:

1. **Simplicity for MVP:** v1.0's stack was leaner (no graph DB, no NATS, no MLOps). For a team with severe resource constraints, v1.0 could reach Phase 1 faster.
2. **LlamaIndex integration:** v1.0 explicitly chose LlamaIndex, which has a gentler learning curve than a custom RAG orchestrator. For teams new to RAG, this reduces time-to-first-retrieval.
3. **Fewer moving parts:** With 6 tables vs 8, and no knowledge graph, v1.0 has less operational surface area.
4. **Direct Telegram integration:** v1.0's bots talk directly to Telegram, which is simpler to debug than a decoupled gateway + event bus.

**v2.0's position:** These trade-offs are valid for extremely constrained teams. However, the user explicitly requested focus on "exceptional features (like agent-swarm) during further development lifecycle." The v2.0 architecture is designed to grow into those capabilities, whereas v1.0 would require significant refactoring to add swarm behavior, agent memory, or MLOps.

---

## Migration Path: v1.0 → v2.0

For a team that has already started implementing v1.0, the migration path to v2.0 is phased:

1. **Phase A (Week 1):** Add NATS JetStream alongside existing webhook dispatcher. Run both in parallel. Migrate one agent at a time.
2. **Phase B (Week 2):** Implement Telegram Gateway Service. Decouple agents from Telegram API.
3. **Phase C (Week 3):** Add Agent Memory (Qdrant collection). Start logging episodic memories.
4. **Phase D (Week 4):** Add Health Monitor and auxiliary agents (Security Auditor first).
5. **Phase E (Weeks 5–6):** Add Knowledge Graph (KùzuDB) alongside Qdrant. Start populating ingredient relationships.
6. **Phase F (Weeks 7–8):** Upgrade LLM Gateway to v2 (circuit breakers, cache, cost tracking).
7. **Phase G (Weeks 9–10):** Implement MLOps pipeline and feedback embeddings.

This staged approach minimizes disruption while progressively unlocking v2.0 capabilities.

---

## Conclusion

**v2.0 is a superset of v1.0** — it preserves all core requirements while adding:
- A production-grade agent swarm architecture
- Hybrid RAG with knowledge graph reasoning
- Self-improving MLOps pipeline
- Advanced physical validation
- Operationally-aware bar context
- Comprehensive observability and resilience

The trade-off is increased initial complexity. However, for a system intended to be built and maintained by AI agents themselves, the v2.0 architecture provides the necessary infrastructure for agents to collaborate, learn, and improve autonomously — which is the defining requirement of this project.
