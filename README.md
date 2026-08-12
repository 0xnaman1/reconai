# Recon AI

Recon AI is a tiny chat-first reconciliation assistant for matching bank statement transactions against general ledger transactions.

The MVP uses FastAPI, Next.js, OpenAI, Supabase Cloud, Redis, RQ, uv, Python 3.14, SQLAlchemy, and Alembic.

## Current Status

Project scaffold is in progress. See `docs/architecture.md` and `docs/todo.md` for the implementation plan.

## Local Development

Copy environment variables:

```bash
cp .env.example .env
```

Create a uv-managed Python 3.14 virtual environment:

```bash
uv venv --python 3.14
```

Start Redis:

```bash
docker compose up redis
```

More setup commands will be added as the API, worker, and frontend are implemented.
