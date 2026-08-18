# CRM Cycle Status and Product Memory

Last verified: August 17, 2026

Purpose: preserve what is proven, what remains uncertain, and what should guide the next CRM development cycle. Update this document after every production acceptance run and whenever daily sales use reveals meaningful friction.

## Current operating decision

The CRM is ready for assisted daily sales work. The next cycle should be guided by real usage rather than adding broad features immediately. Pacific North Systems should use the system for one week, record friction and outcomes, then prioritize improvements that increase qualified conversations, follow up reliability, and closed revenue.

## Working and production verified

| Capability | Current evidence |
| --- | --- |
| Website assessment intake | Assessment submissions create CRM leads and appear in the Today workspace. |
| Assessment email delivery | Resend shows delivered customer results and delivered internal lead notifications. |
| Missed call capture | A real missed call from the PNS number appears in CRM communication history and Today. |
| Missed call recovery SMS | A real recovery message was received and the outbound message appears in CRM history. |
| Callback follow up | The missed call created a callback task that could be completed from Today. |
| Daily sales workspace | Assessment leads, missed calls, due tasks and leads without a next action load in production. |
| Follow up loop | Complete, reschedule, assign next step and terminal outcomes are implemented and tested. |
| Auditability | Follow up actions create append only audit records with actor, previous state, new state and time. |
| Authentication | CRM pages and business APIs require Clerk authentication. Invalid and missing API tokens are rejected. |
| Tenant isolation | Automated coverage verifies that one organization cannot read another organization's records. |
| Backups | Encrypted Cloudflare R2 backup freshness is healthy. The verified recovery baseline passed checksum, schema, migration and disposable restore checks. |
| Monitoring | Database, Redis, worker heartbeat, backups and outbox counts are visible in the Operations page. |
| Release traceability | Operations displays the Railway deployment identifier and Git commit for the live API. |
| Production hardening | API documentation and OpenAPI are hidden in production. Liveness and readiness probes pass. |
| CRM MCP gateway | The gateway is deployed for controlled CRM context and actions from Codex. |
| Outbound text configuration | The PNS Telnyx number, messaging profile and delivery callback are configured. |
| Browser calling credentials | Telnyx credential creation succeeds with the correct PNS credential connection. |

## Working but needing daily evidence

| Capability | What to measure next |
| --- | --- |
| Lead prioritization | Compare recommended leads with actual conversations, meetings and opportunities. |
| Personalized outreach | Track reply rate, meeting rate and opt outs by message style and lead source. |
| Lead discovery and enrichment | Check accuracy of company facts and decision maker information before outreach. |
| Call preparation | Record which scripts and objection responses help create a clear next step. |
| Browser calling | Outbound and incoming interfaces are implemented. Run one controlled inbound production call before changing the proven mobile and Never Miss routing. Confirm browser ringing, two way audio, hangup and CRM logging. |
| CRM MCP actions | Use the gateway during daily work and record missing context, awkward approvals and repetitive steps. |

## Not production ready or intentionally postponed

| Capability | Decision |
| --- | --- |
| Answering incoming calls inside the browser | Implementation and focused tests are complete. Production routing remains intentionally unchanged until a supervised end to end call proves ringing, answer, audio, reconnect, hangup and the unanswered fallback. |
| Fully autonomous outreach | Postponed. Codex should prepare and prioritize messages, while a person approves external communication until quality and response data are established. |
| Autonomous deal closing | Not treated as a software feature. Codex can prepare strategy, proposals and follow ups, but a founder remains responsible for commitments, pricing exceptions and contracts. |

## Known operational items

| Item | Current status |
| --- | --- |
| Outbox failed events | Seven historical failures remain below the alert threshold. Review if the count grows or a current workflow is affected. |
| Outbox pending events | Six pending events were within the normal range during acceptance. Monitor age as well as count. |
| Historical assessment leads | Several test or research leads remain visible. Archive them when they no longer support acceptance or training. |

## Recommended next cycle

1. Run the CRM in real sales work for one week without adding broad features.
2. Create an approval inbox containing prioritized calls, prepared emails, prepared texts and the reason for every recommendation.
3. Record outcomes for every attempted contact: no answer, wrong person, conversation, interested, meeting, proposal, won, lost or follow up required.
4. Build a simple sales learning report showing which industries, lead sources, messages and offers generate conversations and meetings.
5. Improve only the workflow steps that repeatedly waste time or lose qualified prospects.

## Daily operating memory

Codex should begin each sales session by reading the current CRM state and this report. It should then:

1. Identify the highest value contacts requiring action today.
2. Explain briefly why each contact is prioritized.
3. Prepare a call objective, short call script, email and text where appropriate.
4. Ask for approval before sending external communication unless the user explicitly authorizes a defined campaign.
5. Record the result and create a concrete next action with an owner and date.
6. Add newly discovered friction, failures and useful patterns to this document for the next development cycle.

## Acceptance evidence from this cycle

| Check | Result |
| --- | --- |
| Focused API production suites | 45 passed |
| Missed call worker recovery suite | 21 passed |
| Call Center focused interface tests | 2 passed |
| TypeScript validation | Passed |
| Live website, assessment, CRM and API probes | Passed |
| Latest accepted Git commit | `91a9734bd05339a1f5b84e899206e03e81bf554b` |
