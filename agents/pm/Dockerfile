FROM bartender-ai-assistant-agent-base:latest as base

WORKDIR /app

COPY agents/pm/src /app/agents/pm/src
COPY agents/pm/pyproject.toml /app/agents/pm/

WORKDIR /app/agents/pm
RUN poetry install --no-interaction --no-ansi

CMD ["poetry", "run", "python", "src/main.py"]
