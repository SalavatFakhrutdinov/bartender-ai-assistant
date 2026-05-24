FROM bartender-ai-assistant-agent-base:latest as base

WORKDIR /app

COPY agents/developer/src /app/agents/developer/src
COPY agents/developer/pyproject.toml /app/agents/developer/

WORKDIR /app/agents/developer
RUN poetry install --no-interaction --no-ansi

CMD ["poetry", "run", "python", "src/main.py"]
