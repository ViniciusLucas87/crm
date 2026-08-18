# PNS App Factory Foundation

Date: 2026-08-18

## Decision

The App Factory is a product research and validation system. It is not an automatic app publishing machine. Production releases, spending increases, marketplace declarations, identity checks and legal attestations always require the account owner.

The first portfolio contains twenty ranked problems. Never Forget is the strongest current candidate, but it is approved only for a purchase intent experiment. No new product has passed the development gate yet.

## Reusable system map

| Capability | Current PNS component | Factory use |
| --- | --- | --- |
| Authentication | Clerk organizations and permissions | Protect the internal dashboard and separate organizations |
| Payments | Stripe subscriptions, webhooks and customer portal | Reuse only after a product passes validation |
| Telephone and SMS | Telnyx call control, messages, suppression and audit records | Use through narrow product credentials and explicit cost limits |
| Email | Resend and transactional outbox | Opt in validation messages and receipts |
| Application data | PostgreSQL and organization scoped queries | Separate factory research, evidence and experiment tables |
| Background work | Redis, Celery and transactional outbox | Scheduled research and notifications when justified |
| Storage and recovery | Cloudflare R2 backup process | Product specific backup policies after data classification |
| Operations | Health page, audit logs, telemetry and cost controls | Release evidence and emergency shutdown signals |
| Distribution | PNS website, CRM discovery and customer relationships | Ethical landing page experiments and partner referrals |
| Customer service | Conversation and email timelines | Product feedback only after consent and product separation |

## Readiness audit

### Production ready for reuse

Authentication, organization isolation, PostgreSQL, Stripe billing foundations, Telnyx messaging foundations, Resend delivery, transactional outbox, monitoring, audit logs, backup tooling and AI spending limits are implemented in the shared platform.

### Controlled or incomplete

Browser based incoming call answering still requires a controlled live acceptance test. Some older architecture notes describe features that were later completed, so this document and the current cycle status are the source of truth. Experimental products do not receive production administrator credentials.

### Risks

1. A research idea could accidentally be treated as approved product scope.
2. Shared credentials could allow an experiment to affect production customers.
3. Weak evidence could create unnecessary development and support costs.
4. Automated outreach could violate platform rules or damage trust.
5. AI and communication costs could grow without a product level budget.

The new API prevents product build eligibility from being inferred from score alone. It requires evidence and still reports every candidate as not eligible to build until measured demand and the remaining release gates are recorded.

## Shared architecture plan

The factory has three isolated records:

1. Candidate stores the problem, audience, workaround, price hypothesis, distribution thesis, score and decision.
2. Evidence stores dated source links and the observed signal.
3. Experiment stores the hypothesis, channel, success measure, cost ceiling and results.

All records are scoped to the authenticated organization. Factory routes use the same Clerk permission layer as the CRM. Experiments cannot access Stripe, Telnyx, Clerk or Cloudflare administration.

## Product starters

When validation supports development, use the cheapest useful format.

1. Website tool or PWA: Next.js, offline cache only when useful, optional authentication, export and deletion controls.
2. Android: Kotlin, Jetpack Compose, Room, WorkManager and encrypted storage. Start Android only when device capabilities or Play discovery add meaningful value.
3. Service product: existing FastAPI, PostgreSQL and transactional outbox, with a separate product entitlement and spending policy.
4. Marketing page: plain problem statement, real demonstration, proposed price, privacy summary, evidence based claims and one measurable intent action.

## Validation gate

A candidate needs at least three independent sources, a repeated workaround, evidence of time or money spent, a realistic distribution channel and a score of at least 75 before an experiment can be created. Validation should measure qualified intent, not clicks alone.

Never Forget should be tested with a small opt in page and direct conversations with contractors. The first success threshold should be five qualified pilot requests or two paid pilot commitments from fifty relevant visitors. The experiment should stop at CAD 100 spend or at the first complaint, whichever occurs first.

## Financial and safety defaults

1. Research has no paid API dependency by default.
2. Initial marketing experiment ceiling is CAD 100 unless the owner approves more.
3. No automatic private messages.
4. No production deployment from an experiment.
5. No product can read CRM or Never Miss customer data by default.
6. Every later product requires cancellation, deletion, monitoring, rollback and cost limits.
7. High risk medical, legal, financial and fraud protection ideas remain research only.

## Next evidence work

Never Forget and Phone First Family Reminders currently meet the three source minimum. The other eighteen candidates remain explicitly incomplete. The next cycle should deepen evidence for the top five, run an independent critic review, then launch only the strongest ethical purchase intent experiment.
