FROM python:3.12-slim as builder

WORKDIR /app

# Install poetry
RUN pip install poetry==1.8.3

# Copy shared package first (dependency)
COPY packages/shared-py /app/packages/shared-py
RUN cd /app/packages/shared-py && poetry build -f wheel

# Copy API service
COPY apps/api/pyproject.toml apps/api/poetry.lock* /app/apps/api/
WORKDIR /app/apps/api

# Install dependencies without dev packages
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code
COPY apps/api/src /app/apps/api/src
COPY apps/api/alembic /app/apps/api/alembic
COPY apps/api/alembic.ini /app/apps/api/alembic.ini

WORKDIR /app/apps/api

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
