# Recon AI

Recon AI is a tiny chat-first reconciliation assistant for matching bank statement transactions against general ledger transactions.

The MVP uses FastAPI, Next.js, OpenAI, Supabase Cloud, Redis, RQ, uv, Python 3.14, SQLAlchemy, and Alembic.

## Current Status

Phase 3 is complete. Python workspace packages are configured, and Supabase Cloud DB plus Storage verification passes. See `docs/architecture.md` and `docs/todo.md` for the implementation plan.

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

Fill `.env` with Supabase Cloud and OpenAI values before running verification or app services.

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

## Supabase Cloud Setup

Recon AI uses Supabase Cloud for Postgres and Storage.

1. Create a Supabase Cloud project.
2. Open the project dashboard.
3. Copy the project URL into `SUPABASE_URL`.
4. Copy the secret key into `SUPABASE_SECRET_KEY`.
5. Copy the Postgres connection string into `DATABASE_URL`.
6. Create a private Storage bucket named `reconciliation-documents`.

Use a direct Postgres connection string for Alembic migrations when your network supports it. Supabase direct connections use IPv6 unless the project has the IPv4 add-on. If your network cannot reach IPv6, use the Supavisor session pooler connection string on port `5432` for local backend development and migration work. Avoid transaction pooler port `6543` for Alembic migrations.

Do not expose `SUPABASE_SECRET_KEY` in frontend code. Never add it to a `NEXT_PUBLIC_` variable. Supabase legacy `service_role` keys are not required for this project.

Verify Supabase DB and Storage access:

```bash
uv sync --all-packages
uv run verify-supabase
```

Expected output:

```text
database: ok
storage: ok
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
