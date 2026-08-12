# Recon AI Decisions

This document records confirmed implementation decisions for the MVP.

## Product

- App name: `Recon AI`.
- Interface: chat-first client interface.
- MVP scope: local app with Supabase Cloud services.
- Authentication: not included in the MVP.
- Human review: handled through the chat agent.
- Automated tests: not included in the MVP; use manual verification.

## Backend

- Runtime: Python `3.14`.
- Package manager: `uv`.
- API framework: FastAPI.
- Background jobs: Redis plus RQ.
- Migrations: Alembic.
- PDF text extraction: `pypdf` initially.
- Validation: Pydantic.

## Data

- Database: Supabase Cloud Postgres.
- Object storage: Supabase Cloud Storage.
- Database access: SQLAlchemy plus psycopg.
- Schema changes: Alembic migrations managed from this repository.

## LLM

- Provider: OpenAI API.
- Uses: structured transaction extraction and chat agent responses.
- The LLM does not directly write arbitrary database changes.
- The chat agent interacts with the backend through controlled tools.

## Frontend

- Framework: Next.js.
- Language: TypeScript.
- Styling: Tailwind CSS.
- Primary UI: chat transcript with PDF upload and match review cards.
