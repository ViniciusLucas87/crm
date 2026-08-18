# Never Forget Controlled MVP

Date: 2026-08-18

## Product promise

Never Forget helps a contractor leave every customer with one private after service record containing the work summary, receipt link, work photos, warranty information, maintenance instructions and recommended next service date.

The customer opens a private link. No application, account or password is required.

## Implemented workflow

1. An authenticated contractor creates a service record in the CRM.
2. The API creates a cryptographically random private token and stores only its SHA 256 hash.
3. The contractor receives a customer link and chooses how to share it during the controlled pilot.
4. The customer views the record without exposing their saved phone number or email address.
5. The customer can request another visit, ask a question or stop reminders.
6. The request appears in the contractor workspace.
7. If the customer explicitly consented and a future service date exists, a deterministic reminder record is scheduled.

## Safety state

Live reminder delivery is disabled by default with `NEVER_FORGET_LIVE_MESSAGES_ENABLED=false`. The MVP stores schedules but no worker sends them. This avoids accidental customer communication before consent language, Telnyx delivery, opt out and cost acceptance tests are complete.

The public action endpoint is protected by an unguessable token, does not expose internal identifiers or customer contact information, and limits repeated actions to five per hour per record. Receipt and photo links must use HTTPS. All contractor queries are organization scoped and write access requires the existing Clerk permission layer.

## Not implemented yet

1. Direct photo and receipt uploads to isolated R2 storage
2. Automatic delivery of the initial customer link
3. Live scheduled SMS or email reminders
4. Stripe price and entitlement for Never Forget
5. Editing and archiving a service record
6. Marking customer requests as completed
7. Data export and deletion user interface
8. Reminder delivery receipts and retry handling
9. Per product communication and storage cost counters

These are release gates, not hidden claims of completeness.

## Acceptance test before live pilot

1. Create a record using PNS as the contractor and an owner controlled customer address.
2. Open the private link in a signed out browser.
3. Confirm no customer telephone number, email or token hash is visible.
4. Submit a service request and confirm it appears in the CRM.
5. Stop reminders and confirm all pending reminders are cancelled.
6. Connect isolated R2 uploads and verify delete behaviour.
7. Enable delivery only in a test organization and send one approved reminder.
8. Verify sender identification, consent record, STOP handling, delivery receipt and cost record.
9. Keep the public marketing page labelled as a controlled pilot until contractor demand is measured.
