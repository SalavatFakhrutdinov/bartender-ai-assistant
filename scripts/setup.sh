#!/usr/bin/env bash
set -euo pipefail

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   Bartender AI Assistant — Development Environment Setup    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
echo "Checking prerequisites..."
command -v python3 >/dev/null 2>&1 || { echo "python3 is required but not installed."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "docker is required but not installed."; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "docker compose is required but not installed."; exit 1; }

# Check if just is installed, otherwise suggest installation
if ! command -v just >/dev/null 2>&1; then
    echo "⚠️  'just' is not installed. Install it with:"
    echo "   macOS: brew install just"
    echo "   Linux: cargo install just"
    echo ""
fi

# Create .env from template if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and fill in your API keys and secrets!"
    echo ""
fi

# Install Poetry if not present
if ! command -v poetry >/dev/null 2>&1; then
    echo "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
fi

# Install shared package
echo "Installing shared Python package..."
cd packages/shared-py
poetry install
cd ../..

# Install API service dependencies
echo "Installing API service dependencies..."
cd apps/api
poetry install
cd ../..

# Install Node.js dependencies for web
echo "Installing frontend dependencies..."
cd apps/web
if command -v pnpm >/dev/null 2>&1; then
    pnpm install
elif command -v npm >/dev/null 2>&1; then
    npm install
else
    echo "⚠️  Neither pnpm nor npm found. Skipping frontend install."
fi
cd ../..

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys (Clerk, Telegram, LLM providers)"
echo "  2. Run: just dev-up      (start infrastructure)"
echo "  3. Run: just migrate     (create database tables)"
echo "  4. Run: just seed        (populate reference data)"
echo "  5. Run: just test        (run test suite)"
echo ""
