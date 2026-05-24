FROM bartender-ai-assistant-agent-base:latest as base

WORKDIR /app

COPY agents/analyst/src /app/agents/analyst/src
COPY agents/analyst/pyproject.toml /app/agents/analyst/

WORKDIR /app/agents/analyst
RUN poetry install --no-interaction --no-ansi

CMD ["poetry", "run", "python", "src/main.py"]
