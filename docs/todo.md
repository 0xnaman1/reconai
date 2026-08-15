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

- [ ] Add PDF text extraction module using `pypdf`.
- [ ] Extract text from all pages.
- [ ] Handle empty PDFs with a clear error.
- [ ] Handle parser failures with a clear error.
- [ ] Add sample PDF fixtures to `samples` if safe to commit.
- [ ] Integrate PDF extraction into worker job.
- [ ] Update job status to `extracting` during extraction.

## Phase 11: OpenAI Structured Extraction

- [ ] Add OpenAI client helper.
- [ ] Add bank transaction extraction prompt.
- [ ] Add ledger transaction extraction prompt.
- [ ] Define strict structured output schema.
- [ ] Parse OpenAI response into Pydantic models.
- [ ] Validate bank withdrawal/deposit signed amount normalization.
- [ ] Validate ledger signed amount normalization.
- [ ] Add helpful failure handling for malformed LLM output.
- [ ] Store raw transaction text when available.

## Phase 12: Transaction Storage

- [ ] Insert extracted bank transactions with `source = "bank"`.
- [ ] Insert extracted ledger transactions with `source = "ledger"`.
- [ ] Store optional bank closing balance in transaction metadata.
- [ ] Store optional ledger notes and tags in transaction metadata.
- [ ] Ensure amounts use decimal-safe handling.
- [ ] Add `GET /reconciliations/{job_id}/transactions` endpoint.

## Phase 13: Matching Engine

- [ ] Implement exact amount matching.
- [ ] Implement date exact match scoring.
- [ ] Implement date tolerance scoring.
- [ ] Implement reference number scoring.
- [ ] Implement description similarity scoring with `rapidfuzz`.
- [ ] Implement one-to-one best candidate selection.
- [ ] Store auto matches with status `matched`.
- [ ] Store review matches with status `under_review`.
- [ ] Leave low-confidence transactions unmatched.
- [ ] Store clear match reasons.
- [ ] Integrate matching engine into worker job.
- [ ] Update job status to `matching` during matching.
- [ ] Update job status to `completed` after matching.

## Phase 14: Review API

- [ ] Add `GET /reconciliations/{job_id}/matches` endpoint.
- [ ] Add filtering by match status.
- [ ] Add `POST /matches/{match_id}/approve` endpoint.
- [ ] Add `POST /matches/{match_id}/reject` endpoint.
- [ ] Make approve set match status to `reconciled`.
- [ ] Make reject set match status to `rejected`.

## Phase 15: Chat Data Model API

- [ ] Add `POST /chat/sessions` endpoint.
- [ ] Add `GET /chat/sessions/{session_id}/messages` endpoint.
- [ ] Add `POST /chat/sessions/{session_id}/messages` endpoint.
- [ ] Persist user messages.
- [ ] Persist assistant messages.
- [ ] Persist tool messages.
- [ ] Track active reconciliation job on chat session.

## Phase 16: Agent Tool Layer

- [ ] Implement `create_reconciliation_job` tool.
- [ ] Implement `get_reconciliation_status` tool.
- [ ] Implement `get_reconciliation_summary` tool.
- [ ] Implement `list_under_review_matches` tool.
- [ ] Implement `approve_match` tool.
- [ ] Implement `reject_match` tool.
- [ ] Implement `list_unmatched_transactions` tool.
- [ ] Log tool calls to `agent_actions`.
- [ ] Ensure tools use controlled inputs only.
- [ ] Do not add raw SQL tool in MVP.

## Phase 17: OpenAI Chat Agent

- [ ] Add chat agent system prompt.
- [ ] Register backend tools with OpenAI tool calling.
- [ ] Implement agent orchestration loop.
- [ ] Execute requested tools server-side.
- [ ] Persist assistant responses.
- [ ] Persist tool call results.
- [ ] Make the agent explain job status clearly.
- [ ] Make the agent present under-review matches clearly.
- [ ] Make the agent ask for approval or rejection when needed.

## Phase 18: Next.js Frontend Bootstrap

- [ ] Create Next.js app in `apps/web`.
- [ ] Configure TypeScript.
- [ ] Configure Tailwind CSS.
- [ ] Add API client helper.
- [ ] Add environment variable for backend URL.
- [ ] Create base layout.
- [ ] Create home page.
- [ ] Verify frontend runs locally.

## Phase 19: Chat UI

- [ ] Build chat transcript component.
- [ ] Build message input component.
- [ ] Build file upload component for bank PDF.
- [ ] Build file upload component for ledger PDF.
- [ ] Allow upload submission from chat.
- [ ] Create chat session on first load.
- [ ] Send user messages to backend.
- [ ] Render assistant responses.
- [ ] Render loading and processing states.
- [ ] Handle API errors in the UI.

## Phase 20: Reconciliation Review UI

- [ ] Build job status card.
- [ ] Build reconciliation summary card.
- [ ] Build under-review match card.
- [ ] Show bank transaction details in review card.
- [ ] Show ledger transaction details in review card.
- [ ] Show confidence score and match reason.
- [ ] Add approve button.
- [ ] Add reject button.
- [ ] Refresh chat or summary after approve/reject.
- [ ] Add optional read-only reconciliation detail page.

## Phase 21: End-To-End Flow

- [ ] Start Redis.
- [ ] Start FastAPI API.
- [ ] Start RQ worker.
- [ ] Start Next.js frontend.
- [ ] Upload sample bank PDF and ledger PDF.
- [ ] Confirm PDFs are stored in Supabase Storage.
- [ ] Confirm job is created in Supabase Postgres.
- [ ] Confirm worker extracts PDF text.
- [ ] Confirm OpenAI returns structured transactions.
- [ ] Confirm transactions are stored.
- [ ] Confirm matching engine creates matches.
- [ ] Confirm chat agent summarizes results.
- [ ] Confirm under-review matches appear in chat.
- [ ] Confirm approve/reject updates match status.

## Phase 22: Manual Verification And Quality

- [ ] Run the backend locally.
- [ ] Run the worker locally.
- [ ] Run the frontend locally.
- [ ] Manually verify PDF upload works.
- [ ] Manually verify the worker processes a reconciliation job.
- [ ] Manually verify OpenAI extraction returns structured transactions.
- [ ] Manually verify matching results look reasonable with sample PDFs.
- [ ] Manually verify approve and reject actions update match status.
- [ ] Run frontend linting.
- [ ] Run frontend build.

## Phase 23: Documentation

- [ ] Update `README.md` with product overview.
- [ ] Add architecture diagram or text diagram.
- [ ] Add Supabase Cloud setup instructions.
- [ ] Add OpenAI API setup instructions.
- [ ] Add local development commands.
- [ ] Add Alembic migration commands.
- [ ] Add sample workflow.
- [ ] Add screenshots or GIFs.
- [ ] Add known limitations.
- [ ] Add future improvements.
- [ ] Add resume bullet suggestions.

## Phase 24: MVP Polish

- [ ] Improve error messages for failed PDF extraction.
- [ ] Improve error messages for failed OpenAI extraction.
- [ ] Improve empty state in chat UI.
- [ ] Improve loading states while worker job runs.
- [ ] Add clear display for auto matched, under review, reconciled, rejected, and unmatched counts.
- [ ] Ensure UI works on desktop.
- [ ] Ensure UI works on mobile.
- [ ] Remove unused code.
- [ ] Check `.env` and secrets are not committed.
- [ ] Do final end-to-end demo run.

## Deferred Enhancements

- [ ] Add OCR for scanned PDFs.
- [ ] Add local model support with Ollama.
- [ ] Add manual matching through agent tools.
- [ ] Add monthly spend query tool.
- [ ] Add transaction search tool.
- [ ] Add transaction categorization.
- [ ] Add grouped transaction matching.
- [ ] Add partial payment matching.
- [ ] Add CSV export.
- [ ] Add authentication.
- [ ] Add multi-user workspaces.
- [ ] Add deployment guide.
