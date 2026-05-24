FROM bartender-ai-assistant-agent-base:latest as base

WORKDIR /app

COPY agents/qa/src /app/agents/qa/src
COPY agents/qa/pyproject.toml /app/agents/qa/

WORKDIR /app/agents/qa
RUN poetry install --no-interaction --no-ansi

CMD ["poetry", "run", "python", "src/main.py"]
