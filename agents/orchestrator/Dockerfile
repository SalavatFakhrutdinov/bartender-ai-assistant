FROM bartender-ai-assistant-agent-base:latest as base

WORKDIR /app

# Copy orchestrator source
COPY agents/orchestrator/src /app/agents/orchestrator/src
COPY agents/orchestrator/pyproject.toml /app/agents/orchestrator/

WORKDIR /app/agents/orchestrator
RUN poetry install --no-interaction --no-ansi

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
