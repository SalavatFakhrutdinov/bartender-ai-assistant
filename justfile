# Bartender AI Assistant — Task Runner
# Requires: just (https://github.com/casey/just)
# Install: brew install just  (macOS)  or  cargo install just

set dotenv-load := true
set fallback := true

# Default recipe: show available commands
default:
    @just --list

# =============================================================================
# Development Environment
# =============================================================================

# Start all infrastructure and services
dev-up:
    docker compose -f docker-compose.yml -f docker-compose.override.yml up -d

# Stop all services
dev-down:
    docker compose -f docker-compose.yml -f docker-compose.override.yml down

# Stop and remove volumes (destructive)
dev-clean:
    docker compose -f docker-compose.yml -f docker-compose.override.yml down -v --remove-orphans

# View logs for all services
logs:
    docker compose logs -f

# View logs for a specific service (e.g., just logs-api)
logs-api:
    docker compose logs -f api

logs-orchestrator:
    docker compose logs -f orchestrator

logs-nats:
    docker compose logs -f nats

# =============================================================================
# Build
# =============================================================================

# Build all Docker images
build:
    docker compose build

# Build a specific service (e.g., just build-service SERVICE=api)
build-service SERVICE:
    docker compose build {{SERVICE}}

# =============================================================================
# Database
# =============================================================================

# Run Alembic migrations
migrate:
    cd apps/api && poetry run alembic upgrade head

# Create a new Alembic migration (e.g., just migrate-create "add users table")
migrate-create MSG:
    cd apps/api && poetry run alembic revision --autogenerate -m "{{MSG}}"

# Seed database with reference data
seed:
    poetry run python scripts/seed_models.py
    poetry run python scripts/seed_quests.py

# Reset database (drop all tables and re-migrate)
db-reset:
    cd apps/api && poetry run alembic downgrade base
    just migrate
    just seed

# =============================================================================
# Testing
# =============================================================================

# Run all tests
test:
    just test-python
    just test-node

# Run Python tests with coverage
test-python:
    cd packages/shared-py && poetry run pytest -v --cov=shared --cov-report=term-missing
    cd apps/api && poetry run pytest -v --cov=src --cov-report=term-missing
    cd agents/orchestrator && poetry run pytest -v --cov=src --cov-report=term-missing

# Run Node.js tests
test-node:
    cd apps/web && pnpm test

# =============================================================================
# Linting & Formatting
# =============================================================================

# Run all linters and formatters
lint:
    just lint-python
    just lint-node

# Python linting and formatting (ruff + mypy)
lint-python:
    cd packages/shared-py && poetry run ruff check . && poetry run ruff format . && poetry run mypy .
    cd apps/api && poetry run ruff check . && poetry run ruff format . && poetry run mypy .
    cd agents/orchestrator && poetry run ruff check . && poetry run ruff format . && poetry run mypy .

# Node.js linting and formatting
lint-node:
    cd apps/web && pnpm lint && pnpm format

# =============================================================================
# Agent Swarm
# =============================================================================

# Start the agent swarm (orchestrator + all agents)
swarm-up:
    docker compose up -d orchestrator telegram-gateway analyst developer qa pm

# Restart a specific agent (e.g., just agent-restart analyst)
agent-restart AGENT:
    docker compose restart {{AGENT}}

# View orchestrator admin dashboard
orchestrator-status:
    @curl -s http://localhost:8001/agents | python -m json.tool

# =============================================================================
# One-time Setup
# =============================================================================

# Initial project setup (install dependencies, create .env, etc.)
setup:
    @echo "Setting up Bartender AI Assistant development environment..."
    cp -n .env.example .env || true
    @echo "Installing Python dependencies..."
    cd packages/shared-py && poetry install
    cd apps/api && poetry install
    cd agents/orchestrator && poetry install
    @echo "Installing Node.js dependencies..."
    cd apps/web && pnpm install
    @echo "Setup complete. Run 'just dev-up' to start services."
