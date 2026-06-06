# ═══════════════════════════════════════════
# FraudLens Backend — Production Dockerfile
# ═══════════════════════════════════════════
FROM python:3.11-slim AS base

WORKDIR /app

# System dependencies for asyncpg, numpy, scikit-learn
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install torch==2.3.0 torchvision==0.18.0 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Copy application code
COPY . .

# Set Python path so modules can import from the project root
ENV PYTHONPATH=/app

# Create non-root user for security
RUN addgroup --system --gid 1001 fraudlens \
    && adduser --system --uid 1001 --ingroup fraudlens api

USER api

EXPOSE 8000

# Production: no --reload flag
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--log-level", "info"]
