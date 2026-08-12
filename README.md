# Recon AI

Recon AI is a tiny chat-first reconciliation assistant for matching bank statement transactions against general ledger transactions.

The MVP uses FastAPI, Next.js, OpenAI, Supabase Cloud, Redis, RQ, uv, Python 3.14, SQLAlchemy, and Alembic.

## Current Status

Phase 2 is in progress. Python workspace packages are configured for the API, worker, and shared core code. See `docs/architecture.md` and `docs/todo.md` for the implementation plan.

## Repository Layout

```text
apps/api        FastAPI backend
apps/worker     RQ worker package
apps/web        Next.js frontend, not initialized yet
packages/core   Shared Python package
docs            Architecture and execution docs
samples         Sample PDFs, not committed yet
```

## Local Development

Copy environment variables:

```bash
cp .env.example .env
```

Create a uv-managed Python 3.14 virtual environment:

```bash
uv venv --python 3.14
```

Install all Python workspace packages:

```bash
uv sync --all-packages
```

Verify Python and workspace imports:

```bash
uv run python --version
uv run python -c "import recon_ai_core, recon_ai_api, recon_ai_worker; print('ok')"
```

Start Redis:

```bash
docker compose up redis
```

Run the API skeleton:

```bash
uv run uvicorn recon_ai_api.main:app --reload
```

Run the worker placeholder:

```bash
uv run python -m recon_ai_worker.main
```

The frontend is not initialized yet. Next.js setup happens in a later phase.
