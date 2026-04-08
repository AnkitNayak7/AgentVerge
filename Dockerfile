FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies from pyproject (app code is not an installable package layout)
COPY pyproject.toml README.md ./

RUN pip install --upgrade pip \
    && pip install \
    "fastapi>=0.110.0" \
    "google-adk>=1.26.0" \
    "python-dotenv>=1.0.0" \
    "uvicorn[standard]>=0.30.0"

COPY . .

EXPOSE 8080

# Cloud Run sets PORT; default 8080 for local `docker run`
CMD ["sh", "-c", "exec python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
