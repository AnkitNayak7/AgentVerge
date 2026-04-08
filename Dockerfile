# Use stable Python version (important for greenlet compatibility)
FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

# Install system dependencies (optional but safe)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first (for caching)
COPY pyproject.toml ./

# Install dependencies
RUN pip install --upgrade pip \
    && pip install uv \
    && uv sync --no-dev

# Copy rest of the application
COPY . .

# Start FastAPI using uvicorn (recommended for Cloud Run)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
