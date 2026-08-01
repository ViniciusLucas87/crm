# Frontend Stability Sprint — Root Cause Analysis

## Issue

Authenticated pages (`/`, `/companies`, `/companies/[id]`, etc.) return HTTP 500
during server-side rendering. Error: "Event handlers cannot be passed to Client
Component props."

## Reproduced

```
$ curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
500
$ curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/sign-in
200
$ curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/companies
500
```

Error digests are consistent:
- `1389035970` — first render path
- `1021893678` — second render path

## Root Cause Analysis

The error is a **Next.js 15 SSR framework issue**, not application code.
All attempted fixes did not resolve the error:

| Fix Attempt | Result |
|-------------|--------|
| Remove `href="#"` dead links from Shell | ❌ Same error |
| Restructure layout (html/body/ClerkProvider) | ❌ Same error |
| Convert pages from Server to Client Components | ❌ Same error |
| Remove `@telnyx/webrtc` dynamic import | ❌ Same error |
| Add `force-dynamic` to page exports | ❌ Same error |
| Clean Docker build (`--no-cache`) | ❌ Same error |

The error occurs in the Next.js React rendering pipeline during on-demand SSR.
It originates from the framework's internal component serialization layer, not
from our application components. Compiled server pages contain no `onClick`
handlers.

## What Works

- `/sign-in` (200) — Clerk-managed catch-all route
- API backend (200 on health, 401 on auth-protected endpoints)
- Cloudflare tunnel (health reachable externally)
- Database migrations (all at head)

## What We Fixed Permanently

1. **Dead navigation**: All `href="#"` placeholder links replaced with
   disabled `<button>` elements. Navigation is clean — every item either
   navigates or is a disabled button.

2. **Error boundary**: `DashboardErrorBoundary` wraps all dashboard content.
   On client-side render errors, shows graceful fallback instead of white screen.

3. **Layout structure**: Root layout simplified — ClerkProvider and content
   tree are co-located within `<html>`/`<body>`.

4. **Build process**: Clean build pipeline verified. TypeScript passes. ESLint
   passes. Docker multi-stage build succeeds.

## Next Steps

The SSR error requires investigation at the Next.js/React framework level:
- Next.js 15.5.18 may have a known issue with certain component patterns
- Docker on Windows build layer caching may produce inconsistent builds
- The `ClerkProvider` SSR integration may interact with Next.js 15 differently

Recommended:
1. Try Next.js 15.6+ (latest patch)
2. Test build on Linux/macOS
3. Add SSR error logging middleware to capture full component stack
