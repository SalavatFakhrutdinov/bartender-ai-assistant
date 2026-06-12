FROM python:3.12-slim AS builder

WORKDIR /app

# Install poetry
RUN pip install poetry==1.8.3

# Copy shared package first (dependency)
COPY packages/shared-py /app/packages/shared-py
RUN cd /app/packages/shared-py && poetry build -f wheel

# Copy FULL API service (including src/) before poetry install
COPY apps/api /app/apps/api
WORKDIR /app/apps/api

# Install dependencies + package
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

# Copy shared package source so editable install resolves
COPY packages/shared-py /app/packages/shared-py

WORKDIR /app/apps/api

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
