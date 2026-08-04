# PNS CRM Operations and Release Runbook

## Deploy Order

1. **Database migration:** run `alembic upgrade head` on the production database using the Railway CLI or dashboard shell.
2. **API:** deploy it and confirm `/api/v1/health/ready` returns `ready`.
3. **Worker:** deploy the worker and worker beat services, then confirm `/api/v1/operations/status` reports at least one healthy worker.
4. **Web:** deploy Next.js, confirm `/` returns 200, and confirm Clerk authentication works.
5. **Acceptance:** run `scripts/acceptance.sh`. Set `ALLOW_PRODUCTION_WRITES=true` only for the controlled write test.

## Rollback

1. In Railway Dashboard, open the service, choose Deployments, select the previous deployment, and choose Rollback.
2. If DB migration was destructive: restore from latest verified backup using `scripts/restore-drill.sh`
3. Verify `/api/v1/health/ready` returns `ready`
4. Re-run acceptance suite

## Backup Verification

- Daily: check S3/R2 `backups/.last_backup` marker timestamp is within 26 hours (via `/api/v1/operations/status` `backup_last_ts` field)
- Weekly: run `scripts/restore-drill.sh` against staging
- Monthly: full restore drill + row count comparison against production

## Monitoring

| Check | Endpoint | Expected |
|---|---|---|
| Liveness | `GET /api/v1/health/live` | `{"status":"alive"}` |
| Readiness | `GET /api/v1/health/ready` | `{"status":"ready"}` |
| Status | `GET /api/v1/operations/status` (authenticated) | `{"status":"healthy"}` |
| Worker heartbeat | `GET /api/v1/workers/health` | `worker_healthy >= 1` |
| Outbox backlog | Status page | `outbox_failed < 100` |
| Backup freshness | Status page | `backups_ok: true` |

## Alert Thresholds

| Alert | Threshold | Severity | Response |
|---|---|---|---|
| API down | `/health/live` 5xx for 2 min | Critical | Check Railway logs, restart API |
| DB disconnected | `db_status: disconnected` | Critical | Check DB service, connection string |
| Redis disconnected | `redis_status: disconnected` | High | Check Redis service, restart worker |
| Worker stale | `worker_healthy == 0` for 10 min | High | Check Celery broker, restart worker |
| Outbox backlog | `outbox_pending > 500` | Medium | Check worker processing, scale up |
| Outbox failures | `outbox_failed > 50` | High | Check error logs, clear dead letters |
| Backup stale | `backups_ok: false` for 2 days | High | Check backup cron, disk space |
| 5xx rate | > 5% of requests for 5 min | Critical | Check logs, rollback last deploy |
| API latency | p95 > 2000ms for 5 min | Medium | Check DB queries, scale API |
| DB capacity | < 20% free disk | High | Vacuum, increase volume |
| AI spend | Daily cost exceeds budget | High | Reduce enrichment, check circuit breaker |

## Acceptance Checklist

- [ ] Auth: login, logout, protected routes
- [ ] Tenant isolation: org 1 cannot see org 2 data
- [ ] Assessment intake: submit, confirm the lead was created, and confirm the email was delivered
- [ ] Missed call: receive webhook, create recovery task, and send SMS in test mode
- [ ] Today: overdue, due, upcoming, leads with no action, follow-up/replay
- [ ] Audit: entries visible, no cross-tenant leaks
- [ ] Backups: last backup within 24h
- [ ] Docs: `/docs` returns 404 in production
- [ ] Health: all probes green
- [ ] Cleanup: uniquely tagged test data removed
