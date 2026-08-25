# Recon AI Architecture

Recon AI is a local-first, open-source reconciliation assistant for matching bank statement transactions against general ledger transactions. It is designed as a small resume-friendly project, not a production-grade accounting system.

The main interface is a chat agent. Users upload two PDFs, ask questions, review uncertain matches, and approve or reject reconciliation decisions through chat.

## Goals

- Accept two PDF statements: a bank statement and a general ledger statement.
- Extract transaction rows from PDFs using PDF parsing and OpenAI structured outputs.
- Validate extracted transactions with Pydantic.
- Store PDFs in Supabase Storage and structured data in Supabase Cloud Postgres.
- Run deterministic exact and fuzzy reconciliation matching.
- Use a chat agent as the primary user interface.
- Support human-in-the-loop review through agent-guided approval and rejection.
- Keep the application easy for an individual developer to run locally.

## Non-Goals

- No authentication for the MVP.
- No multi-user permissions.
- No OCR in the first version.
- No raw SQL access through the agent.
- No production deployment requirements.
- No complex accounting workflows such as split transactions, partial payments, or multi-currency accounting in the MVP.

## Technology Stack

### Backend

- Python 3.14
- uv package manager
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- psycopg
- RQ
- Redis
- pypdf
- OpenAI API
- Supabase Python client

### Frontend

- Next.js
- TypeScript
- Tailwind CSS
- Chat-first interface

### Data And Infrastructure

- Supabase Cloud Postgres
- Supabase Cloud Storage
- Redis for local background jobs
- Alembic for database migrations
- OpenAI API for structured extraction and chat agent tool calling

## High-Level Architecture

```text
Next.js Chat UI
        |
        v
FastAPI Chat API
        |
        v
Agent Orchestrator
        |
        v
Controlled Backend Tools
        |
        +------------------------+
        |                        |
        v                        v
Supabase Cloud              Redis + RQ Worker
Postgres + Storage               |
                                 v
                         PDF Text Extraction
                                 |
                                 v
                         OpenAI Structured Extraction
                                 |
                                 v
                         Pydantic Validation
                                 |
                                 v
                         Transaction Storage
                                 |
                                 v
                         Matching Engine
```

## Project Structure

```text
recon-ai/
  apps/
    api/
      pyproject.toml
      alembic.ini
      alembic/
      src/recon_ai_api/
    web/
      package.json
      src/
    worker/
      pyproject.toml
      src/recon_ai_worker/
  packages/
    core/
      pyproject.toml
      src/recon_ai_core/
  docs/
    architecture.md
  samples/
    bank_statement.pdf
    ledger_statement.pdf
  .env.example
  .python-version
  docker-compose.yml
  pyproject.toml
  uv.lock
  README.md
```

## Python Workspace

The Python code should use a uv workspace.

Root `pyproject.toml`:

```toml
[tool.uv.workspace]
members = [
  "apps/api",
  "apps/worker",
  "packages/core"
]
```

Python version:

```text
3.14
```

Each Python package should declare:

```toml
requires-python = ">=3.14"
```

The shared `packages/core` package should contain reusable code used by both the API and worker:

- Pydantic schemas
- SQLAlchemy models
- Database session helpers
- Supabase Storage helpers
- OpenAI extraction code
- Matching engine
- Agent tool definitions
- Shared settings

## Environment Variables

The project should provide a `.env.example` with at least:

```env
DATABASE_URL=postgresql+psycopg://postgres:<password>@<host>:5432/postgres
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SECRET_KEY=your-supabase-secret-key
SUPABASE_STORAGE_BUCKET=reconciliation-documents

OPENAI_API_KEY=your-openai-api-key
OPENAI_CHAT_MODEL=gpt-4.1
OPENAI_EXTRACTION_MODEL=gpt-4.1

REDIS_URL=redis://localhost:6379/0
API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Use Supabase Cloud for Postgres and Storage. Use local Redis for RQ jobs.

## Supabase Cloud Setup

The MVP should use Supabase Cloud, not local Supabase.

Setup steps:

1. Create a Supabase Cloud project.
2. Copy the project URL into `SUPABASE_URL`.
3. Copy the secret key into `SUPABASE_SECRET_KEY`.
4. Copy the Postgres connection string into `DATABASE_URL`.
5. Create a Storage bucket named `reconciliation-documents`.
6. Run Alembic migrations against the Supabase Postgres database.

For Alembic migrations, prefer the direct Postgres connection string or Supabase session pooler. Avoid the transaction pooler for migrations because schema migrations can require connection-level behavior that transaction pooling may not support well.

## Database Migrations

Alembic is the source of truth for database schema changes.

SQLAlchemy models should live in `packages/core`. Alembic should import the shared metadata from the core package so migrations can be autogenerated from models.

Initial migration:

```text
0001_initial_schema.py
```

It should create:

- `reconciliation_jobs`
- `transactions`
- `matches`
- `chat_sessions`
- `chat_messages`
- `agent_actions`

Common commands:

```bash
uv run alembic revision --autogenerate -m "initial schema"
uv run alembic upgrade head
```

## Data Model

### reconciliation_jobs

Tracks one reconciliation run for one bank PDF and one ledger PDF.

Columns:

- `id`: UUID primary key
- `status`: text
- `bank_pdf_path`: text
- `ledger_pdf_path`: text
- `error_message`: text nullable
- `created_at`: timestamp with time zone
- `updated_at`: timestamp with time zone

Job statuses:

- `queued`
- `processing`
- `extracting`
- `matching`
- `completed`
- `failed`

### transactions

Stores normalized transactions from both sources.

Columns:

- `id`: UUID primary key
- `job_id`: UUID foreign key to `reconciliation_jobs.id`
- `source`: text, either `bank` or `ledger`
- `transaction_date`: date
- `description`: text
- `reference_number`: text nullable
- `amount`: numeric
- `currency`: text nullable
- `raw_text`: text nullable
- `metadata`: JSONB
- `created_at`: timestamp with time zone

### matches

Stores candidate and confirmed matches between bank and ledger transactions.

Columns:

- `id`: UUID primary key
- `job_id`: UUID foreign key to `reconciliation_jobs.id`
- `bank_transaction_id`: UUID foreign key to `transactions.id`
- `ledger_transaction_id`: UUID foreign key to `transactions.id`
- `match_type`: text
- `confidence_score`: integer
- `status`: text
- `reason`: text
- `created_at`: timestamp with time zone
- `updated_at`: timestamp with time zone

Match types:

- `exact`
- `fuzzy`
- `manual`

Match statuses:

- `matched`
- `under_review`
- `reconciled`
- `rejected`

### chat_sessions

Stores chat conversations.

Columns:

- `id`: UUID primary key
- `active_job_id`: UUID nullable foreign key to `reconciliation_jobs.id`
- `created_at`: timestamp with time zone
- `updated_at`: timestamp with time zone

### chat_messages

Stores chat history.

Columns:

- `id`: UUID primary key
- `session_id`: UUID foreign key to `chat_sessions.id`
- `role`: text
- `content`: text
- `metadata`: JSONB
- `created_at`: timestamp with time zone

Roles:

- `system`
- `user`
- `assistant`
- `tool`

### agent_actions

Stores tool calls made by the agent for traceability.

Columns:

- `id`: UUID primary key
- `session_id`: UUID nullable foreign key to `chat_sessions.id`
- `job_id`: UUID nullable foreign key to `reconciliation_jobs.id`
- `tool_name`: text
- `tool_input`: JSONB
- `tool_output`: JSONB
- `created_at`: timestamp with time zone

## Transaction Normalization

The matching engine should compare transactions using a single signed amount convention.

### Bank Statement Input

Expected bank columns:

- Date
- Description
- Reference Number
- Withdrawal Amount
- Deposit Amount
- Closing Balance

Bank normalization:

```text
withdrawal_amount > 0 => amount = -withdrawal_amount
deposit_amount > 0    => amount = deposit_amount
```

The closing balance should be stored in `metadata` if extracted, but it should not be used for transaction matching in the MVP.

### General Ledger Input

Expected ledger columns:

- Date
- Transaction Details
- Notes and Tags
- Amount

Ledger normalization:

```text
amount = ledger amount
description = transaction details
metadata.notes_and_tags = notes and tags
```

## PDF Extraction

The worker should use `pypdf` for text extraction.

MVP constraints:

- Support text-based PDFs only.
- Mark the job as `failed` if no text can be extracted.
- Do not include OCR in the first version.

Worker flow:

```text
Download PDFs from Supabase Storage
Extract text with pypdf
Send extracted text to OpenAI structured extraction
Validate with Pydantic
Store transactions
Run matching engine
Mark job completed or failed
```

## OpenAI Structured Extraction

OpenAI should be used to convert extracted PDF text into strict transaction JSON.

Make two extraction calls:

- One for bank transactions
- One for ledger transactions

Expected response shape:

```json
{
  "transactions": [
    {
      "transaction_date": "2026-08-01",
      "description": "AWS PAYMENT",
      "reference_number": "TXN123",
      "amount": -250.0,
      "currency": "USD",
      "raw_text": "AWS PAYMENT TXN123 250.00"
    }
  ]
}
```

The Pydantic model should enforce:

- Valid date values
- Required description
- Decimal-compatible amount values
- Optional reference number
- Optional currency
- Optional raw source text

If validation fails, mark the job as `failed` and save a helpful error message on `reconciliation_jobs.error_message`.

## Matching Engine

The matching engine should be deterministic backend code. The chat agent may explain and review matches, but it should not decide matches directly.

For the MVP, use one-to-one matching:

- One bank transaction can match one ledger transaction.
- One ledger transaction can match one bank transaction.
- Do not support split or grouped transactions initially.

Suggested scoring:

```text
Amount exact match:        40 points
Date exact match:          25 points
Date within 1-3 days:      15-20 points
Reference exact match:     25 points
Description similarity:    10 points
```

Suggested thresholds:

```text
90-100: auto matched
70-89:  under review
<70:    unmatched
```

Implementation notes:

- Compare bank transactions against available ledger transactions.
- Give the amount match the highest priority.
- Use date tolerance for bank posting delays.
- Use reference number as a strong signal when present.
- Use description similarity as a supporting signal, not the primary signal.
- Store the best candidate above the review threshold.
- Avoid matching the same ledger transaction twice.

Example match reason:

```text
Amount matched exactly, reference matched, transaction dates differ by 1 day.
```

Use `rapidfuzz` for description similarity.

## Chat Agent

The chat agent is the primary application interface.

Responsibilities:

- Guide the user through uploading bank and ledger PDFs.
- Start reconciliation jobs.
- Report job status and results.
- Present under-review matches.
- Ask the user to approve or reject uncertain matches.
- Answer controlled questions about reconciliation data.

The agent should use OpenAI tool calling with backend-defined tools. It should not receive raw database write access.

## Agent Tools

MVP tools:

```text
get_reconciliation_status(job_id)
get_reconciliation_summary(job_id)
list_under_review_matches(job_id)
approve_match(match_id)
reject_match(match_id)
list_unmatched_transactions(job_id)
list_match_suggestions(job_id)
manual_match(bank_transaction_id, ledger_transaction_id)
```

Creating a reconciliation is not a tool. The upload endpoint stores both PDFs
and creates the job together, so a storage path only exists for a file that was
just uploaded. An agent asked to start a job has no way to obtain one and would
invent it, creating a job whose PDFs do not exist.

Future tools:

```text
query_spend_by_month(month, year)
query_transactions(filters)
```

Do not implement a raw SQL tool for the MVP. Controlled query tools are safer, easier to explain, and better suited to a resume project.

## API Design

FastAPI should expose both chat endpoints and reconciliation endpoints.

Chat endpoints:

```text
POST /chat/sessions
GET /chat/sessions/{session_id}/messages
POST /chat/sessions/{session_id}/messages
```

Reconciliation endpoints:

```text
POST /reconciliations
GET /reconciliations/{job_id}
GET /reconciliations/{job_id}/matches
GET /reconciliations/{job_id}/transactions
```

Review endpoints:

```text
POST /matches/{match_id}/approve
POST /matches/{match_id}/reject
```

The chat UI can call the chat endpoints for natural language interaction and call review endpoints directly for approve/reject buttons.

## Worker Design

Use RQ with Redis for asynchronous reconciliation processing.

Primary job:

```text
process_reconciliation_job(job_id)
```

Steps:

1. Mark job as `processing`.
2. Download PDFs from Supabase Storage.
3. Mark job as `extracting`.
4. Extract text from both PDFs.
5. Call OpenAI structured extraction for bank transactions.
6. Call OpenAI structured extraction for ledger transactions.
7. Validate extracted transactions with Pydantic.
8. Store normalized transactions.
9. Mark job as `matching`.
10. Run matching engine.
11. Store matches.
12. Mark job as `completed`.
13. On any unrecoverable error, mark job as `failed` and store `error_message`.

## Frontend Design

The main UI is a chat page.

Pages:

```text
/
/reconciliations/[id]
```

The home page should contain:

- Chat transcript
- File upload controls for bank and ledger PDFs
- Assistant responses
- Job status cards
- Match review cards
- Approve and reject buttons

The reconciliation detail page is optional for the MVP but useful for debugging and screenshots. It can show:

- Job status
- Bank transaction count
- Ledger transaction count
- Auto matched count
- Under-review count
- Reconciled count
- Rejected count
- Unmatched transactions

## Human-In-The-Loop Review

Under-review matches should be presented by the chat agent.

Example interaction:

```text
Assistant: I found a possible match with 82% confidence.

Bank: Aug 3, AWS PAYMENT, reference TXN123, -250.00
Ledger: Aug 4, Amazon Web Services invoice, -250.00
Reason: Amount matched exactly, date differs by 1 day, descriptions are similar.

Should I approve this match?
```

If approved:

```text
matches.status = reconciled
```

If rejected:

```text
matches.status = rejected
```

Manual matching should be added after the first MVP.

## Build Order

1. Create monorepo structure.
2. Configure uv workspace and Python 3.14.
3. Create `packages/core` with settings, schemas, SQLAlchemy models, and database helpers.
4. Configure Alembic in `apps/api`.
5. Create and run the initial migration against Supabase Cloud Postgres.
6. Create the Supabase Storage bucket.
7. Build FastAPI app skeleton.
8. Build Redis and RQ worker skeleton.
9. Build PDF upload endpoint and store files in Supabase Storage.
10. Queue reconciliation jobs from the API.
11. Implement PDF text extraction with `pypdf`.
12. Implement OpenAI structured extraction.
13. Implement Pydantic validation and transaction storage.
14. Implement deterministic matching engine.
15. Add chat session and message endpoints.
16. Add OpenAI chat agent with controlled tools.
17. Build Next.js chat UI.
18. Add match review cards and approve/reject actions.
19. Add a read-only reconciliation detail page if useful.
20. Add README setup instructions, screenshots, and sample workflow.

## Local Development Commands

Expected setup:

```bash
cp .env.example .env
uv sync
docker compose up redis
uv run alembic upgrade head
uv run uvicorn recon_ai_api.main:app --reload
uv run rq worker --url redis://localhost:6379/0
npm run dev
```

These commands may be refined once the exact package scripts are created.

## Manual Verification Strategy

The MVP will not include an automated test suite. Quality should be checked through a focused manual demo flow using the sample bank statement and ledger PDFs.

Manual verification checklist:

- Start Redis, the FastAPI API, the RQ worker, and the Next.js frontend locally.
- Upload the sample bank statement and ledger PDFs through the chat UI.
- Confirm the PDFs are stored in Supabase Storage.
- Confirm a reconciliation job is created in Supabase Postgres.
- Confirm the worker extracts text from both PDFs.
- Confirm OpenAI returns structured transaction JSON.
- Confirm Pydantic validation accepts the extracted transactions.
- Confirm bank withdrawals are stored as negative amounts and deposits as positive amounts.
- Confirm ledger amounts preserve their existing sign.
- Confirm the matching engine creates reasonable auto-matched and under-review results.
- Confirm the chat agent summarizes the reconciliation clearly.
- Confirm approve and reject actions update match status correctly.
- Confirm frontend linting and build pass before considering the MVP complete.

## README Requirements

The README should include:

- What Recon AI does.
- Architecture diagram.
- Tech stack.
- Supabase Cloud setup.
- `.env` setup.
- Local run commands.
- Sample workflow.
- Screenshots or GIFs.
- Known limitations.
- Future improvements.

Suggested resume summary:

```text
Built an LLM-powered reconciliation assistant with FastAPI, Next.js, Supabase, OpenAI tool calling, structured extraction, deterministic fuzzy matching, and human-in-the-loop review.
```

## Future Improvements

- Add OCR for scanned PDFs.
- Add local model support with Ollama.
- Add manual matching through agent tools.
- Add controlled analytics tools such as monthly spend summaries.
- Add transaction categorization.
- Add authentication and multi-user workspaces.
- Add deployment documentation.
- Add support for grouped and partial matches.
- Add export to CSV.
- Add confidence calibration based on user feedback.
