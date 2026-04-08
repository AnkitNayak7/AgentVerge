# Use stable Python version
FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition first (better caching)
COPY pyproject.toml ./

# Install Python tooling and dependencies
RUN pip install --upgrade pip \
    && pip install uv \
    && uv sync --no-dev

# Copy application source
COPY . .

# Cloud Run listens on 8080
EXPOSE 8080

# ✅ FIX: Run uvicorn via Python module (Cloud Run safe)
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
