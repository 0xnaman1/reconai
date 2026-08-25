# Recon AI Todo

This file is the phase-wise execution checklist for building Recon AI. Complete phases in order unless a later task is clearly independent.

## Phase 0: Project Decisions

- [x] Confirm repository name and final app name: `Recon AI`.
- [x] Confirm OpenAI will be used for both structured extraction and chat agent responses.
- [x] Confirm Supabase Cloud will be used for Postgres and Storage.
- [x] Confirm no authentication for the MVP.
- [x] Confirm Python version: `3.14`.
- [x] Confirm Python package manager: `uv`.
- [x] Confirm database migration tool: `Alembic`.
- [x] Confirm background jobs: `Redis` plus `RQ`.

## Phase 1: Repository Bootstrap

- [x] Create root project structure.
- [x] Create `apps/api` for the FastAPI backend.
- [x] Create `apps/worker` for the RQ worker.
- [x] Create `apps/web` for the Next.js frontend.
- [x] Create `packages/core` for shared Python code.
- [x] Create `samples` folder for sample PDFs.
- [x] Create `.python-version` with `3.14`.
- [x] Create root `pyproject.toml` with uv workspace configuration.
- [x] Create `.env.example`.
- [x] Create `.gitignore`.
- [x] Create initial `README.md`.
- [x] Create `docker-compose.yml` with Redis service.

## Phase 2: Python Workspace Setup

- [x] Initialize `packages/core` Python package.
- [x] Initialize `apps/api` Python package.
- [x] Initialize `apps/worker` Python package.
- [x] Configure all Python packages with `requires-python = ">=3.14"`.
- [x] Add core backend dependencies.
- [x] Add FastAPI dependencies to `apps/api`.
- [x] Add RQ worker dependencies to `apps/worker`.
- [x] Run `uv sync` successfully.
- [x] Verify imports work across workspace packages.

## Phase 3: Supabase Cloud Setup

- [x] Create Supabase Cloud project.
- [x] Copy Supabase project URL into `.env`.
- [x] Copy Supabase secret key into `.env`.
- [x] Copy Postgres connection string into `.env` as `DATABASE_URL`.
- [x] Create Supabase Storage bucket named `reconciliation-documents`.
- [x] Document bucket setup in `README.md`.
- [x] Verify local backend can connect to Supabase Postgres.
- [x] Verify local backend can access Supabase Storage.

## Phase 4: Shared Core Package

- [x] Add application settings with `pydantic-settings`.
- [x] Add database engine and session helpers.
- [x] Add SQLAlchemy base metadata.
- [x] Add SQLAlchemy models for reconciliation jobs.
- [x] Add SQLAlchemy models for transactions.
- [x] Add SQLAlchemy models for matches.
- [x] Add SQLAlchemy models for chat sessions.
- [x] Add SQLAlchemy models for chat messages.
- [x] Add SQLAlchemy models for agent actions.
- [x] Add Pydantic schemas for extracted transactions.
- [x] Add Pydantic schemas for API responses.
- [x] Add shared enum-like constants for statuses and sources.

## Phase 5: Alembic Migrations

- [x] Configure Alembic in `apps/api`.
- [x] Make Alembic load environment variables from `.env`.
- [x] Make Alembic import SQLAlchemy metadata from `packages/core`.
- [x] Generate initial migration.
- [x] Review generated migration manually.
- [x] Apply migration to Supabase Cloud Postgres.
- [x] Verify tables exist in Supabase dashboard.
- [x] Add migration commands to `README.md`.

## Phase 6: FastAPI Skeleton

- [x] Create FastAPI application entrypoint.
- [x] Add health check endpoint.
- [x] Add database session dependency.
- [x] Add CORS configuration for local Next.js frontend.
- [x] Add global error handling for expected application errors.
- [x] Add basic API router structure.
- [x] Run API locally with `uvicorn`.
- [x] Verify health endpoint works.

## Phase 7: Worker Skeleton

- [x] Create RQ worker entrypoint.
- [x] Add Redis connection helper.
- [x] Add queue helper for reconciliation jobs.
- [x] Add placeholder `process_reconciliation_job(job_id)` task.
- [x] Run Redis locally with Docker Compose.
- [x] Run RQ worker locally.
- [x] Enqueue and execute a sample job manually.

## Phase 8: Supabase Storage Integration

- [x] Add Supabase client helper in `packages/core`.
- [x] Add file upload helper for PDFs.
- [x] Add file download helper for worker processing.
- [x] Add predictable storage path format for reconciliation PDFs.
- [x] Skip PDF file type validation for MVP assumption.
- [x] Verify upload to Supabase Storage manually.
- [x] Verify download from Supabase Storage manually.

## Phase 9: Reconciliation Job API

- [x] Add `POST /reconciliations` endpoint.
- [x] Accept bank PDF and ledger PDF as multipart uploads.
- [x] Upload both PDFs to Supabase Storage.
- [x] Create `reconciliation_jobs` row with status `queued`.
- [x] Queue RQ job with the created job ID.
- [x] Return job ID and status.
- [x] Add `GET /reconciliations/{job_id}` endpoint.
- [x] Add job summary response fields.

## Phase 10: PDF Text Extraction

- [x] Add PDF text extraction module using `pypdf`.
- [x] Extract text from all pages.
- [x] Handle empty PDFs with a clear error.
- [x] Handle parser failures with a clear error.
- [x] Integrate PDF extraction into worker job.
- [x] Update job status to `extracting` during extraction.

## Phase 11: OpenAI Structured Extraction

- [x] Add OpenAI client helper.
- [x] Add bank transaction extraction prompt.
- [x] Add ledger transaction extraction prompt.
- [x] Define strict structured output schema.
- [x] Parse OpenAI response into Pydantic models.
- [x] Validate bank withdrawal/deposit signed amount normalization.
- [x] Validate ledger signed amount normalization.
- [x] Add helpful failure handling for malformed LLM output.
- [x] Store raw transaction text when available.

## Phase 12: Transaction Storage

- [x] Insert extracted bank transactions with `source = "bank"`.
- [x] Insert extracted ledger transactions with `source = "ledger"`.
- [x] Store optional bank closing balance in transaction metadata.
- [x] Store optional ledger notes and tags in transaction metadata.
- [x] Ensure amounts use decimal-safe handling.
- [x] Add `GET /reconciliations/{job_id}/transactions` endpoint.

## Phase 13: Matching Engine

- [x] Implement exact amount matching.
- [x] Implement date exact match scoring.
- [x] Implement date tolerance scoring.
- [x] Implement reference number scoring.
- [x] Implement description similarity scoring with `rapidfuzz`.
- [x] Implement one-to-one best candidate selection.
- [x] Store auto matches with status `matched`.
- [x] Store review matches with status `under_review`.
- [x] Leave low-confidence transactions unmatched.
- [x] Store clear match reasons.
- [x] Integrate matching engine into worker job.
- [x] Update job status to `matching` during matching.
- [x] Update job status to `completed` after matching.

## Phase 14: Review API

- [x] Add `GET /reconciliations/{job_id}/matches` endpoint.
- [x] Add filtering by match status.
- [x] Add `POST /matches/{match_id}/approve` endpoint.
- [x] Add `POST /matches/{match_id}/reject` endpoint.
- [x] Make approve set match status to `reconciled`.
- [x] Make reject set match status to `rejected`.

## Phase 15: Chat Data Model API

- [x] Add `POST /chat/sessions` endpoint.
- [x] Add `GET /chat/sessions/{session_id}/messages` endpoint.
- [x] Add `POST /chat/sessions/{session_id}/messages` endpoint.
- [x] Persist user messages.
- [x] Persist assistant messages.
- [x] Persist tool messages.
- [x] Track active reconciliation job on chat session.

## Phase 16: Agent Tool Layer

- [x] Implement `create_reconciliation_job` tool.
- [x] Implement `get_reconciliation_status` tool.
- [x] Implement `get_reconciliation_summary` tool.
- [x] Implement `list_under_review_matches` tool.
- [x] Implement `approve_match` tool.
- [x] Implement `reject_match` tool.
- [x] Implement `list_unmatched_transactions` tool.
- [x] Log tool calls to `agent_actions`.
- [x] Ensure tools use controlled inputs only.
- [x] Do not add raw SQL tool in MVP.

## Phase 17: OpenAI Chat Agent

- [x] Add chat agent system prompt.
- [x] Register backend tools with OpenAI tool calling.
- [x] Implement agent orchestration loop.
- [x] Execute requested tools server-side.
- [x] Persist assistant responses.
- [x] Persist tool call results.
- [x] Make the agent explain job status clearly.
- [x] Make the agent present under-review matches clearly.
- [x] Make the agent ask for approval or rejection when needed.

## Phase 18: Next.js Frontend Bootstrap

- [x] Create Next.js app in `apps/web`.
- [x] Configure TypeScript.
- [x] Configure Tailwind CSS.
- [x] Add API client helper.
- [x] Add environment variable for backend URL.
- [x] Create base layout.
- [x] Create home page.
- [x] Verify frontend runs locally.

## Phase 19: Chat UI

- [x] Build chat transcript component.
- [x] Build message input component.
- [x] Build file upload component for bank PDF.
- [x] Build file upload component for ledger PDF.
- [x] Allow upload submission from chat.
- [x] Create chat session on first load.
- [x] Send user messages to backend.
- [x] Render assistant responses.
- [x] Render loading and processing states.
- [x] Handle API errors in the UI.

## Phase 20: Reconciliation Review UI

- [x] Build job status card.
- [x] Build reconciliation summary card.
- [x] Build under-review match card.
- [x] Show bank transaction details in review card.
- [x] Show ledger transaction details in review card.
- [x] Show confidence score and match reason.
- [x] Add approve button.
- [x] Add reject button.
- [x] Refresh chat or summary after approve/reject.
- [x] Add optional read-only reconciliation detail page.

## Phase 21: End-To-End Flow

- [x] Run the whole pipeline against real statements: Redis, API, worker and
      frontend together, upload through to reviewed matches.

## Phase 22: Beyond The Original Plan

Built after the numbered phases, in response to using the app:

- [x] Reconcile transactions the engine left unmatched. Ranked suggestions per
      unmatched transaction plus a manual pairing endpoint, agent tools and UI.
- [x] Work on several reconciliations from one conversation, with a job list,
      copyable job ids and per-job tabs for the two review queues.
- [x] Bind a job to the chat session over HTTP, so the agent no longer needs the
      job id named in prose.
- [x] Recover from a chat session id whose row no longer exists.
- [x] Remove the `create_reconciliation_job` agent tool. Storage paths only
      exist for a file just uploaded, so the model could only ever invent them.

## Phase 23: Documentation

- [x] README with overview, architecture, setup, commands and limitations.
- [ ] Screenshots or a GIF of the app.

## Deferred Enhancements

- [x] Add manual matching through agent tools.
- [ ] Add OCR for scanned PDFs.
- [ ] Add local model support with Ollama.
- [ ] Add monthly spend query tool.
- [ ] Add transaction search tool.
- [ ] Add transaction categorization.
- [ ] Add grouped transaction matching.
- [ ] Add partial payment matching.
- [ ] Add CSV export.
- [ ] Add authentication.
- [ ] Add multi-user workspaces.
- [ ] Add deployment guide.
- [ ] Add automated tests.
