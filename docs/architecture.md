# Sprint 1 Architecture

## System Summary

Sprint 1 ships a Dockerized monorepo with a Next.js frontend, a FastAPI backend, PostgreSQL persistence, Redis, and a Celery worker container. The only production user flows implemented in Sprint 1 are dashboard read access and company management.

## Major Modules

### Frontend

- `apps/web/src/app/layout.tsx`: app shell and global metadata
- `apps/web/src/app/page.tsx`: dashboard route
- `apps/web/src/app/companies/page.tsx`: companies route
- `apps/web/src/components/dashboard/*`: shell and KPI card components
- `apps/web/src/components/companies/companies-screen.tsx`: companies CRUD table, filters, and form
- `apps/web/src/lib/api.ts`: frontend HTTP client and DTO mapping
- `apps/web/src/lib/types.ts`: frontend view models

### Backend

- `apps/api/app/main.py`: FastAPI bootstrap and CORS
- `apps/api/app/presentation/api/v1/routes/*`: HTTP routes
- `apps/api/app/presentation/api/v1/deps.py`: dependency wiring
- `apps/api/app/application/*/services.py`: use-case orchestration
- `apps/api/app/domain/*`: repository contracts and DTOs
- `apps/api/app/infrastructure/repositories/*`: SQLAlchemy repository implementations
- `apps/api/app/infrastructure/auth/clerk.py`: Clerk JWT verification, permission checks, and org/user sync
- `apps/api/app/infrastructure/db/models.py`: SQLAlchemy models

### Shared Contracts

- `packages/contracts/src/index.ts`: shared dashboard contract for TypeScript consumers

### Worker

- `apps/worker/celery_app.py`: worker bootstrap

## Request Flow

1. The browser requests either `/` or `/companies` from Next.js.
2. The frontend route uses `apps/web/src/lib/api.ts` to call FastAPI.
3. FastAPI routes in `presentation/api/v1/routes` resolve services through `deps.py`.
4. Application services call repository interfaces implemented by SQLAlchemy adapters.
5. SQLAlchemy repositories read or write PostgreSQL tables defined in `infrastructure/db/models.py`.
6. Pydantic response models are returned to the frontend, which maps snake_case API payloads into camelCase view models.

## API Inventory

### Public endpoint

- `GET /api/v1/health`: health check, no authentication

### Protected endpoints

- `GET /api/v1/auth/me`: returns `AuthContext`
- `GET /api/v1/dashboard/summary`: returns dashboard KPI aggregate response
- `POST /api/v1/companies`: create company
- `GET /api/v1/companies`: list companies with paging, search, sort, owner, status, and archive filters
- `GET /api/v1/companies/{company_id}`: fetch one company
- `PATCH /api/v1/companies/{company_id}`: update one company
- `DELETE /api/v1/companies/{company_id}`: archive company
- `POST /api/v1/companies/{company_id}/restore`: restore company
- `POST /api/v1/companies/{company_id}/duplicate`: duplicate company

## Frontend Inventory

### `/`

- Components: `Shell`, `KpiGrid`, `Card`
- API dependency: `GET /api/v1/dashboard/summary`
- Loading state: none yet on the server route
- Empty state: KPI zeros are displayed when the database has no matching rows
- Error state: unauthorized and API failures render a dashboard-unavailable card

### `/companies`

- Components: `Shell`, `CompaniesScreen`, `Card`
- API dependencies:
	- `GET /api/v1/companies`
	- `POST /api/v1/companies`
	- `PATCH /api/v1/companies/{company_id}`
	- `DELETE /api/v1/companies/{company_id}`
	- `POST /api/v1/companies/{company_id}/restore`
	- `POST /api/v1/companies/{company_id}/duplicate`
- Loading state: inline table loading row
- Empty state: inline "No companies found" message
- Error state: inline error banner for unauthorized or request failures

## Database Inventory

### `companies`

- Columns: `id`, `organization_id`, `name`, `industry`, `website`, `phone`, `email`, `address`, `employees`, `revenue`, `status`, `tags`, `owner`, `notes`, `is_archived`, `created_at`, `updated_at`
- Indexes: `id`, `organization_id`, `name`, `owner`, `is_archived`
- Relationships: referenced by `opportunities.company_id`, `tasks.company_id`, `activities.company_id`

### `opportunities`

- Columns: `id`, `organization_id`, `company_id`, `status`, `value`, `forecast_value`, `created_at`
- Indexes: `organization_id`, `company_id`
- Foreign keys: `company_id -> companies.id`

### `tasks`

- Columns: `id`, `organization_id`, `company_id`, `title`, `due_date`, `is_completed`
- Indexes: `organization_id`, `due_date`, `is_completed`
- Foreign keys: `company_id -> companies.id`

### `activities`

- Columns: `id`, `organization_id`, `company_id`, `activity_type`, `due_date`, `created_at`
- Indexes: `organization_id`, `due_date`
- Foreign keys: `company_id -> companies.id`

### `organizations`

- Columns: `id`, `clerk_org_id`, `name`, `slug`, `created_at`
- Indexes: `clerk_org_id`, `slug`
- Relationships: referenced by `organization_memberships.organization_id`

### `users`

- Columns: `id`, `clerk_user_id`, `email`, `full_name`, `is_active`, `created_at`
- Indexes: `clerk_user_id`, `email`
- Relationships: referenced by `organization_memberships.user_id`

### `organization_memberships`

- Columns: `id`, `organization_id`, `user_id`, `role`, `created_at`
- Indexes: `organization_id`, `user_id`
- Foreign keys:
	- `organization_id -> organizations.id`
	- `user_id -> users.id`

## Migrations

- `20260717_0001_create_sales_foundation_tables.py`: creates `companies`, `opportunities`, `tasks`, and `activities`
- `20260717_0002_auth_foundation_tables.py`: creates `organizations`, `users`, and `organization_memberships`
- `20260717_0003_scope_sales_tables_to_organizations.py`: adds `organization_id` to sales tables and `clerk_org_id` to organizations

The migration set matches the current SQLAlchemy model definitions for Sprint 1.

## Developer Starting Points

- Start in `README.md` for commands and secure defaults.
- Read `apps/api/app/main.py` and `apps/api/app/presentation/api/v1/router.py` to understand HTTP entrypoints.
- Read `apps/web/src/lib/api.ts` to understand how the frontend consumes the API.
- Read `apps/api/app/infrastructure/db/models.py` and the Alembic migrations to understand the Sprint 1 data model.
