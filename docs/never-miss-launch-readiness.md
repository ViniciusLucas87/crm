# Never Miss launch readiness

Last reviewed: 2026-08-20 (America/Vancouver)

## What is now wired in the product

- A Stripe Payment Link can start the Never Miss or Never Miss Plus 30-day trial.
- The signed Stripe webhook creates a durable customer subscription record and activation token.
- Trial, active, past-due, cancellation-at-period-end, and cancellation states are recorded from Stripe subscription events.
- Customers can activate their own routing number, update recovery settings, pause replies, complete a real missed-call recovery test, and open a customer-specific Stripe Billing Portal session.
- A cancellation disables automatic replies after Stripe confirms the cancellation and sends forwarding-removal instructions.
- The customer page shows trial end, scheduled cancellation, usage, and the end-to-end recovery-test status.
- Docker services restart unless stopped. The local stack now includes PostgreSQL, Redis, API, web, worker, and scheduler health checks. A Windows sign-in entry starts the local stack, and an hourly Codex uptime monitor checks it.

## Required before accepting the first paid customer

### Stripe

- Create one live subscription Payment Link for each plan using CAD prices: Never Miss at $39/month and Never Miss Plus at $89/month.
- Configure both links to collect a card, apply a 30-day free trial, and redirect to `https://www.pacificnorthsystems.com/never-miss/activate?session_id={CHECKOUT_SESSION_ID}`.
- Enable the customer portal for payment-method changes, invoices, cancellation, and cancellation at period end.
- Add the live `STRIPE_SECRET_KEY`, webhook signing secret, and both Payment Link IDs to the production API environment. Add the two Payment Link URLs to the marketing environment as `NEVER_MISS_FREE_TRIAL_URL` and `NEVER_MISS_PLUS_FREE_TRIAL_URL`.
- Subscribe the production webhook endpoint to checkout completion, subscription create/update/delete, invoice paid, and invoice payment failed. Use `https://api.pacificnorthsystems.com/api/v1/subscriptions/stripe/webhook`.
- Perform a Stripe test-mode trial, cancel-before-trial-end test, paid-renewal test, failed-payment test, and Billing Portal cancellation-at-period-end test. Do not use a real customer until all five are recorded.

### Telnyx and customer delivery

- Confirm that the production Call Control application and messaging profile are assigned to every provisioned Canadian number.
- Set `TELNYX_AUTO_PROVISION_ENABLED=true` only after a production number-order sandbox test has confirmed the correct application and messaging profile.
- Confirm the public Telnyx webhook URL, webhook signature verification, and any SMS compliance requirements for the customer’s message and opt-out handling.
- Configure `TELNYX_WEBHOOK_PUBLIC_KEY` from Telnyx Mission Control. The API verifies the `telnyx-signature-ed25519` and `telnyx-timestamp` headers against the exact raw request body and rejects stale or unsigned webhooks. Do not use a legacy shared webhook secret for this endpoint.
- For every customer, complete the actual unanswered-call test after carrier forwarding is configured: missed call detected, recovery SMS received, customer response received, callback task visible, and customer confirmation recorded.
- Test forwarding behaviour with the customer’s carrier because unanswered-call forwarding and voicemail behaviour differs by plan.

### Hosting, operations, and support

- Deploy the reviewed API and marketing changes together with the database migration `20260820_nm_trial_lifecycle`.
- Use a production host for the API, worker, scheduler, PostgreSQL, Redis, backups, and monitoring. A local Docker Desktop install restarts after this Windows user signs in, but it is not a substitute for hosted 24-hour production availability when the PC is offline.
- Configure encrypted, tested database backups and a restore exercise. Confirm backup retention and an owner for on-call alerts.
- Add uptime checks for the public API health endpoint, readiness endpoint, Never Miss page, Stripe webhook delivery failures, Telnyx webhook failures, worker queue lag, and payment failure events.
- Configure a real support inbox and response owner. Reply to setup and failed-payment requests within one business day until support coverage is formalized.
- Have Canadian counsel review the public terms, privacy policy, acceptable use, SMS consent language, cancellation wording, and data-retention statements before the first broad campaign.

## Production audit: 2026-08-20

The Railway production project has separate online API, worker, scheduler, PostgreSQL, Redis, marketing, CRM, and daily backup services. Public checks returned HTTP 200 for `/api/v1/health/live`, `/api/v1/health/ready`, and `/never-miss`. An unsigned request to the Stripe webhook returned HTTP 400, which confirms the deployed endpoint rejects an unverified payload.

The reviewed local release adds the `20260820_nm_trial_lifecycle` migration, trial and scheduled-cancellation tracking, a customer-scoped Billing Portal session, customer-confirmed recovery testing, and authenticated operations metrics for oldest outbox age, Stripe failed payments in the prior 24 hours, and unprocessed Telnyx webhooks. The focused API test suite passed 38 tests; marketing lint, type check, tests, and production build passed locally.

The current encrypted backup marker and artifact were verified on 2026-08-20, including its checksum. A fresh restore drill passed against an isolated PostgreSQL 18 database and the disposable database was removed afterwards. The `20260820_nm_trial_lifecycle` migration was applied transactionally over Railway's private network and the new columns were verified.

The object-store credentials cannot read or set the bucket lifecycle policy, so retention is not yet confirmed. Grant the backup operator only the bucket-lifecycle permission needed to set and verify a written schedule, then record it here. Also name an on-call owner and a support inbox owner before accepting a paid customer. The production API environment still needs a verified live Stripe secret, and marketing needs the two verified free-trial Payment Link URLs before self-service checkout can open.

## Low-cost Google Search campaign, ready to build after the above is complete

Start with one Canada-only Search campaign at CAD $15/day for 14 days. Use the Never Miss landing page, not the checkout page, as the initial final URL. The campaign should have only these ad groups:

1. **Missed-call recovery**: `[missed call text service]`, `[missed call text back]`, `"missed call text service"`, `"automatic missed call text"`.
2. **Contractors**: `[missed call solution for contractors]`, `"contractor missed calls"`, `"plumber missed calls"`, `"electrician missed calls"`.
3. **Call-back follow-up**: `[missed call follow up]`, `"call back reminder for small business"`, `"customer call back system"`.

Use two responsive search ads per ad group. Keep claims factual: “Text missed callers automatically”, “30-day free trial”, “$39 CAD/month after trial”, “Cancel before day 30 to avoid your first charge”, and “Keep your current business number.” Do not claim guaranteed bookings, revenue, AI reception, or features that are not in production.

Initial negative keywords: `free`, `job`, `jobs`, `career`, `template`, `script`, `iphone setting`, `android setting`, `voicemail greeting`, `call centre job`, `answering service job`, `phone repair`, `fax`, `personal use`, `residential`. Review the search-terms report twice a week and add irrelevant queries deliberately.

Before enabling ads, measure three separate conversions: `trial_checkout_started`, `trial_checkout_completed`, and `never_miss_activation_completed`. Keep the consent banner and conversion tags consistent with the privacy policy. Do not add call assets until the PNS number is visible as text on the advertising domain and can be verified by Google.

Google recommends starting Search keyword lists with precise, relevant terms and then expanding with evidence. It also supports account and campaign negative keywords, while the search-terms report lets the team inspect the queries that triggered ads. See [Google’s keyword guidance](https://support.google.com/google-ads/answer/10039665), [negative-keyword guidance](https://support.google.com/google-ads/answer/7102995), and [call-ad phone verification requirements](https://support.google.com/adspolicy/answer/16428224).
