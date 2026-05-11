FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifests
COPY requirements.txt requirements-dev.txt ./

# Copy application code
COPY ./app ./app

# Copy main.py
COPY main.py .

# Copy migrations
COPY ./migrations ./migrations

# Copy and set permissions for entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Set PYTHONPATH to include /app so imports work correctly
ENV PYTHONPATH=/app

# Runtime target (production-like): install runtime dependencies only
FROM base AS runtime
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8000

# Use entrypoint to wait for DB and run migrations
ENTRYPOINT ["/docker-entrypoint.sh"]

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Development target: include test/dev dependencies
FROM base AS dev
RUN pip install --no-cache-dir -r requirements-dev.txt

EXPOSE 8000
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]



