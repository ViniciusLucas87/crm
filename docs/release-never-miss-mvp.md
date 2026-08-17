# Never Miss MVP

Date: 2026-08-17

## Packages

### Never Miss · CAD $19.99/month

The existing Telnyx missed call recovery workflow is now configurable by organization. The MVP supports:

1. Product enablement and plan selection
2. Business and notification phone settings
3. Customer-specific recovery messages
4. Monthly call and message limits
5. Missed call, automatic reply, and callback metrics
6. Automatic creation of a customer inquiry from a missed call
7. Existing spam screening, STOP handling, event reconciliation, and SMS idempotency

### Never Miss Plus · CAD $59/month

The MVP provides:

1. A normalized inquiry record
2. Website, form, assessment, phone, SMS, referral, and manual sources
3. Protected public intake using a rotatable key stored only as a SHA-256 hash
4. Duplicate-safe external IDs
5. Organization-level data isolation
6. New, contacted, qualified, booked, won, lost, and archived stages
7. Priority, owner, and next-action fields
8. A unified CRM inbox

## User interfaces

1. CRM workspace at `/products` with a Never Miss navigation label
2. Canonical website product page at `/never-miss`
3. Never Miss link in the public website navigation
4. Never Miss link in the CRM Command Center

## Database migration

Apply migration `20260817_products_mvp` before starting the updated API or worker.

```bash
cd apps/api
alembic upgrade head
```

## Pilot activation

1. Open the CRM Never Miss workspace
2. Enter the customer's business name and assigned Telnyx number
3. Enter the notification number
4. Review the recovery message
5. Enable Never Miss
6. Save the configuration
7. Complete one answered and one unanswered acceptance call
8. Confirm the automatic message, callback task, and customer inquiry record
9. Generate a Never Miss Plus intake key only when connecting an external form
10. Store the key in the source system's secret manager

## Validation completed

1. API packaged-product tests pass
2. Existing Phase 1 intake tests pass
3. API lint passes for the new product modules
4. CRM TypeScript check and production build pass
5. Marketing TypeScript check, 35 tests, and production build pass
6. Alembic reports a single migration head

## Known acceptance dependencies

1. The worker integration suite requires the repository's PostgreSQL test service. Docker Desktop was not running during local validation.
2. The browser authorization suite requires live local web and API services. Its failures without those services are environmental rather than assertion failures.
3. Production deployment requires migration execution and a real Telnyx acceptance call.
4. The current assisted-pilot model is operated by PNS. Customer self-service authentication and billing are intentionally deferred until commercial validation.

## Release boundary

This is a working assisted-pilot MVP, not a self-service SaaS release. Do not add AI voice, a mobile app, broad integrations, or automated billing until five paying customers validate recurring demand.
