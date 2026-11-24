# Multi-stage Dockerfile for high-performance FastAPI backend
FROM python:3.12-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final runtime image
FROM python:3.12-slim as runner

WORKDIR /app

# Create non-root user for security (OWASP compliance)
RUN groupadd -g 1001 dtcgroup && \
    useradd -u 1001 -g dtcgroup -m dtcuser

# Copy installed dependencies
COPY --from=builder /root/.local /home/dtcuser/.local
ENV PATH=/home/dtcuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Copy backend and ML model
COPY --chown=dtcuser:dtcgroup backend/ /app/backend/
COPY --chown=dtcuser:dtcgroup ml_model/ /app/ml_model/

USER dtcuser

EXPOSE 8000

# Run with 4 Uvicorn workers for high concurrency and heavy user load
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers", "--forwarded-allow-ips", "*"]
