FROM python:3.11-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
COPY ./app ./app
COPY main.py .
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENV PYTHONPATH=/app

# Development stage — hot reload and test dependencies (opt-in via docker-compose.dev.yml)
FROM base AS dev
RUN pip install --no-cache-dir -r requirements-dev.txt

EXPOSE 8000
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage — default when no build target is specified
FROM base AS runtime
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
