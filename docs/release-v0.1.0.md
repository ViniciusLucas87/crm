# Release Notes: v0.1.0

## New Features

- Dashboard summary page backed by PostgreSQL KPI aggregation
- Companies workflow with create, read, update, archive, restore, duplicate, search, sort, filter, and pagination
- Auth context endpoint and permission-protected API routes
- Docker Compose stack for web, API, worker, PostgreSQL, and Redis
- GitHub Actions CI for frontend, backend, and Docker build verification

## Architecture

- Next.js frontend calling FastAPI over HTTP
- FastAPI clean-architecture layout with service and repository boundaries
- SQLAlchemy persistence with Alembic-managed PostgreSQL schema
- Redis-backed worker container for future asynchronous workloads

## Breaking Changes

- Dashboard KPI contract now uses `companies`, `activeOpportunities`, and `wonDeals`
- Protected API routes no longer allow silent development access by default

## Known Limitations

- Live end-to-end sign-in verification depends on provisioning real Clerk credentials in runtime environments

## Future Roadmap

- Add contacts, opportunities management, and richer dashboard drilldowns
- Expand automated tests beyond the current smoke and API coverage

## Release Candidate Review Summary

- Frontend validation passed locally: install, lint, typecheck, tests, and build
- Backend validation passed locally: Ruff, Black, Pytest, Alembic, and API startup
- Docker validation passed for service startup and endpoint reachability
- JavaScript production dependency audit passed after upgrading Next.js, Clerk, React, and PostCSS resolution
- Companies persistence and dashboard company-count reactivity were verified against PostgreSQL
- Remaining release blockers are documented in the final review report rather than hidden in code