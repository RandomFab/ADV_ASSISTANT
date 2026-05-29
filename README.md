<div align="center">

# SteelBot — AI Sales Assistant

**A conversational assistant that helps sales teams manage orders, stock, deliveries and customer claims through natural language.**

![Python](https://img.shields.io/badge/Python-3.13-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688.svg?logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-1.2-1C3C3C.svg?logo=langchain&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-FastMCP-FF6B6B.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.57-FF4B4B.svg?logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1.svg?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker&logoColor=white)

</div>

## About

SteelBot is a production-style AI assistant for an industrial sales team. It combines a **LangGraph agent** powered by **Mistral AI** with a custom **MCP (Model Context Protocol) server** exposing the company's business tools (clients, orders, stock, deliveries, claims) backed by PostgreSQL.

The stack is split into three Dockerized services behind a FastAPI gateway, with a Streamlit chat UI, structured logging, Evidently drift reports and a GitHub Actions CI pipeline (ruff + multi-stage image build).

## Features

- Conversational agent built on **LangGraph** + **Mistral AI**
- **MCP server** (FastMCP, SSE transport) exposing five business tool modules
- **FastAPI** REST gateway with health, chat and monitoring endpoints
- **Streamlit** chat interface
- **PostgreSQL 16** with seeded demo data (clients, orders, stock, deliveries, claims)
- Structured interaction logging and **Evidently** drift / quality reports
- GitHub issue alerting on monitoring incidents
- Full **Docker Compose** orchestration with healthchecks
- **CI/CD** pipeline: ruff lint + format + multi-target Docker image builds
- Comprehensive **pytest** suite (unit + functional)

## Quick Start

Requires **Docker** and **Docker Compose**. A Mistral API key is required for the agent to respond.

```bash
# Clone
git clone https://github.com/RandomFab/steelbot-mcp-sales-agent.git
cd steelbot

# Configure
cp .env.example .env
# then edit .env and set MISTRAL_API_KEY (and optionally GITHUB_TOKEN / GITHUB_REPO)

# Run
docker compose up --build
```

Once all services are healthy:

| Service       | URL                              |
|---------------|----------------------------------|
| Streamlit UI  | http://localhost:8501            |
| FastAPI docs  | http://localhost:8001/docs       |
| MCP server    | http://localhost:8000/sse        |
| PostgreSQL    | localhost:5432                   |

> Local (non-Docker) development is possible per service with `uv sync && uv run ...`
## Environment Variables

Defined in `.env` (template in `.env.example`):

| Variable             | Purpose                                    |
|----------------------|--------------------------------------------|
| `POSTGRES_*`         | Database name, user, password, host, port  |
| `MISTRAL_API_KEY`    | LLM access (required)                      |
| `GITHUB_TOKEN`       | PAT used to open monitoring alert issues   |
| `GITHUB_REPO`        | `owner/repo` target for alerts             |
| `API_URL`            | URL of FastAPI used by Streamlit           |
| `MCP_URL`            | URL of MCP server used by FastAPI agent    |

## Architecture

Four services orchestrated via Docker Compose on a single bridge network:

```
   Streamlit UI  --->  FastAPI gateway  --->  LangGraph agent  --->  MCP server (FastMCP/SSE)
     :8501              :8001                                              :8000
                                                                            |
                                                                            v
                                                              PostgreSQL 16 (:5432)
```

- **`backend/src/api`** — FastAPI app, routes, middleware, schemas
- **`backend/src/agent`** — LangGraph state graph + system prompts
- **`backend/src/mcp`** — FastMCP server and tool modules (`clients`, `orders`, `stock`, `delivery`, `reclamations`)
- **`backend/src/database`** — SQLAlchemy models, connection, init and seeding
- **`backend/src/monitoring`** — structured logger, GitHub alerting, Evidently reports
- **`frontend/ui/app.py`** — Streamlit chat client

## Project Structure

```
ADV_ASSISTANT/
├── backend/
│   ├── src/
│   │   ├── api/             # FastAPI app, routes, middleware
│   │   ├── agent/           # LangGraph agent + prompts
│   │   ├── mcp/             # MCP server + business tools
│   │   ├── database/        # SQLAlchemy models, seed
│   │   ├── monitoring/      # logger, alerting, Evidently
│   │   └── services/
│   ├── tests/               # unit + functional pytest suite
│   ├── Dockerfile           # multi-target: mcp | fastapi
│   └── pyproject.toml
├── frontend/
│   ├── ui/app.py            # Streamlit chat UI
│   ├── Dockerfile
│   └── pyproject.toml
├── .github/workflows/
│   └── cicd.yaml            # lint + build pipeline
├── docker-compose.yaml
└── .env.example
```

## Database Seeding

The database schema is created automatically on first start, but demo data must be seeded manually.

**With Docker (recommended):**
```bash
# After docker compose up, run once:
docker exec steelbot_backend uv run python -m src.database.init_db
docker exec steelbot_backend uv run python -m src.database.seed
```

**Without Docker:**
```bash
cd backend
uv run python -m src.database.init_db   # create tables
uv run python -m src.database.seed      # insert demo data (40 clients, orders, stock, claims)
```

> The seed uses a fixed random seed (`42`) — results are identical on every run.

## Testing

The backend ships with a full pytest suite covering unit tests for each MCP tool module, monitoring and schemas, plus functional tests for API endpoints, the agent graph, database models and middleware.

```bash
cd backend
uv run pytest                                     # all tests
uv run pytest tests/unit/                         # unit only
uv run pytest tests/unit/mcp/                     # MCP tools only
uv run pytest tests/functional/                   # functional only
uv run pytest tests/functional/test_api_*.py      # API only
uv run pytest --cov=src --cov-report=html         # HTML coverage report
```

**Common flags:**
```bash
uv run pytest -v          # verbose output
uv run pytest -x          # stop at first failure
uv run pytest -s          # show print() output
uv run pytest --lf        # re-run last failed tests
```

**Available fixtures** (defined in `tests/conftest.py`):

| Fixture | Description |
|---|---|
| `db_session` | In-memory SQLAlchemy session |
| `db_with_seed` | Pre-seeded in-memory database |
| `api_client` | FastAPI TestClient |
| `mock_agent` | Mocked LangGraph agent |
| `mock_github_requests` | Mocked GitHub API |
| `tmp_interactions_log` | Temporary log file |

**With Docker:**
```bash
docker exec steelbot_backend uv run pytest
docker exec steelbot_backend uv run pytest --cov=src
```

## CI/CD

GitHub Actions workflow [`.github/workflows/cicd.yaml`](.github/workflows/cicd.yaml) runs on every push to `main` / `develop` and on PRs targeting `main`:

1. **Lint** — `ruff check` and `ruff format --check` on both `backend/` and `frontend/`
2. **Build** — multi-target Docker image build (`mcp-server`, `fastapi`, `streamlit`) with GitHub Actions cache, validation only (no push)

## Tech Stack

| Layer       | Tools                                                    |
|-------------|----------------------------------------------------------|
| LLM / Agent | Mistral AI, LangGraph, langchain-mcp-adapters            |
| Tools layer | FastMCP (SSE transport)                                  |
| API         | FastAPI, Uvicorn, Pydantic                               |
| Frontend    | Streamlit                                                |
| Data        | PostgreSQL 16, SQLAlchemy 2, Faker (seed)                |
| Monitoring  | Structured JSON logs, Evidently, GitHub Issues alerting  |
| Tooling     | uv, ruff, pytest, pytest-asyncio, Docker Compose         |

## Author

**RandomFab** — Fabien BARDOUIL
