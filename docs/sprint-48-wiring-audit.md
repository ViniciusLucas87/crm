# Sprint 48.0 — System Wiring Audit Report
# Generated 2026-08-01
# Pacific North Systems — Project TITAN

================================================================================
SECTION 1 — COMPLETE WIRING MATRIX
================================================================================

Legend:
  ✅ WIRED         — Fully connected end-to-end
  ⚠️ PARTIAL       — Some parts connected, gaps exist
  ❌ UNWIRED       — No connection exists
  🟡 DEFAULT       — Returns default/static value
  🔴 MOCK          — Hardcoded mock data
  ⬜ NO_PRODUCER   — Data exists but no event creates it
  ⬛ NO_CONSUMER   — Event fires but nothing reads it
  🔵 NO_API        — Backend has data, no API serves it
  🟣 NO_UI         — API exists, no frontend consumes it
  🟠 DUPLICATE     — Multiple sources of truth for same concept

================================================================================
1.1 CONVERSATION / RELATIONSHIP METRICS
================================================================================

| Feature | UI | API | DB | Status | Detail |
|---------|-----|-----|-----|--------|--------|
| Relationship Stage | CompanyConversationTab selector | PATCH /api/conversations/{id}?stage= | Conversation.relationship_stage | ⚠️ PARTIAL | Selector writes stage; summary metric card may read from wrong field |
| Stage display (metric card) | conversation tab stats grid | GET /api/conversations?company_id=X | Conversation.relationship_stage | ⚠️ PARTIAL | Shows "New" while selector shows "Negotiation" — likely stale or wrong field read |
| Calls count | Stats grid card | conversation-conversation-tab.tsx | derived from calls | 🟡 DEFAULT | Shows "0" — no call-to-conversation linkage exists |
| Activities count | Stats grid card | same | derived from activities | 🟡 DEFAULT | Shows "0" — activities exist but not linked to conversation |
| Tasks count | Stats grid card | same | derived from tasks | 🟡 DEFAULT | Shows "0" — tasks exist but not linked to conversation |
| Days Active | Stats grid card | same | derived from activities | 🟡 DEFAULT | Shows "0" — no calculation logic |
| Health Score | Stats grid card | same | N/A | 🔴 MOCK | Shows "Cold 50/100" — hardcoded default |
| Talk Time | Stats grid card | same | derived from calls | 🟡 DEFAULT | Shows empty — no aggregation |
| Owner | Stats grid card | same | Company.owner or Conversation assigned_user | 🟡 DEFAULT | Shows empty — no owner on conversation |
| Conversation Timeline | Merged feed | same component | calls + activities + tasks | ⚠️ PARTIAL | Renders but empty because no records linked to conversation |

================================================================================
1.2 CALL LIFECYCLE (TELNYX)
================================================================================

| Feature | UI | API | DB | Status | Detail |
|---------|-----|-----|-----|--------|--------|
| Call initiation | CallButton → WebRTC | POST /api/telephony/token → GET /api/telephony/call?to=X | CallSession (in-memory) | ⚠️ PARTIAL | CallSession is in-memory dataclass, NOT persisted to DB |
| Call connected | LiveTranscript UI | telnyx webhook → call.answered | CallSession.status | ⚠️ PARTIAL | State tracked in memory only |
| Call ended | PostCallPreview | telnyx webhook → call.hangup | CallSession (duration calculated) | ⚠️ PARTIAL | Duration calculated in memory, NOT persisted |
| Call → Activity | N/A | N/A | Activity table | ❌ UNWIRED | Calls do NOT create Activity records |
| Call → Timeline | N/A | N/A | N/A | ❌ UNWIRED | Calls do NOT create Timeline events |
| Call → Conversation | N/A | N/A | Conversation | ❌ UNWIRED | Calls do NOT update conversation metrics |
| Call → Knowledge Graph | N/A | N/A | KnowledgeFact | ❌ UNWIRED | Calls do NOT write KG facts |
| Call miss handling | N/A | telnyx webhook → call.missed | CallSession (in-memory) | ⚠️ PARTIAL | Missed tracked in memory only, no activity/timeline |
| Call failure handling | N/A | telnyx webhook → call.failed | CallSession (in-memory) | ⚠️ PARTIAL | Same as missed |
| Call duration | N/A | Calculated from answered_at→ended_at | CallSession.duration_seconds | ⚠️ PARTIAL | In-memory only |
| Post-call analysis | N/A | N/A | N/A | ❌ UNWIRED | No consumer exists |
| Follow-up from call | N/A | N/A | Task | ❌ UNWIRED | No auto-task from call commitments |
| Seller talk time | N/A | N/A | N/A | ❌ UNWIRED | Not tracked |
| Prospect talk time | N/A | N/A | N/A | ❌ UNWIRED | Not tracked |

================================================================================
1.3 TRANSCRIPTION
================================================================================

| Feature | UI | API | DB | Status | Detail |
|---------|-----|-----|-----|--------|--------|
| Live transcript | LiveTranscript component | WebSocket via Deepgram | N/A | ✅ WIRED | Real-time UI works |
| Transcript segments | N/A | N/A | transcript_segments | ⚠️ PARTIAL | Model exists in DB but unclear if populated |
| Final transcript | N/A | N/A | transcripts | ⚠️ PARTIAL | Model exists, unknown if populated on call end |
| Transcript → Activity | N/A | N/A | N/A | ❌ UNWIRED | Transcript completion does not create activity |
| Transcript → Timeline | N/A | N/A | N/A | ❌ UNWIRED | No timeline entry |
| Transcript → Knowledge Graph | N/A | N/A | N/A | ❌ UNWIRED | No KG facts extracted |

================================================================================
1.4 ASSESSMENT / WEBSITE INTEGRATION
================================================================================

| Feature | UI | API | DB | Status | Detail |
|---------|-----|-----|-----|--------|--------|
| Assessment submission | Marketing form | POST /api/v1/public/automation-assessment | automation_assessments + companies + contacts + leads | ✅ WIRED | Full pipeline works |
| Assessment → Activity | N/A | Assessment service | activities | ✅ WIRED | Activity created on submission |
| Assessment → Task | N/A | Assessment service | tasks | ✅ WIRED | Follow-up task created |
| Assessment → Outbox | N/A | Assessment service | outbox_events | ✅ WIRED | 6 events written |
| Assessment → Email | N/A | outbox_process_email worker | outbox_events + SMTP | ✅ WIRED | Both internal + visitor emails delivered |
| Assessment → Knowledge Graph | N/A | knowledge_assessment_ingestion worker | knowledge_facts | ✅ WIRED | 10+ facts written |
| Assessment → Timeline | N/A | N/A | lead_timeline_events | ❌ UNWIRED | No timeline event created |
| Assessment → Conversation | N/A | N/A | conversations | ❌ UNWIRED | Assessment does not update conversation metrics |
| Assessment → Relationship stage | N/A | N/A | N/A | ❌ UNWIRED | Assessment does not advance stage |
| Assessment → Relationship health | N/A | N/A | N/A | ❌ UNWIRED | No health recalculation |
| Assessment → Opportunity | N/A | Assessment service | leads (opportunity_score) | ⚠️ PARTIAL | Updates lead score, not Opportunity model directly |
| Assessment → AI Summary | N/A | N/A | N/A | ❌ UNWIRED | No summary generation queued |
| Assessment detail page | /assessments/[id] | GET /api/v1/assessments/{uuid} | automation_assessments | ✅ WIRED | Full CRM page with intelligence |
| Assessment → Lead card | AssessmentIntelligenceCard | GET /api/v1/assessments/by-lead/{id} | automation_assessments | ✅ WIRED | Component exists |

================================================================================
1.5 ACTIVITIES
================================================================================

| Feature | UI | API | DB | Status | Detail |
|---------|-----|-----|-----|--------|--------|
| Activity list | ActivityTimeline component | GET /api/activities?company_id=X | activities | ✅ WIRED | Works for assessment activities |
| Activity → Timeline | TimelineView | N/A | lead_timeline_events or projection | ⚠️ PARTIAL | Timeline exists but may not include all activities |
| Activity → Conversation | CompanyConversationTab | N/A | conversations | ❌ UNWIRED | Activities not linked to conversation |
| Activity from calls | N/A | N/A | N/A | ❌ UNWIRED | No producer |
| Activity from emails | N/A | N/A | N/A | ❌ UNWIRED | No producer |
| Activity from meetings | N/A | N/A | N/A | ❌ UNWIRED | No producer |
| Activity from notes | N/A | N/A | N/A | ❌ UNWIRED | No producer |
| Activity from opportunity changes | N/A | N/A | N/A | ❌ UNWIRED | No producer |

================================================================================
1.6 TIMELINE
================================================================================

| Feature | UI | API | DB | Status | Detail |
|---------|-----|-----|-----|--------|--------|
| Timeline view | TimelineView component | timeline API | lead_timeline_events | ⚠️ PARTIAL | Model exists, likely empty for most entities |
| Call timeline entries | N/A | N/A | N/A | ❌ UNWIRED | No producer |
| Email timeline entries | N/A | N/A | N/A | ❌ UNWIRED | No producer |
| Assessment timeline entries | N/A | N/A | N/A | ❌ UNWIRED | No producer |
| Task timeline entries | N/A | N/A | N/A | ❌ UNWIRED | No producer |
| Stage change timeline entries | N/A | N/A | N/A | ❌ UNWIRED | No producer |

================================================================================
1.7 TASKS
================================================================================

| Feature | UI | API | DB | Status | Detail |
|---------|-----|-----|-----|--------|--------|
| Task list | CompanyTasksTab | tasks API | tasks | ✅ WIRED | Assessment follow-up tasks visible |
| Task → Timeline | N/A | N/A | N/A | ❌ UNWIRED | No timeline event on task creation/completion |
| Auto-task from call | N/A | N/A | N/A | ❌ UNWIRED | No commitment→task extraction |
| Auto-task from email | N/A | N/A | N/A | ❌ UNWIRED | No producer |
| Auto-task from meeting | N/A | N/A | N/A | ❌ UNWIRED | No producer |
| Task → Conversation | N/A | N/A | conversations | ❌ UNWIRED | Tasks not linked to conversation |

================================================================================
1.8 OPPORTUNITIES
================================================================================

| Feature | UI | API | DB | Status | Detail |
|---------|-----|-----|-----|--------|--------|
| Opportunity list | CompanyOpportunitiesTab | opportunities API | opportunities | ✅ WIRED | CRUD works |
| Opportunity from assessment | Assessment service | N/A | leads (acts as lead) | ⚠️ PARTIAL | Assessment creates Lead, not Opportunity directly |
| Opportunity → Timeline | N/A | N/A | N/A | ❌ UNWIRED | Stage changes not on timeline |
| Opportunity momentum | N/A | N/A | N/A | ❌ UNWIRED | No momentum tracking |
| Opportunity auto-update | N/A | N/A | N/A | ❌ UNWIRED | Communications don't update opportunity |

================================================================================
1.9 KNOWLEDGE GRAPH
================================================================================

| Feature | UI | API | DB | Status | Detail |
|---------|-----|-----|-----|--------|--------|
| Company KG facts | CompanyIntelligenceTab | knowledge API | knowledge_facts | ⚠️ PARTIAL | UI exists, assessment facts populate |
| KG from calls | N/A | N/A | N/A | ❌ UNWIRED | No producer |
| KG from emails | N/A | N/A | N/A | ❌ UNWIRED | No producer |
| KG from transcripts | N/A | N/A | N/A | ❌ UNWIRED | No producer |
| KG from meetings | N/A | N/A | N/A | ❌ UNWIRED | No producer |

================================================================================
1.10 AI SUMMARY
================================================================================

| Feature | UI | API | DB | Status | Detail |
|---------|-----|-----|-----|--------|--------|
| AI Summary tab | CompanyAiSummaryTab | N/A | N/A | 🟡 DEFAULT | Shows empty state — no summary generation |
| Post-call summary | PostCallPreview | N/A | N/A | ❌ UNWIRED | No producer |
| Relationship summary | N/A | N/A | N/A | ❌ UNWIRED | No producer |

================================================================================
1.11 DOCUMENTS
================================================================================

| Feature | UI | API | DB | Status | Detail |
|---------|-----|-----|-----|--------|--------|
| Document list | DocumentManager | documents API | company_documents | ✅ WIRED | CRUD works |
| Document → Timeline | N/A | N/A | N/A | ❌ UNWIRED | No timeline event on upload |

================================================================================
1.12 DASHBOARD KPIs
================================================================================

| Feature | UI | API | DB | Status | Detail |
|---------|-----|-----|-----|--------|--------|
| Dashboard page | / (dashboard) | dashboard endpoints | daily_metrics + live queries | ⚠️ PARTIAL | KPIs query live data; some fallbacks |
| Companies KPI | Dashboard cards | /api/dashboard/* | companies | ✅ WIRED | |
| Leads KPI | Dashboard cards | /api/dashboard/* | leads | ✅ WIRED | |
| Opportunities KPI | Dashboard cards | /api/dashboard/* | opportunities | ✅ WIRED | |
| Tasks KPI | Dashboard cards | /api/dashboard/* | tasks | ✅ WIRED | |

================================================================================
SECTION 2 — EMPTY-FIELD / DEFAULT-VALUE INVENTORY
================================================================================

2.1 CONVERSATION TAB (CompanyConversationTab)
  - Calls: "0" — no call-to-conversation linkage
  - Activities: "0" — activities not linked to conversation
  - Tasks: "0" — tasks not linked to conversation
  - Days Active: "0" — no calculation logic
  - Health: "Cold 50/100" — HARDCODED DEFAULT (line in component: `healthScore: 50, healthLabel: "Cold"`)
  - Talk Time: empty/blank — no aggregation
  - Owner: empty — no owner on conversation or company
  - Stage: inconsistent between selector and metric card

2.2 AI SUMMARY TAB (CompanyAiSummaryTab)
  - Shows empty state — no summary generation pipeline exists

2.3 COMPANY INTELLIGENCE TAB
  - Shows enrichment data if populated by workers
  - Assessment intelligence for new assessments flows through

2.4 TIMELINE (TimelineView)
  - Empty for most entities — only populated if lead_timeline_events has records
  - No automatic population from assessment, calls, emails, or activities

================================================================================
SECTION 3 — MOCK / DEFAULT-VALUE INVENTORY
================================================================================

3.1 Conversation Health: `healthScore: 50, healthLabel: "Cold"` — hardcoded in CompanyConversationTab
3.2 Conversation Stage metric: reads from a different field than the stage selector writes to
3.3 Task priority: defaults to "medium"
3.4 Lead score: uses _calculate_lead_score() which is a good deterministic function
3.5 Opportunity probability: defaults to 50
3.6 Company research_status: defaults to "pending"

================================================================================
SECTION 4 — MISSING EVENT PRODUCERS
================================================================================

4.1 Call → Activity producer — calls completed/missed/failed do not create activities
4.2 Call → Timeline projector — no timeline entry on call events
4.3 Call → Conversation updater — calls don't update conversation metrics
4.4 Call → Knowledge Graph — no facts extracted from calls
4.5 Call → Post-call analysis — no consumer
4.6 Email → Activity producer — no email activity creation
4.7 Email → Timeline projector — no timeline entry on email events
4.8 Assessment → Timeline projector — no timeline entry on assessment
4.9 Assessment → Conversation updater — no conversation updates
4.10 Assessment → Relationship stage — no stage advancement
4.11 Assessment → AI Summary — no summary generation
4.12 Task → Timeline projector — no timeline on task creation/completion
4.13 Opportunity → Timeline projector — no timeline on stage changes
4.14 Document → Timeline projector — no timeline on upload

================================================================================
SECTION 5 — MISSING EVENT CONSUMERS
================================================================================

5.1 assessment.completed — no consumer (only written, not processed beyond email/KG)
5.2 assessment.report.requested — no consumer (PDF not generated)
5.3 lead.followup.requested — partially consumed (task exists but no automation)
5.4 knowledge.assessment_ingestion.requested — ✅ consumed by knowledge_assessment_ingestion worker
5.5 Call-related outbox events — NONE EXIST (no outbox events for calls)

================================================================================
SECTION 6 — DUPLICATE SOURCE OF TRUTH INVENTORY
================================================================================

6.1 Lead vs Opportunity: Assessment creates a Lead (with opportunity_score, estimated_value), 
    but there's a separate Opportunity model. Two competing entities for sales pipeline data.
    
6.2 Relationship Stage: Conversation.relationship_stage (set by selector) 
    vs. Lead.status (new/qualified/contacted) 
    vs. Opportunity.stage (lead/qualified/proposal/etc.)
    Three different stage/status fields with overlapping semantics.

6.3 Company owner: Company.owner (String column, not FK to users) 
    vs. no conversation-level owner.

6.4 Health/Score: Company.opportunity_score + Company.confidence_score 
    vs. Lead opportunity_score
    vs. AutomationAssessment.automation_score
    vs. Hardcoded conversation health = 50.

================================================================================
SECTION 7 — CURRENT DATA MODEL GAPS
================================================================================

7.1 CallSession: EXISTS as in-memory dataclass ONLY. Not persisted to database.
    ✅ Has: session_id, provider_call_id, company_id, contact_id, duration_seconds, 
           direction, status, transcript_status
    ❌ Missing: DB table for persistence, conversation_id, activity_id linkage

7.2 No Communication/Email/Meeting models exist in the database
    ❌ No EmailMessage table
    ❌ No MeetingSession table  
    ❌ No CommunicationThread table
    ❌ No CommunicationParticipant table

7.3 Conversation model exists but linkages are incomplete:
    ✅ Has: company_id, primary_contact_id, relationship_stage, status, summary
    ❌ Missing: activity count projection, call count projection, health score,
               talk time aggregation, owner, days_active calculation

7.4 Activity model:
    ✅ Has: company_id, contact_id, activity_type, subject, body
    ❌ Missing: conversation_id, opportunity_id, communication_id, 
               direction, occurred_at (uses created_at), correlation_id

7.5 No Timeline projector service exists (must be built)
    ❌ lead_timeline_events exists but is likely for lead research pipeline, 
       not general CRM timeline

================================================================================
SECTION 8 — PROPOSED IMPLEMENTATION PHASES
================================================================================

PHASE 1: Canonical Activity + Timeline Wiring (Sprint 48.1)
  - Persist CallSession to database
  - Create Call→Activity projector
  - Create Assessment→Timeline projector
  - Create Activity→Conversation linker
  - Wire Activity list to show all sources
  - Ensure Timeline shows calls, assessments, activities, tasks

PHASE 2: Telnyx Call Lifecycle + Metrics (Sprint 48.2)
  - Full call lifecycle: initiated→connected→ended with persistence
  - Call→Activity generation (all states: completed, missed, failed)
  - Call→Timeline projection
  - Call→Conversation metrics update (call count, talk time, last interaction)
  - Post-call analysis worker
  - Speaker talk time tracking

PHASE 3: Email Ingestion + Delivery (Sprint 48.3)
  - Create EmailMessage model
  - Create Email→Activity projector (sent, received, bounced)
  - Create Email→Timeline projector
  - Zoho Mail IMAP/webhook ingestion strategy
  - Thread matching (Message-ID, In-Reply-To, References)
  - Entity resolution (email→Contact lookup)
  - Email→Conversation metrics update

PHASE 4: Meeting Integration (Sprint 48.4)
  - Create MeetingSession model
  - Meeting→Activity projector
  - Meeting→Timeline projector
  - Google Calendar or Calendly webhook integration

PHASE 5: Relationship Metrics + Health (Sprint 48.5)
  - Build RelationshipHealthService (versioned, deterministic)
  - Build metrics projector (counts, days active, talk time, last interaction)
  - Resolve stage source-of-truth conflict
  - Wire Conversation tab metrics to real data
  - Owner resolution logic

PHASE 6: AI Summary + KG Enrichment (Sprint 48.6)
  - Build AI Relationship Summary generator
  - Wire post-call summary generation
  - Wire assessment→AI summary
  - Expand KG ingestion from calls, emails, meetings

PHASE 7: Task + Opportunity Automation (Sprint 48.7)
  - Auto-task from call commitments
  - Auto-task from email questions
  - Opportunity momentum updates from communications
  - Stage advancement suggestions

PHASE 8: Backfill + Replay (Sprint 48.8)
  - Backfill timeline from existing activities
  - Recalculate relationship metrics
  - Rebuild health scores
  - Verify end-to-end

================================================================================
SECTION 9 — RISK ASSESSMENT
================================================================================

HIGH RISK:
  - CallSession not persisted: all call data is lost on server restart
  - No email/meeting models: entire communication channels unrepresented
  - Multiple stage/status fields: UI inconsistency guaranteed without resolution

MEDIUM RISK:
  - Conversation metrics hardcoded: misleading zeros erode trust
  - No idempotency on call/email ingestion: risk of duplicates
  - Knowledge Graph not fed by calls/emails: AI summaries will be incomplete

LOW RISK:
  - Assessment pipeline is solid foundation to extend
  - Outbox pattern is proven and reliable
  - Existing worker infrastructure supports new projectors

================================================================================
SECTION 10 — PROVIDER INTEGRATION PLAN
================================================================================

Telnyx (Calls):
  - Existing: WebRTC SDK in browser, webhook receiver in backend
  - Gap: No persistence, no activity/timeline/KG projection
  - Plan: Persist CallSession via webhook handler, add outbox events, build projectors

Zoho Mail (Email):
  - Existing: SMTP outbound via Celery worker (working)
  - Gap: No inbound ingestion, no email model, no threading
  - Plan: IMAP polling worker using existing Zoho app password (proven auth)
    OR Zoho Mail API webhooks (requires Zoho API setup)
  - Recommended: Start with IMAP polling every 60s for MVP, add webhooks later

Calendar (Meetings):
  - Existing: Calendly booking links in emails
  - Gap: No meeting model, no calendar integration
  - Plan: Calendly webhook → meeting creation → activity → timeline
    OR Google Calendar API if Google Workspace is configured
