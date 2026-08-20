# Recon AI

Recon AI is a tiny chat-first reconciliation assistant for matching bank statement transactions against general ledger transactions.

The MVP uses FastAPI, Next.js, OpenAI, Supabase Cloud, Redis, RQ, uv, Python 3.14, SQLAlchemy, and Alembic.

## Current Status

Phase 12 is complete. Reconciliation job upload API, Supabase Storage upload, DB job creation, RQ enqueue wiring, worker PDF text extraction, OpenAI structured transaction extraction, and transaction storage are in place. See `docs/architecture.md` and `docs/todo.md` for the implementation plan.

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

Verify shared SQLAlchemy metadata:

```bash
uv run python -c "from recon_ai_core.database import Base; import recon_ai_core.models; print(sorted(Base.metadata.tables.keys()))"
```

## Database Migrations

Alembic lives in `apps/api` and loads models from `packages/core`.

Create a migration from SQLAlchemy models:

```bash
uv run alembic -c apps/api/alembic.ini revision --autogenerate -m "migration name"
```

Apply migrations to Supabase Cloud Postgres:

```bash
uv run alembic -c apps/api/alembic.ini upgrade head
```

Check current migration version:

```bash
uv run alembic -c apps/api/alembic.ini current
```

Verify MVP tables exist and have RLS enabled:

```bash
uv run python -c "from sqlalchemy import create_engine, text; from recon_ai_core.settings import get_settings; engine=create_engine(get_settings().database_url); print(engine.connect().execute(text(\"select c.relname, c.relrowsecurity from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relname in ('reconciliation_jobs','transactions','matches','chat_sessions','chat_messages','agent_actions') order by c.relname\")).all())"
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

Verify Supabase Storage upload/download helpers:

```bash
uv run verify-storage
```

Storage paths use this format:

```text
reconciliations/{job_id}/{bank|ledger}.pdf
```

PDF file type validation is intentionally skipped for the MVP. The app assumes uploaded files are PDFs.

Start Redis:

```bash
docker compose up redis
```

Run the API skeleton:

```bash
uv run uvicorn recon_ai_api.main:app --reload
```

Health checks:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/db
```

Expected output:

```json
{"status":"ok"}
```

Create a reconciliation job:

```bash
curl -X POST http://localhost:8000/reconciliations \
  -F "bank_pdf=@samples/sample_bank_statement.pdf" \
  -F "ledger_pdf=@samples/ledger.pdf"
```

Get reconciliation job details and summary:

```bash
curl http://localhost:8000/reconciliations/{job_id}
```

The upload endpoint assumes both files are PDFs for the MVP. Redis must be reachable at `REDIS_URL` so the API can enqueue the worker job.

Verify worker imports:

```bash
uv run python -c "import recon_ai_worker.jobs, recon_ai_worker.main; print('worker imports ok')"
```

Run the RQ worker:

```bash
uv run recon-worker
```

Run one burst worker for manual verification:

```bash
uv run rq worker reconciliation --burst --url redis://localhost:6379/0
```

Enqueue a sample reconciliation job from another terminal:

```bash
uv run enqueue-sample-job
```

The frontend is not initialized yet. Next.js setup happens in a later phase.
