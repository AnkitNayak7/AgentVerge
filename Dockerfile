FROM python:3.13-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

# Copy application code
COPY . .

# Install dependencies
RUN pip install --upgrade pip \
    && pip install uv \
    && uv sync --no-dev

# Start FastAPI app and let Cloud Run inject PORT
CMD ["uv", "run", "python", "main.py"]
