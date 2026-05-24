FROM python:3.12-slim

WORKDIR /app

# Install poetry
RUN pip install poetry==1.8.3

# Copy shared package
COPY packages/shared-py /app/packages/shared-py
RUN cd /app/packages/shared-py && poetry build -f wheel

# Copy base agent package
COPY agents/_base/pyproject.toml agents/_base/poetry.lock* /app/agents/_base/
WORKDIR /app/agents/_base
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy base agent source
COPY agents/_base/base_agent /app/agents/_base/base_agent

# This is a base image — child Dockerfiles will copy their own src/ and set CMD
