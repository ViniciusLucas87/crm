# Pacific North Systems — Production Deployment Gap Report
# Generated 2026-08-01 | Sprint: Production Deployment
# Platform: Railway

================================================================================
SECTION 0 — HOSTING PLATFORM
================================================================================

Platform: Railway (railway.app)

Railway provides:
  • Automatic TLS/HTTPS for all services (no Caddy/nginx needed)
  • Internal private networking between services
  • Managed PostgreSQL and Redis (optional)
  • Built-in health checks, logging, and monitoring
  • Custom domain support with automatic DNS
  • Dockerfile-based or docker-compose deployment
  • Volume mounts for persistent storage

Services to deploy on Railway:
  1. marketing  — public website (Next.js, port 3000)
  2. web        — CRM application (Next.js, port 3000)
  3. api        — FastAPI backend (port 8000)
  4. worker     — Celery worker (async processing)
  5. worker-beat — Celery beat scheduler
  6. postgres   — PostgreSQL 16 (managed or containerized)
  7. redis      — Redis 7 (managed or containerized)

Railway-managed services (recommended):
  - PostgreSQL (managed, with backups)
  - Redis (managed)

================================================================================
SECTION 1 — CLASSIFICATION MATRIX (Railway-adjusted)
================================================================================

Legend:
  ✅ READY           — Production-grade, no changes needed
  ⚠️ NEEDS CONFIG    — Works, needs production values
  🔧 DEV ONLY        — Development-only, must change for prod
  ❌ MISSING         — Does not exist, must be created
  🚫 INSECURE        — Security risk in current form
  🛑 BLOCKING        — Cannot deploy without addressing

================================================================================
1.1 INFRASTRUCTURE
================================================================================

| Item | Status | Detail |
|------|--------|--------|
| docker-compose.yml | ⚠️ NEEDS CONFIG | Railway-compatible service definitions |
| API Dockerfile | ✅ READY | Multi-stage, build-time validation, OCI labels |
| Web Dockerfile | ✅ READY | Multi-stage, production build, `npm run start` |
| Worker Dockerfile | ✅ READY | Copies API code, build-time model check, Celery |
| Marketing Dockerfile | ⚠️ NEEDS CONFIG | Create Dockerfile for Railway deployment |
| Reverse proxy | ✅ RAILWAY | Railway handles TLS + routing automatically |
| TLS/HTTPS | ✅ RAILWAY | Automatic Let's Encrypt via Railway |
| Port binding | ✅ RAILWAY | Railway handles internal routing, no host port mapping needed |
| Internal networking | ✅ RAILWAY | Services communicate via Railway private network |
| PostgreSQL port | ✅ READY | Bound to `127.0.0.1` — safe |
| Redis port | ✅ READY | Bound to `127.0.0.1` — safe |
| Worker restart policy | ✅ READY | `restart: unless-stopped` |
| Volumes (postgres_data) | ✅ READY | Named volume, persistent |

================================================================================
1.2 DNS + DOMAINS
================================================================================

| Item | Status | Detail |
|------|--------|--------|
| pacificnorthsystems.com | ⚠️ NEEDS CONFIG | Marketing site needs production deploy |
| www.pacificnorthsystems.com | ⚠️ NEEDS CONFIG | Redirect to apex |
| crm.pacificnorthsystems.com | ❌ MISSING | Subdomain not configured |
| api.pacificnorthsystems.com | ❌ MISSING | Subdomain not configured |
| MX records (Zoho) | ⚠️ NEEDS CONFIG | Must verify production MX intact |
| SPF / DKIM / DMARC | ⚠️ NEEDS CONFIG | Must verify email auth records intact |

================================================================================
1.3 AUTHENTICATION
================================================================================

| Item | Status | Detail |
|------|--------|--------|
| Clerk integration (frontend) | ✅ READY | `clerkMiddleware()` protects all routes |
| Clerk integration (backend) | ✅ READY | JWT validation, RBAC, org isolation |
| Dashboard layout auth check | ✅ READY | `auth()` with redirect to `/sign-in` |
| API BFF proxy auth | ✅ READY | `proxyAuthenticatedApi()` with token forwarding |
| Clerk production keys | 🛑 BLOCKING | Development keys in `.env` — must swap to production |
| Clerk instance | 🛑 BLOCKING | Using `classic-cattle-18.clerk.accounts.dev` — production instance needed |
| Role-based access control | ⚠️ NEEDS CONFIG | RBAC works but `workers.py` has `read:companies` vs `companies:read` |
| Self sign-up enabled | ⚠️ NEEDS CONFIG | Check Clerk dashboard — should be disabled for CRM |
| Admin user | ⚠️ NEEDS CONFIG | Vini Dias needs admin role in production Clerk |

================================================================================
1.4 SECURITY
================================================================================

| Item | Status | Detail |
|------|--------|--------|
| CORS origins | 🛑 BLOCKING | Currently `localhost:3000` only — must add production domains |
| CORS allow_credentials | ✅ READY | True — correct for credentialed requests |
| Secure cookies | ⚠️ NEEDS CONFIG | Clerk handles, but verify `Secure` in production |
| HTTPS redirect | ❌ MISSING | No reverse proxy to enforce HTTPS |
| CSP headers | ❌ MISSING | No Content-Security-Policy configured |
| HSTS headers | ❌ MISSING | No Strict-Transport-Security configured |
| Rate limiting | 🔧 DEV ONLY | In-memory rate limiter only — not distributed |
| Secrets in .env.example | 🚫 INSECURE | Root `.env.example` contains hardcoded Clerk test keys |
| Telnyx debug logs | ⚠️ NEEDS CONFIG | Verify `debug: false` in production WebRTC client |

================================================================================
1.5 DATABASE
================================================================================

| Item | Status | Detail |
|------|--------|--------|
| PostgreSQL 16 | ✅ READY | Alpine image, healthcheck |
| Alembic migrations | ✅ READY | All migrations apply cleanly, head at `20260801_0003` |
| Connection pooling | 🔧 DEV ONLY | SQLAlchemy defaults — may need production pooling |
| Backup | ❌ MISSING | No backup configured |
| Timezone | ✅ READY | `UTC` used throughout |
| Production credentials | 🛑 BLOCKING | `postgres:postgres` — must use strong password |
| Private networking | ✅ READY | Bound to `127.0.0.1` |

================================================================================
1.6 REDIS + CELERY
================================================================================

| Item | Status | Detail |
|------|--------|--------|
| Redis 7 | ✅ READY | Alpine image, healthcheck |
| Celery worker | ✅ READY | 16 registered tasks |
| Celery Beat | ✅ READY | 17 scheduled tasks |
| Queue definitions | ✅ READY | critical, high, normal, low, background |
| Connection retry | ⚠️ NEEDS CONFIG | Deprecation warning — set `broker_connection_retry_on_startup` to True |
| Production credentials | 🛑 BLOCKING | `redis_dev` password — must use strong password |
| Private networking | ✅ READY | Bound to `127.0.0.1` |

================================================================================
1.7 EXTERNAL SERVICES
================================================================================

| Item | Status | Detail |
|------|--------|--------|
| Telnyx (telephony) | ⚠️ NEEDS CONFIG | WebRTC, webhooks, production app/connection IDs |
| Deepgram (transcription) | ⚠️ NEEDS CONFIG | API key, WebSocket endpoint |
| Zoho SMTP (email outbound) | ✅ READY | `smtp.zohocloud.ca:465` working |
| Zoho IMAP (email inbound) | ✅ READY | `imap.zohocloud.ca:993` working |
| AI providers (DeepSeek/OpenAI) | ⚠️ NEEDS CONFIG | DeepSeek key set, OpenAI empty |
| Calendly (booking) | ✅ READY | Booking URLs in emails |
| PDF generation | ⚠️ NEEDS CONFIG | Status tracked, implementation pending |

================================================================================
1.8 ASSESSMENT PIPELINE
================================================================================

| Item | Status | Detail |
|------|--------|--------|
| Public endpoint | ✅ READY | `POST /api/v1/public/automation-assessment` |
| Idempotency | ✅ READY | Key + fingerprint validation, 409 on conflict |
| Health gate | ✅ READY | Advisory check before accepting payload |
| CRM persistence | ✅ READY | Transactional, all-or-nothing |
| Outbox events (6) | ✅ READY | Emails, KG, follow-up |
| Email delivery | ✅ READY | Internal + visitor via Zoho SMTP |
| Knowledge Graph | ✅ READY | 10+ facts written per assessment |
| Internal email filter | ✅ READY | X-PNS headers prevent CRM pollution |
| Marketing proxy | ✅ READY | Policy A: 201 only after CRM commit |

================================================================================
SECTION 2 — BLOCKING ITEMS (Must Fix Before Deploy)
================================================================================

🛑 1. Clerk Production Instance
   - Current: `classic-cattle-18.clerk.accounts.dev` (development)
   - Action: Create production Clerk application, update all keys

🛑 2. CORS Origins
   - Current: `http://localhost:3000`
   - Action: Add `https://crm.pacificnorthsystems.com, https://pacificnorthsystems.com`

🛑 3. Database Password
   - Current: `postgres:postgres`
   - Action: Generate strong password, rotate

🛑 4. Redis Password
   - Current: `redis_dev`
   - Action: Generate strong password, rotate

🛑 5. Reverse Proxy + TLS
   - Current: No reverse proxy, no TLS, ports exposed directly
   - Action: Deploy nginx/Caddy with Let's Encrypt cert for all three domains

🛑 6. DNS Records
   - Current: Only apex domain
   - Action: Add `crm` and `api` subdomain records

🚫 7. Exposed Secrets
   - Current: Clerk test keys in `.env.example`, Telnyx key in `.env`
   - Action: Remove from example files, rotate exposed keys

================================================================================
SECTION 3 — RECOMMENDED HOSTING ARCHITECTURE (Railway)
================================================================================

Platform: Railway

```
Railway Project: pns-crm
  ├── marketing          (Next.js, Dockerfile, port 3000)
  │   → https://pacificnorthsystems.com
  ├── web                (Next.js CRM, Dockerfile, port 3000)
  │   → https://crm.pacificnorthsystems.com
  ├── api                (FastAPI, Dockerfile, port 8000)
  │   → https://api.pacificnorthsystems.com
  ├── worker             (Celery worker, Dockerfile)
  ├── worker-beat        (Celery beat, Dockerfile)
  ├── postgres           (Railway managed PostgreSQL 16)
  └── redis              (Railway managed Redis 7)
```

Railway benefits:
  • Automatic TLS/HTTPS for every service with custom domain
  • Internal private networking — services talk via railway internal DNS
  • Built-in health checks, logs, and metrics
  • PostgreSQL: managed backups, automatic minor updates
  • Redis: managed, persistent
  • No reverse proxy to configure — Railway IS the reverse proxy
  • Deploy via `railway up` or GitHub integration
  • Environment variables managed in Railway dashboard

Cost estimate (Railway):
  • Marketing (0.5 vCPU / 512MB): ~$8/mo
  • CRM Web (0.5 vCPU / 512MB): ~$8/mo
  • API (1 vCPU / 1GB): ~$20/mo
  • Worker + Beat (shared 0.5 vCPU / 512MB): ~$8/mo
  • PostgreSQL (1GB): ~$10/mo
  • Redis (256MB): ~$3/mo
  • Total: ~$57/mo

================================================================================
SECTION 4 — RAILWAY SETUP (replaces Caddy)
================================================================================

Railway handles TLS automatically — no Caddyfile or nginx config needed.

1. Create Railway account at railway.app
2. Create new project: "pns-crm"
3. Add services via Dockerfiles:
   - Marketing: apps/marketing/Dockerfile
   - CRM Web: apps/web/Dockerfile
   - API: apps/api/Dockerfile
   - Worker: apps/worker/Dockerfile
   - Worker-Beat: apps/worker/Dockerfile (with beat CMD)
4. Add Railway managed PostgreSQL and Redis
5. Configure custom domains per service
6. Set environment variables in Railway dashboard
7. Deploy via GitHub integration or `railway up`

================================================================================
SECTION 5 — NEXT STEPS
================================================================================

1. Provision production server or managed services
2. Configure DNS (crm, api subdomains)
3. Deploy reverse proxy with TLS
4. Create production Clerk application
5. Update ALL environment variables to production values
6. Rotate all exposed secrets
7. Run alembic upgrade head on production database
8. Deploy containers
9. Run E2E acceptance test
10. Enable backups
11. Monitor for 24h
