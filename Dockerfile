FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install uv
RUN uv sync --no-dev

EXPOSE 8080

CMD ["uv", "run", "python", "main.py"]
