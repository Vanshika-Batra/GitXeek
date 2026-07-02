# GitXeek API

Production FastAPI backend with async PostgreSQL, Alembic migrations, and Docker deployment.

## Structure

```
app/
├── main.py              # Application entry & lifespan
├── core/config.py       # Environment-based settings
├── db/session.py        # Async SQLAlchemy engine & session
├── api/
│   ├── deps.py          # Shared FastAPI dependencies
│   └── v1/
│       ├── router.py    # Versioned API router
│       └── endpoints/   # Route handlers
alembic/                 # Database migrations
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Start PostgreSQL, then run migrations and the server:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

Health check: `GET /api/v1/health`

## Production

```bash
docker build -t gitxeek-api .
docker run -p 8000:8000 --env-file .env gitxeek-api
```

## Adding features

| Layer      | Location                    |
|------------|-----------------------------|
| Models     | `app/db/session.py` (Base)  |
| Schemas    | `app/schemas/`              |
| Services   | `app/services/`             |
| Endpoints  | `app/api/v1/endpoints/`     |

Register new routers in `app/api/v1/router.py`.
