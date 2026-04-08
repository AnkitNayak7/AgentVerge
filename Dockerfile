FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition
COPY pyproject.toml ./

# Install Python deps
RUN pip install --upgrade pip \
    && pip install uv \
    && uv sync --no-dev

# Copy application code
COPY . .

# Startup script
RUN chmod +x start.sh

EXPOSE 8080

CMD ["./start.sh"]
