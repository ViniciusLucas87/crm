# Pacific North Systems — Deployment Guide

## Architecture

```
pacificnorthsystems.com / .ca
          │
     CanSpace DNS
          │
    ┌─────┴─────┐
    │            │
  Vercel      Railway
 (Next.js)   (FastAPI)
    │            │
    └─────┬──────┘
          │
    Railway PostgreSQL
```

| Layer | Platform | Technology |
|---|---|---|
| Frontend | Vercel | Next.js 15 (App Router) |
| Backend | Railway | FastAPI (future) |
| Database | Railway | PostgreSQL (future) |
| DNS | CanSpace | Domain registrar only |
| Email | Zoho Cloud | MX records at CanSpace |

---

## Repository

```
GitHub: (to be created)
Branch strategy: main → production
```

---

## Environment Variables

### Vercel (Production) — REQUIRED

| Variable | Value | Notes |
|---|---|---|
| `CRM_API_BASE_URL` | `https://pns-crm.up.railway.app` | **Mandatory in production.** Build will reject deployment if missing. |
| `NEXT_PUBLIC_SITE_URL` | `https://pacificnorthsystems.com` | Canonical URL for sitemap, OG metadata |

**If `CRM_API_BASE_URL` is not set in production**, the Next.js build throws a fatal error and the assessment endpoint returns `status: "pending"` instead of false success. No lead is lost — the client preserves the full payload and can retry.

### Railway (Future)

| Variable | Value |
|---|---|
| `DATABASE_URL` | Railway PostgreSQL connection string |
| `CORS_ORIGINS` | `https://pacificnorthsystems.com` |
| `ENVIRONMENT` | `production` |

---

## Assessment Lead-Capture Flow

### 1. Visitor submits assessment

```
Browser (client-side)
  │
  │  POST /api/assessment-submit
  │  { contactName, contactEmail, contactCompany, ..., results }
  │
  ▼
Next.js API Route (Vercel serverless)
  │
  │  Generates unique requestId: pns_<timestamp>_<random>
  │  Builds CRM payload with X-Idempotency-Key
  │
  ├─ CRM_API_BASE_URL configured?
  │   │
  │   ├─ YES → POST to {CRM}/api/v1/public/automation-assessment
  │   │         │
  │   │         ├─ 200 → return { status: "received", requestId, crmId }
  │   │         │         CRM creates: Company, Contact, Lead, Assessment,
  │   │         │         Activity, follow-up Task
  │   │         │
  │   │         └─ Error/Timeout → return { status: "pending", requestId } (202)
  │   │                            Client can retry via PUT with same requestId
  │   │
  │   └─ NO  → return { status: "pending", requestId }
  │             (Development only; production rejects at build time)
  │
  └─ Response to browser
       │
       ├─ status: "received" → green banner, "We'll follow up within 1 business day"
       └─ status: "pending"  → yellow banner, "Processing delayed — your data is safe"
                                Retry button available
```

### 2. Where is the lead persisted?

| Stage | Persistence |
|---|---|
| Before submit | Browser sessionStorage (assessment progress, intermediate steps) |
| After submit | Client holds full payload + requestId in React state |
| CRM received | CRM database (PostgreSQL on Railway) |
| CRM pending | Client React state + requestId; retry via PUT |

**No lead is ever lost.** The client preserves the complete submission until the CRM confirms receipt.

### 3. CRM_API_BASE_URL behavior

| Environment | CRM_API_BASE_URL | Behavior |
|---|---|---|
| Local dev | Not set | Returns `pending`; build succeeds, assessment shows "CRM not configured" |
| Local dev | Set to localhost | Forwards to local CRM; works normally |
| Vercel preview | Set | Forwards to CRM; `VERCEL_ENV !== "production"` → no fatal build error |
| **Vercel production** | **Not set** | **Build throws fatal error** — deployment is blocked |
| **Vercel production** | **Set** | Forwards to CRM; if CRM unreachable → returns `pending` (202) with retry |

### 4. CRM unreachable / unavailable

1. API returns `202 Accepted` with `{ status: "pending", requestId, message }`
2. Client shows yellow banner: "Processing delayed — your data is safe"
3. Retry button calls `PUT /api/assessment-submit` with same `requestId`
4. `X-Idempotency-Key: {requestId}` ensures CRM doesn't create duplicate leads
5. Full submission payload is preserved in client state

### 5. Email flow (Zoho)

```
CRM (Railway/FastAPI)
  │
  │  On assessment received:
  │
  ├─→ Internal notification: hello@pacificnorthsystems.com
  │     │
  │     └─ Zoho forwards → vinidias@pacificnorthsystems.com
  │
  └─→ Visitor confirmation: {visitor email}
        Includes: results summary, next steps, PDF (future)

Marketing website does NOT send email directly.
All email is owned by the CRM backend via Zoho SMTP/API.
```

### 6. Duplicate prevention

| Mechanism | How |
|---|---|
| `X-Idempotency-Key` | CRM checks `request_id` before creating Lead; duplicate POSTs return existing record |
| Client retry | Uses `PUT` with same `requestId`; CRM idempotency handles duplicates |
| Session storage | Assessment progress saved per-session; cleared on reset |

### 7. End-to-end test (CRM available)

```
1. Complete assessment (all 6 steps)
2. Submit → POST /api/assessment-submit
3. Expect: 200 { status: "received", requestId: "pns_...", crmId: "..." }
4. CRM verifications:
   ✓ Company created or matched by name
   ✓ Contact created or matched by email
   ✓ Lead created with assessment data
   ✓ Assessment stored with answers + results
   ✓ Activity logged ("Assessment submitted")
   ✓ Follow-up Task created (due: +1 business day)
   ✓ Internal email sent to hello@ → vinidias@
   ✓ Visitor confirmation email sent
5. Retry with same requestId:
   ✓ CRM returns existing record (no duplicate)
```

### 8. End-to-end test (CRM unavailable)

```
1. Complete assessment
2. Submit → POST /api/assessment-submit
3. Expect: 202 { status: "pending", requestId: "pns_..." }
4. Client shows yellow banner with Retry button
5. Full submission data preserved in React state
6. Click Retry → PUT /api/assessment-submit
7. If CRM still down → 202 again (no data loss)
8. When CRM recovers → 200 { status: "received" }
```
|---|---|
| `DATABASE_URL` | Railway PostgreSQL connection string |
| `CORS_ORIGINS` | `https://pacificnorthsystems.com` |
| `ENVIRONMENT` | `production` |

---

## DNS Configuration

Do NOT modify until deployment is verified on Vercel preview URL.

### Current DNS (CanSpace)

| Record | Type | Value |
|---|---|---|
| `@` | A | `31.43.161.6` (→ change to Vercel) |
| `@` | A | `31.43.160.6` (→ change to Vercel) |
| `www` | CNAME | `sites.framer.app.` (→ change to Vercel) |
| `@` | MX | Zoho Cloud (keep) |

### Target DNS (for Vercel)

| Record | Type | Value |
|---|---|---|
| `@` | A | `76.76.21.21` |
| `www` | CNAME | `cname.vercel-dns.com` |

1. Add both domains in Vercel: `pacificnorthsystems.com` + `pacificnorthsystems.ca`
2. Vercel will issue auto-renewing SSL certificates
3. Set `pacificnorthsystems.com` as primary, redirect `.ca` → `.com`

---

## Deployment Steps

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Production-ready marketing site"
git remote add origin <repo-url>
git push -u origin main
```

### 2. Import to Vercel
1. Go to https://vercel.com/import
2. Connect GitHub repo
3. Framework: Next.js (auto-detected)
4. Root directory: `apps/marketing`
5. Build command: `pnpm build` (or `cd ../.. && pnpm --filter @pns/marketing build`)
6. Output directory: `.next`
7. Add environment variables from table above

### 3. Configure Domains in Vercel
1. Project Settings → Domains
2. Add `pacificnorthsystems.com`
3. Add `pacificnorthsystems.ca` (redirect to .com)
4. Add `www.pacificnorthsystems.com` (redirect to apex)

### 4. Update DNS at CanSpace
1. Log into CanSpace → My Domains → pacificnorthsystems.com → Manage DNS Records
2. Delete existing A records (`31.43.161.6`, `31.43.160.6`)
3. Add A record: `@` → `76.76.21.21`
4. Change www CNAME: `www` → `cname.vercel-dns.com`
5. Keep MX records for Zoho email
6. Repeat for pacificnorthsystems.ca (or set up domain forwarding)

### 5. Verify
- [ ] https://pacificnorthsystems.com loads the new site
- [ ] https://www.pacificnorthsystems.com redirects to apex
- [ ] https://pacificnorthsystems.ca redirects to .com
- [ ] SSL certificate is active (Vercel auto-provisions)
- [ ] All pages render correctly
- [ ] Assessment form submits successfully
- [ ] Blog articles load
- [ ] robots.txt accessible at /robots.txt
- [ ] sitemap.xml accessible at /sitemap.xml

---

## Rollback Procedure

1. In CanSpace DNS: revert A records to `31.43.161.6` and `31.43.160.6`
2. Or in Vercel: promote previous deployment from Deployments tab
3. DNS propagation: up to 1 hour

---

## Post-Deployment Verification

- [ ] Homepage loads with all sections
- [ ] Assessment: complete full flow, verify submission succeeds
- [ ] Blog: index page, both articles render
- [ ] Solutions: all sections present
- [ ] Privacy & Terms pages accessible
- [ ] 404 page is branded
- [ ] All CTAs link correctly
- [ ] Calendly links open in new tab
- [ ] Mobile responsive (test at 375px, 768px, 1024px)
- [ ] Lighthouse: Performance ≥ 90, Accessibility ≥ 95, SEO = 100
- [ ] No console errors
- [ ] No broken images
- [ ] Forms validate correctly
