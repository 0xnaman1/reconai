# Recon AI

Recon AI reconciles a bank statement against a general ledger, and lets you argue with the result.

<img width="1511" height="1046" alt="Image" src="https://github.com/user-attachments/assets/b2aca086-a6b9-4acf-91a5-c2e5465c2007" />

Upload two PDFs. It reads both, matches what it can defend, and hands you the rest: the pairs it was not confident enough to assert on its own, and the transactions it could not pair at all. You work through those in the UI or by asking the assistant about them in plain English.

The matching is deterministic. The language model reads PDFs and talks to you; it never decides what matches what.

## How it works

```text
  Next.js UI  ──upload──►  FastAPI  ──enqueue──►  Redis / RQ  ──►  Worker
       │                      │                                     │
       │                      │                          pdfplumber │ text
       │                      │                            OpenAI   │ structured rows
       │                      ▼                                     ▼
       └──chat──►  Agent (OpenAI tool calling)  ◄────  Supabase Postgres
                          │                                   ▲
                          └── 8 typed tools ──────────────────┘
                                                     Supabase Storage (PDFs)
```

A job moves `queued → extracting → matching → completed`. Each stage writes its status, so a failure names the stage it failed in.

### Scoring

Every bank row is scored against every ledger row, out of 100:

| Signal | Points |
| --- | --- |
| Amount matches exactly | 40 |
| Date matches exactly | 25 |
| Date within 1 / 2 / 3 days | 20 / 18 / 15 |
| Reference matches (punctuation ignored) | 25 |
| Description similarity | 0-10 |

- **90 and above** — matched automatically.
- **70 to 89** — held for review. Usually a missing reference or dates a few days apart.
- **Below 70** — left unmatched, and offered as a ranked suggestion you can pair by hand.

Amount is the gate. Without it the ceiling is 60, so no amount mismatch is ever matched automatically. Pairs are claimed best-first, one-to-one, with a deterministic tie-break, so the same input always produces the same output.

Unmatched is derived, never stored: a transaction no active match points at. Rejecting a match returns both sides to the pool.

## Requirements

- Python 3.14 and [uv](https://docs.astral.sh/uv/)
- Node.js 20+
- Docker (for Redis only)
- A Supabase Cloud project
- An OpenAI API key

## First-time setup

### 1. Clone and install

```bash
git clone git@github.com:0xnaman1/reconai.git
cd reconai

uv venv --python 3.14
uv sync --all-packages

cd apps/web && npm install && cd ../..
```

### 2. Supabase Cloud

1. Create a project at [supabase.com](https://supabase.com).
2. From the dashboard, copy the project URL, the secret key, and the Postgres connection string.
3. Create a **private** Storage bucket named `reconciliation-documents`.

Supabase direct connections use IPv6 unless the project has the IPv4 add-on. If your network cannot reach IPv6, use the Supavisor **session pooler** string on port `5432`. Avoid the transaction pooler on port `6543` for Alembic — migrations need a stable connection.

### 3. OpenAI

Create a key at [platform.openai.com](https://platform.openai.com/api-keys). Both extraction and chat default to `gpt-4.1` and are configurable.

### 4. Environment

```bash
cp .env.example .env
```

Fill in:

```dotenv
DATABASE_URL=postgresql+psycopg://postgres:...@...supabase.com:5432/postgres
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_SECRET_KEY=<secret key>
SUPABASE_STORAGE_BUCKET=reconciliation-documents
OPENAI_API_KEY=sk-...
REDIS_URL=redis://localhost:6379/0
```

Never put `SUPABASE_SECRET_KEY` behind a `NEXT_PUBLIC_` variable. The frontend only needs the API URL, which `apps/web/.env.local` already sets to `http://localhost:8000`.

### 5. Migrate

```bash
uv run alembic -c apps/api/alembic.ini upgrade head
```

### 6. Verify

```bash
uv run verify-supabase   # database: ok / storage: ok
uv run verify-storage
```

## Running it

Four terminals:

```bash
docker compose up redis                              # 1. queue
uv run recon-worker                                  # 2. worker
uv run uvicorn recon_ai_api.main:app --reload        # 3. API on :8000
cd apps/web && npm run dev                           # 4. UI on :3000
```

The worker matters. Without it a job sits in `queued` forever, because nothing pops the queue.

Open <http://localhost:3000>, upload a bank statement and a ledger, and watch the job move through its stages. When it completes, the assistant reports on it and the review tabs fill in.

### A sample conversation

> **You:** How did it go?
>
> **Recon AI:** 45 of 50 bank rows matched automatically, all at 99 or 100. Nothing is waiting on your decision. Five rows on each side stayed unmatched.
>
> **You:** What's unmatched?
>
> **Recon AI:** Five bank transactions with no counterpart, including METRO MOBILITY on 10 Jul for -6,413.82. The closest ledger row is METRO MOBILITY on 11 Jul for -6,451.32 — same reference suffix, one day later, 37.50 apart. That gap looks like a fee rather than a different transaction.
>
> **You:** Pair those two.

## Useful commands

```bash
# Re-run matching on an existing job. No OpenAI calls, so it costs nothing.
curl -X POST http://localhost:8000/reconciliations/{job_id}/rematch

# Health
curl http://localhost:8000/health
curl http://localhost:8000/health/db

# Interactive API docs
open http://localhost:8000/docs

# Migrations
uv run alembic -c apps/api/alembic.ini revision --autogenerate -m "name"
uv run alembic -c apps/api/alembic.ini current

# Frontend gates
cd apps/web && npx tsc --noEmit && npm run lint && npm run build
```

Re-running matching discards every existing match, including ones you already approved or rejected. Those decisions have to be made again.

## Layout

```text
apps/api        FastAPI backend and Alembic migrations
apps/worker     RQ worker: PDF text, extraction, matching
apps/web        Next.js frontend
packages/core   Shared: models, schemas, matching, agent, tools, storage
docs            Architecture and the phase-by-phase build log
samples         Your test PDFs, not committed
```

Matching, reporting, the agent and its tools live in `packages/core` so the API and the worker run the same code rather than two versions of it.

## The agent

The assistant reaches the backend through eight typed tools and nothing else — no raw SQL, no database handle. Every call is recorded in `agent_actions` with its arguments and its result, so what it did on your behalf is auditable.

`get_reconciliation_status`, `get_reconciliation_summary`, `list_under_review_matches`, `list_unmatched_transactions`, `list_match_suggestions`, `approve_match`, `reject_match`, `manual_match`.

Starting a reconciliation is deliberately not a tool. Upload stores the PDFs and creates the job together, so a storage path only exists for a file just uploaded — an agent asked to start a job could only invent one.

It will not approve, reject, or pair anything without you naming which one.

## Known limitations

- **No authentication.** Every job is visible to every visitor. Single-user, local-first.
- **Text PDFs only.** Scanned statements need OCR, which is not implemented.
- **No tests.** Verification was manual and by throwaway script.
- **One currency per pair.** Rows whose currencies both exist and differ are never compared. No conversion.
- **One-to-one matching.** A payment split across two ledger entries will not match.
- **The file type is not validated.** Upload assumes both files really are PDFs.
- **Extraction quality depends on the statement.** An unusual layout may put a reference somewhere the prompt does not look, which shows up as a matching failure rather than an extraction one.

## Future work

OCR for scanned statements, CSV export, transaction search and categorization, grouped and partial-payment matching, authentication and multi-user workspaces, a deployment guide, and a test suite. Tracked in `docs/todo.md`.
