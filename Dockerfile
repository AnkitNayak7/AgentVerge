FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install uv
RUN uv sync --no-dev

EXPOSE 8000

CMD ["uv", "run", "python", "main.py"]
