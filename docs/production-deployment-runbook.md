# Pacific North Systems — Production Deployment Runbook
# Version 2.0 | 2026-08-01 | Platform: Railway

================================================================================
ARCHITECTURE OVERVIEW
================================================================================

```
Internet
  │
  ├─ pacificnorthsystems.com ──→ Railway: marketing (Next.js, port 3000)
  ├─ crm.pacificnorthsystems.com ──→ Railway: web (Next.js CRM, port 3000)
  ├─ api.pacificnorthsystems.com ──→ Railway: api (FastAPI, port 8000)
  │
  └─ Railway internal network ───────────────────────────────────────────┐
      │                                                                   │
      ├─ api ──→ postgres (managed, private)                             │
      ├─ api ──→ redis (managed, private)                                │
      ├─ worker ──→ postgres + redis                                     │
      ├─ worker-beat ──→ redis                                           │
      │                                                                   │
      └─ External Services ──────────────────────────────────────────────┘
          Clerk (auth)    Telnyx (calls)   Deepgram (transcription)
          Zoho (email)    DeepSeek (AI)    Calendly (booking)
```

Railway handles:
  • TLS/HTTPS termination for all services automatically
  • Internal DNS between services (e.g. api resolves to API container)
  • Custom domain routing per service
  • Health checks and auto-restart
  • Log aggregation
  • PostgreSQL backups (managed)

================================================================================
PREREQUISITES
================================================================================

1. Railway account at railway.app
2. Domain: pacificnorthsystems.com with DNS access
3. Clerk production account with application created
4. Telnyx, Deepgram, DeepSeek production accounts
5. Zoho Mail (already configured)
6. GitHub repository connected to Railway (or `railway up` CLI)

================================================================================
PHASE 1: RAILWAY PROJECT SETUP
================================================================================

1. Login to railway.app
2. Create new project: "pns-crm"
3. Add services (one per app):

   a) PostgreSQL (managed):
      - Add service → Database → PostgreSQL
      - Railway provides DATABASE_URL and connection details automatically
   
   b) Redis (managed):
      - Add service → Database → Redis
      - Railway provides REDIS_URL automatically
   
   c) API (FastAPI):
      - Add service → GitHub Repo → select repo
      - Root directory: apps/api
      - Railway auto-detects Dockerfile
      - Set PORT=8000 in variables
   
   d) CRM Web (Next.js):
      - Add service → GitHub Repo → select repo
      - Root directory: apps/web
      - Set PORT=3000
   
   e) Marketing (Next.js):
      - Add service → GitHub Repo → select repo
      - Root directory: apps/marketing
      - Set PORT=3000
   
   f) Worker (Celery):
      - Add service → GitHub Repo → select repo
      - Root directory: apps/worker
      - Custom start command: celery -A worker_tasks.celery_app worker --loglevel=INFO --concurrency=4
   
   g) Worker-Beat (Celery Beat):
      - Add service → GitHub Repo → select repo
      - Root directory: apps/worker
      - Custom start command: celery -A worker_tasks.celery_app beat --loglevel=INFO

4. Configure custom domains per service:
   - marketing → pacificnorthsystems.com, www.pacificnorthsystems.com
   - web → crm.pacificnorthsystems.com
   - api → api.pacificnorthsystems.com

================================================================================
PHASE 2: DNS CONFIGURATION
================================================================================

At your DNS provider, add CNAME records:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| CNAME | crm | <railway-provided-domain> | 300 |
| CNAME | api | <railway-provided-domain> | 300 |
| CNAME | www | <railway-marketing-domain> | 300 |

For the apex domain (pacificnorthsystems.com), use:
- ANANE/ALIAS record if supported → Railway marketing service domain
- Or CNAME flattening (Cloudflare, DNSimple)

**DO NOT CHANGE:**
- MX records (Zoho Mail)
- SPF TXT record
- DKIM records
- DMARC record

Verify DNS propagation:
```bash
dig crm.pacificnorthsystems.com CNAME +short
dig api.pacificnorthsystems.com CNAME +short
```

================================================================================
PHASE 3: ENVIRONMENT VARIABLES (Railway Dashboard)
================================================================================

Set these in Railway dashboard → each service → Variables.

SHARED (all services):
```bash
PNS_ENV=production
```

API service:
```bash
# Railway provides DATABASE_URL automatically for managed Postgres
# Railway provides REDIS_URL automatically for managed Redis
API_HOST=0.0.0.0
API_PORT=8000
ALLOWED_ORIGINS=https://pacificnorthsystems.com,https://www.pacificnorthsystems.com,https://crm.pacificnorthsystems.com
CLERK_ISSUER=https://<production-clerk-domain>
CLERK_JWKS_URL=https://<production-clerk-domain>/.well-known/jwks.json
DEEPSEEK_API_KEY=<production-key>
TELEPHONY_PROVIDER=telnyx
TELNYX_API_KEY=<production-key>
TELNYX_APPLICATION_ID=<production-app-id>
TELNYX_PHONE_NUMBER=+16042251745
TELNYX_PUBLIC_URL=https://api.pacificnorthsystems.com
DEEPGRAM_API_KEY=<production-key>
TRANSCRIPTION_PROVIDER=deepgram
SMTP_HOST=smtp.zohocloud.ca
SMTP_PORT=465
SMTP_USER=vinidias@pacificnorthsystems.com
SMTP_PASS=<new-app-password>
SMTP_FROM_EMAIL=hello@pacificnorthsystems.com
SMTP_FROM_NAME=Pacific North Systems
INTERNAL_NOTIFICATION_EMAIL=hello@pacificnorthsystems.com
IMAP_HOST=imap.zohocloud.ca
IMAP_PORT=993
ENABLE_TELEPHONY=true
ENABLE_WEBRTC=true
```

CRM Web + Marketing:
```bash
# Web
NEXT_PUBLIC_API_BASE_URL=https://api.pacificnorthsystems.com
NEXT_PUBLIC_APP_URL=https://crm.pacificnorthsystems.com
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...

# Marketing
CRM_API_BASE_URL=https://api.pacificnorthsystems.com
NEXT_PUBLIC_SITE_URL=https://pacificnorthsystems.com
```

Worker + Worker-Beat:
```bash
# Railway provides DATABASE_URL and REDIS_URL automatically
SMTP_HOST=smtp.zohocloud.ca
SMTP_PORT=465
SMTP_USER=vinidias@pacificnorthsystems.com
SMTP_PASS=<same-app-password>
SMTP_FROM_EMAIL=hello@pacificnorthsystems.com
SMTP_FROM_NAME=Pacific North Systems
INTERNAL_NOTIFICATION_EMAIL=hello@pacificnorthsystems.com
IMAP_HOST=imap.zohocloud.ca
IMAP_PORT=993
```

================================================================================
PHASE 4: CLERK PRODUCTION SETUP
================================================================================

1. Go to https://dashboard.clerk.com
2. Create new Production application "PNS CRM"
3. Configure:
   - Domain: crm.pacificnorthsystems.com
   - Sign-in URL: https://crm.pacificnorthsystems.com/sign-in
   - After sign-in: https://crm.pacificnorthsystems.com
   - Allowed origins: https://crm.pacificnorthsystems.com, https://pacificnorthsystems.com
4. Disable public sign-up
5. Create admin user: vinidias@pacificnorthsystems.com
6. Copy production keys → Railway environment variables

================================================================================
PHASE 5: SECRET ROTATION
================================================================================

Rotate all previously-exposed credentials:
1. Clerk keys → production keys from Phase 4
2. Database password → Railway managed (auto-generated)
3. Redis password → Railway managed (auto-generated)
4. Zoho app password → new in Zoho Accounts
5. Telnyx API key → new in Telnyx Portal
6. Deepgram API key → new in Deepgram Console  
7. DeepSeek API key → new in DeepSeek Platform

================================================================================
PHASE 6: MARKETING DOCKERFILE
================================================================================

Create `apps/marketing/Dockerfile` for Railway deployment:

```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY apps/marketing/package.json apps/marketing/package-lock.json* ./
RUN npm ci --omit=dev --no-audit

FROM node:20-alpine AS builder
WORKDIR /app
COPY apps/marketing .
COPY --from=deps /app/node_modules ./node_modules
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json .
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["npm", "run", "start"]
```

================================================================================
PHASE 7: DATABASE MIGRATION
================================================================================

Railway provides a shell to the API service. Run:

```bash
# Via Railway CLI:
railway run --service api alembic upgrade head
railway run --service api alembic current
# Expected: 20260801_0003 (head)
```

================================================================================
PHASE 8: DEPLOY
================================================================================

Railway deploys automatically on Git push (if connected).
Or manually:
```bash
railway up
```

================================================================================
PHASE 9: ACCEPTANCE TESTS
================================================================================

Same test suite as before — run from incognito browser:

1. https://crm.pacificnorthsystems.com → redirect to Clerk login
2. https://crm.pacificnorthsystems.com/companies → redirect to login  
3. Sign in → CRM loads
4. Submit assessment from https://pacificnorthsystems.com
5. Verify CRM records, emails, KG facts

================================================================================
PHASE 10: BACKUPS
================================================================================

Railway managed PostgreSQL includes:
- Automatic daily backups (7-day retention on Hobby plan)
- Point-in-time recovery (on Pro plan)
- Manual backup available via Railway dashboard

Additional: periodic pg_dump export to external storage (optional).

================================================================================
PHASE 11: ROLLBACK
================================================================================

Railway rollback:
1. Go to Railway dashboard → service → Deployments
2. Click "Rollback" on the previous working deployment
3. If database issue: restore from Railway backup

DNS rollback:
1. Update CNAME records to previous Railway service domain or maintenance page

================================================================================
PHASE 12: MONITORING
================================================================================

Railway provides:
- Per-service logs (dashboard → service → Deployments → View Logs)
- CPU, memory, network metrics
- Health check status
- Alerting on service failure

Key URLs to monitor:
- https://api.pacificnorthsystems.com/api/v1/health
- https://crm.pacificnorthsystems.com
