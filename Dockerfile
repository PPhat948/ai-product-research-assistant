FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY requirements.txt .

# Install dependencies using uv
RUN uv pip install --system --no-cache -r requirements.txt

COPY . .

# Copy vector DB (if it exists locally)
COPY chroma_db ./chroma_db

# Env var to skip ingestion in Cloud Run
ENV SKIP_INGESTION=true

# Expose port (Cloud Run sets PORT env var)
EXPOSE 8080

# Run commands using shell to expand PORT variable
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
