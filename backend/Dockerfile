from python:3.13-slim

RUN apt-get update && apt-get install -y \
    gcc \
    curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir uv

ENV PATH="/root/.local/bin:${PATH}"

COPY backend/pyproject.toml backend/uv.lock backend/requirements.txt ./
RUN uv sync

COPY backend/ ./

RUN mkdir -p /app/logs && chmod -R 755 /app

CMD ["uv", "run", "gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]