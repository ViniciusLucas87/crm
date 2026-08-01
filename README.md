# Pacific North Systems Sales OS

Sprint 1 release candidate for Pacific North Systems' founder-led sales operating system.

## Stack

- Web: Next.js 15, React 19 RC, TypeScript, Tailwind CSS
- API: FastAPI, SQLAlchemy, Alembic
- Data: PostgreSQL, Redis
- Jobs: Celery worker
- Infra: Docker Compose, GitHub Actions

## Sprint 1 Scope

- Dashboard summary page backed by PostgreSQL aggregates
- Companies module with create, list, update, archive, restore, duplicate, search, sorting, pagination, and filtering
- Auth context endpoint plus permission-protected API routes
- Shared dashboard contract in `packages/contracts`
- Dockerized local stack for web, API, worker, PostgreSQL, and Redis

## Monorepo Layout

- `apps/web`: Next.js dashboard and companies UI
- `apps/api`: FastAPI application using domain/application/infrastructure/presentation boundaries
- `apps/worker`: Celery worker process
- `packages/contracts`: shared TypeScript contracts
- `docs`: architecture and release documentation

## Prerequisites

- Node.js 20+
- Python 3.12+
- Docker Desktop with Compose
- pnpm 9+

## Environment

Use `.env.example` as the starting point for local and deployment configuration.

Important:

- Protected API routes require Clerk configuration.
- Set `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY` for web runtime.
- Set `CLERK_ISSUER` and `CLERK_JWKS_URL` for API JWT verification.

## Local Commands

Install frontend dependencies:

```bash
pnpm install
```

Run frontend validation:

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

Run backend validation:

```bash
python -m ruff check apps/api/app apps/api/tests
python -m black --check apps/api/app apps/api/tests
python -m pytest apps/api/tests -q
```

Run database migrations:

```bash
cd apps/api
python -m alembic upgrade head
```

Start the API locally:

```bash
python -m uvicorn app.main:app --app-dir apps/api --host 127.0.0.1 --port 8000
```

## Docker

Build and run the full stack:

```bash
docker compose up --build
```

Services:

- Web: http://localhost:3000
- API: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Current Protected Routes

- `GET /api/v1/auth/me`
- `GET /api/v1/dashboard/summary`
- `POST /api/v1/companies`
- `GET /api/v1/companies`
- `GET /api/v1/companies/{company_id}`
- `PATCH /api/v1/companies/{company_id}`
- `DELETE /api/v1/companies/{company_id}`
- `POST /api/v1/companies/{company_id}/restore`
- `POST /api/v1/companies/{company_id}/duplicate`

## Quality Gates

- `pnpm lint`
- `pnpm typecheck`
- `pnpm test`
- `pnpm build`
- `python -m ruff check apps/api/app apps/api/tests`
- `python -m black --check apps/api/app apps/api/tests`
- `python -m pytest apps/api/tests -q`

## Documentation

- See `docs/architecture.md` for the current Sprint 1 architecture and inventories.
- See `docs/release-v0.1.0.md` for release notes and the release candidate review summary.
