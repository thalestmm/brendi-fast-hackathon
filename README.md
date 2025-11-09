# 🧠 Gestão Web + Agent · Hackathon Brendi

Mini hackathon para engenheiros de software seniores com foco em construir a melhor experiência de análise de gestão para donos de restaurantes Brendi. O objetivo é entregar um dashboard funcional integrado a um agente LLM capaz de gerar insights acionáveis a partir de dados brutos.

---

## Table of Contents

- [Overview](#overview)
- [Architecture at a Glance](#architecture-at-a-glance)
- [Core Features](#core-features)
- [Data & Tenant Model](#data--tenant-model)
- [AI Agent & Messaging Flow](#ai-agent--messaging-flow)
- [Design Patterns & Key Decisions](#design-patterns--key-decisions)
- [Local Development](#local-development)
  - [Prerequisites](#prerequisites)
  - [Environment Setup](#environment-setup)
  - [Backend API (FastAPI)](#backend-api-fastapi)
  - [Background Worker & Message Buffer](#background-worker--message-buffer)
  - [Frontend (React + Vite)](#frontend-react--vite)
  - [Running Everything with Docker](#running-everything-with-docker)
  - [Sample Data & RAG Ingestion](#sample-data--rag-ingestion)
- [Quality & Tooling](#quality--tooling)
- [Deployment Notes](#deployment-notes)
- [Troubleshooting](#troubleshooting)

---

## Overview

This project delivers a restaurant-analytics cockpit with an embedded AI agent. Restaurant managers get a consolidated view of metrics (orders, revenue, campaigns, feedback) and can talk to an AI copilot that understands their business context. The solution emphasises **simplicity, clarity, and maintainability** while offering a solid foundation for production-grade features.

Key goals:
- Present actionable KPIs and charts that reflect restaurant performance.
- Use Retrieval-Augmented Generation (RAG) to answer questions with tenant-specific context.
- Support real-time conversation with low latency thanks to WebSockets and a buffering worker.
- Stay multi-tenant from day one by scoping data and requests by store.

---

## Architecture at a Glance

- **Backend:** FastAPI application (`backend/app`) serving REST endpoints, WebSockets, LangGraph agents, and background workers.
- **Frontend:** React (Vite) dashboard (`frontend/src`) with a persistent AI chat panel and analytics pages powered by ShadCN-inspired components and Recharts.
- **Data Stores:** PostgreSQL (transactions & analytics), Redis (caching, buffering, queues), ChromaDB (vector store for RAG).
- **Async Processing:** Redis Queue worker aggregates chat messages, generates insights, and coordinates AI calls.
- **Infra:** Dockerfiles for backend and frontend, `docker-compose.yml` for local orchestration, health checks, and Nginx serving the compiled frontend.

```
brendi-fast-hackathon/
├── backend/            # FastAPI app, LangGraph agent, workers, data ingestion
├── frontend/           # React dashboard and chat client
├── data/               # Sample Bambinella JSON datasets for local use
├── docker-compose.yml  # Local orchestration (Redis, backend, worker, Chroma, frontend)
└── env.example         # Reference configuration for environment variables
```

---

## Core Features

- **Analytics Dashboards:** Orders, Campaigns, and Customer views with charts (daily orders, order value distribution, top menu items, etc.).
- **AI Insights Cards:** Lightweight summaries that highlight trends and anomalies per dashboard.
- **Real-Time Chat:** WebSocket-based conversation between the manager and the AI assistant, including live typing indicators and buffered message handling.
- **Message Buffering:** Consecutive chat messages are queued inside Redis and processed together to reduce perceived latency and improve answer quality.
- **RAG-Powered Responses:** The agent blends LLM reasoning with store-specific documents stored in ChromaDB for grounded answers.
- **Multi-Tenant Compliance:** Every request carries `X-Store-ID`; routers, services, and repositories respect tenant scope.
- **Automatic Data Ingestion:** Development mode can auto-load JSON data into PostgreSQL and Chroma on startup.

---

## Data & Tenant Model

- All sample data lives under `data/` and is namespaced by `store_id`.
- `backend/app/models/` defines SQLAlchemy models for orders, campaigns, menu events, feedback, consumers, and stores.
- `backend/app/services/data_loader.py` converts JSON payloads into relational records.
- When running locally, set `STORE_ID` in `.env` (defaults to `0WcZ1MWEaFc1VftEBdLa`). Every analytics request, cache entry, and RAG lookup filters by this identifier.

---

## AI Agent & Messaging Flow

1. **Frontend WebSocket:** `frontend/src/components/Chat/ChatPanel.tsx` opens a WebSocket to `/ws/chat` and shows a typing indicator while the backend buffers messages.
2. **Redis Buffer:** `app/core/buffer.py` stores rapid user messages, resets the processing deadline, and exposes `get_pending_buffers()` for the worker. This keeps UX snappy and reduces token usage spikes.
3. **RQ Worker:** `app/workers/worker.py` scans for expired buffers, combines messages, and sends a single payload into the LangGraph agent.
4. **LangGraph Pipeline:** Defined in `app/graphs/agent.py` with supporting nodes and tools (`analytics`, `rag`, `calculator`). The agent decides whether to look up analytics, call the RAG retriever, or synthesize answers directly.
5. **Response Streaming:** The agent response is streamed back through WebSockets, updating the chat interface in real time.

---

## Design Patterns & Key Decisions

- **Dependency Injection (FastAPI):** Routers request services via `Depends` (see `app/core/dependencies.py`), keeping handlers thin and testable.
- **Service Layer:** Complex business logic lives in `app/services/`, e.g. `AnalyticsService` wraps data aggregation and caching behind simple method calls.
- **Repository-Like Separation:** SQLAlchemy queries stay inside service modules, isolating persistence from API and agent code.
- **Strategy Pattern for Insights:** `app/graphs/insights.py` chooses the best insight generator per data source, allowing easy extension for new insight types.
- **Event-Driven Buffering:** Redis + RQ implement an observer-style workflow where workers react to buffered chat events without blocking HTTP/WebSocket threads.
- **Config as Singleton:** `app/core/config.py` centralises environment configuration using `pydantic-settings`, ensuring consistent access throughout the app.
- **Simplicity First:** No heavy state management on the frontend, minimal indirection, and consciously avoided premature abstractions.

---

## Local Development

### Prerequisites

- Python 3.13+ (the Docker image uses 3.13; `uv` handles env management).
- Node.js 20+ and npm (for Vite + React).
- PostgreSQL 15+ with a database named `brendi_db` (or update `DATABASE_URL`).
- Redis 7+ (local server or Docker).
- ChromaDB (optional locally; required for full RAG experience).
- `uv` package manager (`pip install uv`) and `docker`/`docker compose` for container workflows.

### Environment Setup

1. Copy the example env file and adjust values:
   ```bash
   cp env.example .env
   ```
2. At minimum configure:
   - `OPENAI_API_KEY`
   - `DATABASE_URL` (e.g. `postgresql+asyncpg://postgres:postgres@localhost:5432/brendi_db`)
   - `REDIS_HOST`, `REDIS_PORT`
   - `STORE_ID` (use the provided default to match sample data)
   - Optional: `LANGSMITH_*` for tracing.
3. Export variables for local shells (`direnv` or `source .env`). Docker Compose automatically loads them.

### Backend API (FastAPI)

```bash
cd backend
uv sync                              # creates .venv with all deps from pyproject + uv.lock
uv run alembic upgrade head          # apply database migrations
uv run python -m app.cli.ingest_data \
  --data-dir ../data \
  --store-id "${STORE_ID:-0WcZ1MWEaFc1VftEBdLa}" \
  --skip-embeddings                  # optional; skip if Chroma not running yet
uv run uvicorn app.main:app --reload --port 8000
```

The API exposes:
- REST endpoints under `/api/v1` (`analytics`, `chat`, `data`).
- WebSocket endpoint at `/ws/chat`.
- Interactive docs at `http://localhost:8000/docs` in non-production environments.
- Health check at `http://localhost:8000/health`.

### Background Worker & Message Buffer

1. Ensure Redis is running (`brew services start redis`, `docker run redis:7-alpine`, or `docker compose up redis`).
2. Start the worker in a separate terminal:
   ```bash
   cd backend
   uv run python -m app.workers.worker
   ```
   The worker polls Redis for buffered messages, processes expired batches, and pushes responses back into the chat pipeline.

### Frontend (React + Vite)

```bash
cd frontend
npm install
```

Create `frontend/.env.local` (or `.env`) to point to your API:
```
VITE_API_BASE_URL=http://localhost:8000
VITE_DEFAULT_STORE_ID=0WcZ1MWEaFc1VftEBdLa
```

Then start the dev server:
```bash
npm run dev
```

The dashboard lives at `http://localhost:5173` by default and proxies API requests to the configured backend.

### Running Everything with Docker

The repository ships with a compose file that wires Redis, backend, worker, ChromaDB, and the Nginx-hosted frontend:

```bash
docker compose up --build
```

Prerequisites:
- Provide `DATABASE_URL` (external Postgres) in your `.env`.
- Set `OPENAI_API_KEY` (or leave blank if using mock/testing mode).
- Ensure the database is reachable from the containers (e.g. run Postgres in Docker or expose via host networking).

Services:
- `backend` → FastAPI served by Gunicorn.
- `worker` → message buffer + LangGraph worker.
- `frontend` → Nginx serving the built React assets on port `3030`.
- `redis` and `chroma` → infrastructure services with health checks.

### Sample Data & RAG Ingestion

- JSON datasets are under both `/data` (project root) and `backend/data` (mounted read-only inside containers).
- `app/services/data_loader.py` ingests orders, feedback, campaigns, menu events, consumers, and store metadata.
- To re-run RAG ingestion manually:
  ```bash
  cd backend
  uv run python -m app.cli.ingest_data \
    --data-dir ../data \
    --store-id "${STORE_ID}"
  ```
- Automatic ingestion happens on backend startup when `AUTO_INGEST_DATA=true`.

---

## Quality & Tooling

- **Linting:** Python uses Ruff-style checks (run `uv run ruff check .` if Ruff is installed). Frontend relies on ESLint (`npm run lint`).
- **Type Checking:** FastAPI leverages Pydantic for runtime validation; TypeScript provides compile-time safety on the frontend.
- **Testing:** Back-end tests can be added under `backend/tests/` and executed with `uv run pytest`. Front-end tests can use Vitest/Jest (not yet scaffolded).
- **Logging:** Configured via `app/core/logging_config.py`, with rotating file handlers by default (`/app/logs` inside containers).
- **Observability:** Optional LangSmith tracing for agent runs (enable via env vars).

---

## Deployment Notes

- Use the provided Dockerfiles for production builds. The backend expects `gunicorn` with uvicorn workers; the frontend builds static assets and ships them behind Nginx (`frontend/nginx.conf`).
- Set `ENVIRONMENT=production` to disable Swagger UI and verbose logging.
- Configure CORS, Redis, Postgres, and Chroma endpoints via environment variables for each tenant/stack.
- Make sure to provision Redis persistence (`redis_data` volume) and Chroma storage (`chroma_data`).
- Health endpoints (`/health`) and container health checks allow orchestration platforms to monitor service readiness.

---

## Troubleshooting

- **Missing Data:** Ensure PostgreSQL is running and migrations + ingestion completed. Check logs for errors during startup.
- **Chat Queue Delays:** Confirm Redis is reachable and the worker process is active. Inspect buffer keys with `redis-cli keys "message_buffer:*"`.
- **RAG Responses Stale:** Re-run the ingestion CLI after updating JSON data or resetting Chroma collections.
- **CORS / API Errors:** Verify `VITE_API_BASE_URL` and `X-Store-ID` headers. API logs (backend) will surface validation issues.
- **OpenAI Failures:** Ensure `OPENAI_API_KEY` is configured and the network allows outbound traffic. Fallbacks return graceful error messages to the UI.

---

Happy hacking! 🧑‍🍳🚀
