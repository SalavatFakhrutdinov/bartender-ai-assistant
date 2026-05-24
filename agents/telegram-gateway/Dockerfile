FROM python:3.12-slim

WORKDIR /app

RUN pip install poetry==1.8.3

COPY packages/shared-py /app/packages/shared-py
RUN cd /app/packages/shared-py && poetry build -f wheel

COPY agents/telegram-gateway/pyproject.toml agents/telegram-gateway/poetry.lock* /app/agents/telegram-gateway/
WORKDIR /app/agents/telegram-gateway
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY agents/telegram-gateway/src /app/agents/telegram-gateway/src

CMD ["python", "src/main.py"]
