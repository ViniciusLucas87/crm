# ADR-001: Asynchronous Intelligence Pipeline

**Status**: Accepted  
**Date**: 2026-07-22  
**Author**: Pacific North Systems Engineering  
**Supersedes**: Synchronous enrichment (pre-Sprint 20)

---

## 1. Context

Pacific North Systems OS is transitioning from a CRM into an AI Sales Intelligence Platform. The original architecture performed AI enrichment synchronously during discovery — the user waited 25-30 seconds per company while the LLM generated scores, founder advice, and project recommendations.

This created three problems:

1. **Blocking UX** — Users stared at spinners while enrichment ran.
2. **Sequential bottleneck** — Companies were enriched one at a time. Ten companies meant 4-5 minutes of waiting.
3. **Provider lock-in** — Adding Google Maps, LinkedIn, or website crawling required modifying the discovery engine itself. Every provider needed its own bespoke workflow.

The Intelligence Pipeline solves all three by separating *Discovery* from *Intelligence* and making every data source a pluggable stage.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      USER SEARCH                         │
└─────────────────────┬───────────────────────────────────┘
                      │ < 5 seconds
                      ▼
┌─────────────────────────────────────────────────────────┐
│                 DISCOVERY PROVIDER                       │
│  (LLM / Google Maps / Clearbit / future providers)      │
│                                                         │
│  • Searches external data sources                       │
│  • Normalizes company data                              │
│  • Saves Lead records                                   │
│  • Creates EnrichmentJob records                         │
│  • Queues Celery tasks                                  │
│  • Returns immediately                                  │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                  CELERY JOB QUEUE                        │
│              (Redis-backed, 4 workers)                   │
│                                                         │
│  Each company → 1 independent enrichment task            │
│  One failure never blocks another company               │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              INTELLIGENCE PIPELINE                       │
│                                                         │
│  Stage 1: Discovery          ✓ Completed (sync)         │
│  Stage 2: AI Research        ⏳ Background worker        │
│  Stage 3: Website Intel      ⏳ Future provider          │
│  Stage 4: Google Maps        ⏳ Future provider          │
│  Stage 5: Google Reviews     ⏳ Future provider          │
│  Stage 6: LinkedIn Intel     ⏳ Future provider          │
│  Stage 7: Tech Detection     ⏳ Future provider          │
│  Stage 8: Buying Signals     ⏳ Future provider          │
│  Stage 9: News Intel         ⏳ Future provider          │
│  Stage 10: Lead Intelligence ⏳ Aggregator stage         │
│                                                         │
│  Each stage: independent, retryable, traceable           │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                    UI AUTO-REFRESH                        │
│                                                         │
│  • Polls every 3 seconds while enrichments are pending  │
│  • Intel column: 🟡 Waiting → 🔵 Processing → 🟢 Ready  │
│  • PNS Fit scores appear progressively                   │
│  • Founder Mode card populates as stages complete        │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Discovery Layer

### 3.1 Responsibility

Discovery does **one thing**: find companies and queue them for intelligence. It does NOT enrich, score, or analyze. Those are pipeline stages.

### 3.2 Flow

```python
# discovery_engine.py — DiscoveryEngine.discover()

async def discover(self, org_id, criteria) -> DiscoveryResult:
    # 1. Call provider (LLM, Google Maps, etc.)
    companies = await self._provider.discover(criteria)     # ~1-3 seconds

    # 2. For each unique company:
    for company in companies:
        if is_duplicate(company):
            skip

        # Create lead with minimal data (status="new", enrichment_status="pending")
        lead = self._create_lead_fast(org_id, company)

        # Queue Celery task for background enrichment
        job_id = queue_enrichment(
            lead_id=lead.id,
            company_name=company.name,
            industry=company.industry,
            # ... all fields needed by the enrichment prompt
        )

        # Record the job for tracking
        self._session.add(EnrichmentJob(
            id=job_id,
            lead_id=lead.id,
            status="queued",
            discovery_source="ai_discovery",
        ))

    # 3. Return immediately — no enrichment
    return result   # ~3.6 seconds total
```

### 3.3 Performance Target

| Metric | Target | Measured |
|--------|--------|----------|
| Discovery latency | < 5 seconds | 3.6-3.8s |
| Companies per search | 5-10 | 5-10 |
| Duplicate detection | Inline | SQL ILIKE |

### 3.4 Adding a New Discovery Provider

Implement `DiscoveryProvider` (abstract class):

```python
class DiscoveryProvider(ABC):
    @abstractmethod
    async def discover(self, criteria: DiscoveryCriteria) -> list[DiscoveredCompany]:
        ...

class GoogleMapsProvider(DiscoveryProvider):
    async def discover(self, criteria):
        # 1. Call Google Maps Places API
        # 2. Normalize to DiscoveredCompany
        # 3. Return list
        pass
```

The engine handles deduplication, lead creation, and job queuing — the provider only searches.

---

## 4. Intelligence Pipeline (Celery Tasks)

### 4.1 Task Lifecycle

```
Queued → Running → Completed
              ↓
           Failed → Retrying → Running → Completed
              ↓
           Failed (permanent — max retries exceeded)
```

### 4.2 Current Implementation

The first enrichment stage ("AI Research") runs as a single Celery task:

```python
# tasks.py

@celery_app.task(
    name="intelligence.enrich_lead",
    bind=True,
    max_retries=4,
    acks_late=True,
)
def enrich_lead(self, lead_id, org_id, company_name, ...):
    # 1. Mark job as "running"
    # 2. Mark lead.enrichment_status = "processing"
    # 3. Call LLM (DeepSeek via OpenAI-compatible API)
    # 4. Parse JSON response
    # 5. Update lead with:
    #    - opportunity_score, pns_fit_score
    #    - pns_fit_data (JSON: founder_recommendation, founder_advice,
    #      fit_factors, first_project, return_on_founder_time, outreach_strategy...)
    #    - executive_summary, buying_signals, recommended_services
    #    - enrichment_status = "complete"
    # 6. Mark job as "completed"
    # 7. Create timeline event
```

### 4.3 Stage Registration (Future)

Each stage will be a separate Celery task with a well-known name:

```
intelligence.ai_research       → Stage 2
intelligence.website_intel      → Stage 3
intelligence.google_maps        → Stage 4
intelligence.google_reviews     → Stage 5
intelligence.linkedin           → Stage 6
intelligence.tech_detection     → Stage 7
intelligence.buying_signals     → Stage 8
intelligence.news_intel         → Stage 9
intelligence.lead_summary       → Stage 10 (aggregator)
```

Each stage:
- Takes `(lead_id, organization_id)` as input
- Reads existing lead data from the database
- Adds new intelligence fields
- Updates its own `EnrichmentJob` record
- Marks completion status

---

## 5. Dependencies Between Stages

Stages declare dependencies via configuration:

```python
STAGE_DEPENDENCIES = {
    "intelligence.ai_research":    [],                          # No deps
    "intelligence.website_intel":   [],                          # Independent
    "intelligence.google_maps":    [],                          # Independent
    "intelligence.google_reviews": ["intelligence.google_maps"], # Needs Maps first
    "intelligence.linkedin":       [],                          # Independent
    "intelligence.tech_detection": ["intelligence.website_intel"],
    "intelligence.buying_signals": [],                          # Independent
    "intelligence.news_intel":     [],                          # Independent
    "intelligence.lead_summary":   ["*"],                       # Waits for all
}
```

A stage with dependencies is only queued after its prerequisites complete. The aggregator stage (`lead_summary`) waits for all other stages and produces the unified recommendation.

### 5.1 Dependency Resolution

```python
def enqueue_stage(lead_id, org_id, stage_name):
    deps = STAGE_DEPENDENCIES.get(stage_name, [])

    if deps == ["*"]:
        # Aggregator: wait for all other stages
        deps = [s for s in STAGE_DEPENDENCIES if s != "intelligence.lead_summary"]

    # Check if all dependencies are complete
    for dep in deps:
        job = get_job(lead_id, dep)
        if not job or job.status != "completed":
            # Re-queue self — will retry when deps complete
            return schedule_retry(lead_id, stage_name)

    # All deps satisfied — queue the task
    celery_app.send_task(stage_name, kwargs={...})
```

---

## 6. Retry and Failure Handling

### 6.1 Retry Schedule

| Attempt | Delay | Rationale |
|---------|-------|-----------|
| 1 | Immediate | Transient error (network blip) |
| 2 | 30 seconds | Brief outage |
| 3 | 2 minutes | Rate limit / quota reset |
| 4 | 10 minutes | Provider degradation |

Maximum 4 attempts per stage. After all retries exhausted, mark as `failed` permanently.

### 6.2 Isolation Guarantees

- **Company isolation**: One company's failure never blocks another. Each company has independent Celery tasks.
- **Stage isolation**: One stage's failure never blocks another stage for the same company. Failed stages are marked individually.
- **Worker isolation**: 4 concurrent workers. If Worker 1 crashes on Company A, Workers 2-4 continue processing Companies B-D.

### 6.3 Error Storage

Every `EnrichmentJob` records:
```python
{
    "status": "failed",
    "attempts": 4,
    "error_message": "AsyncClient.__init__() got an unexpected keyword argument 'proxies'",
    "worker_id": "d705effc33ee",
    "processing_time_ms": 1234,
    "completed_at": "2026-07-22T05:30:20Z"
}
```

---

## 7. Database Model

### 7.1 Lead Extensions

```python
class Lead(Base):
    # ... existing fields ...
    enrichment_status: str   # "pending" | "processing" | "complete" | "failed" | "retrying"
    enrichment_job_id: str   # Celery task UUID for current/last job
```

### 7.2 EnrichmentJob

```python
class EnrichmentJob(Base):
    __tablename__ = "enrichment_jobs"

    id: str                    # Celery task UUID (PK)
    organization_id: int       # Tenant isolation
    lead_id: int               # FK to leads
    discovery_source: str      # "ai_discovery" | "google_maps" | ...
    priority: int              # 0 = normal, higher = sooner
    status: str                # queued | running | completed | failed | retrying | cancelled
    attempts: int              # Current attempt count
    max_attempts: int          # Default 4
    error_message: str         # Last error (500 char limit)
    worker_id: str             # Celery hostname
    processing_time_ms: int    # Total time for successful completion
    created_at: datetime
    started_at: datetime
    completed_at: datetime
```

### 7.3 Future: Stage Tracking

When multi-stage pipeline is fully implemented, `EnrichmentJob` gains a `stage` column:
```python
stage: str  # "ai_research" | "website_intel" | "google_maps" | ...
```

Each lead will have multiple `EnrichmentJob` records — one per stage.

---

## 8. UI Update Propagation

### 8.1 Polling Strategy

The Lead Workspace polls the API every 3 seconds when any lead has a pending enrichment:

```typescript
// workspace/page.tsx
useEffect(() => {
    const hasPending = leads.some(l =>
        l.enrichment_status === "pending" ||
        l.enrichment_status === "processing" ||
        l.enrichment_status === "queued" ||
        l.enrichment_status === "retrying"
    );
    if (!hasPending) return;
    const interval = setInterval(() => fetchLeads(), 3000);
    return () => clearInterval(interval);
}, [leads, fetchLeads]);
```

### 8.2 Status Badges

| Status | Badge | Meaning |
|--------|-------|---------|
| `pending` | 🟡 Waiting | Job queued, not yet picked up |
| `processing` | 🔵 Processing | Worker actively calling LLM |
| `complete` | 🟢 Ready | All enrichment data available |
| `retrying` | 🔄 Retry | Failed, will retry automatically |
| `failed` | 🔴 Failed | Permanent failure after 4 attempts |

### 8.3 Progressive Enrichment

As each stage completes, the lead detail page gains more data:
1. **Discovery only**: Company name, industry, city, employees, score=50
2. **AI Research complete**: PNS Fit score, founder advice, first project, outreach strategy, explainability
3. **Website Intel complete** (future): Tech stack, hiring signals, services detected
4. **Google Reviews complete** (future): Sentiment, pain points, recurring complaints
5. **Lead Summary complete** (future): Unified recommendation, win score

The `PNSFitCard` component only renders when `pns_fit_data` is present — automatically appearing as soon as AI Research completes.

---

## 9. API Endpoints

### 9.1 Discovery

```
POST /api/v1/leads/discover
  → Returns immediately with created leads
  → Enrichment runs in background
  → Message: "AI enrichment running in background"
```

### 9.2 Job Status

```
GET /api/v1/leads/enrichment/jobs?status=running
  → List enrichment jobs with filters

GET /api/v1/leads/enrichment/metrics
  → { total_jobs, queued, running, completed, failed, retrying, avg_processing_time_ms }
```

### 9.3 Sorting

```
GET /api/v1/leads?sort=pns_fit_desc
  → Sort by PNS Fit Score (descending)
  → Supported: score_desc, score_asc, pns_fit_desc, pns_fit_asc, created_at_desc, created_at_asc, name_asc
```

---

## 10. Adding a New Intelligence Provider (Future)

### Step 1: Implement the Provider

```python
# providers/website_intelligence.py
class WebsiteIntelligenceProvider:
    async def analyze(self, website_url: str) -> dict:
        # Crawl website, detect tech stack, extract services
        return {
            "tech_stack": ["React", "AWS", "PostgreSQL"],
            "services": ["Residential electrical", "Commercial wiring"],
            "hiring_signals": ["Hiring 3 electricians"],
        }
```

### Step 2: Create the Celery Task

```python
# tasks.py
@celery_app.task(name="intelligence.website_intel", bind=True, max_retries=4)
def website_intel_task(self, lead_id, org_id):
    lead = get_lead(lead_id)
    if not lead.website:
        skip_stage(lead_id, "website_intel", reason="No website")
        return

    provider = WebsiteIntelligenceProvider()
    result = run_async(provider.analyze(lead.website))

    # Update lead with website intelligence
    update_lead(lead_id, {
        "tech_stack": result["tech_stack"],
        "detected_services": result["services"],
    })

    mark_stage_complete(lead_id, "website_intel")
```

### Step 3: Register the Stage

```python
# config.py
STAGE_DEPENDENCIES["intelligence.website_intel"] = []  # No dependencies

# The discovery engine will automatically queue it
# alongside ai_research for every new lead.
```

### Step 4: Add UI Display

Add a section to the lead detail page that renders when `tech_stack` data is present. No backend changes needed — the polling already works for any new field.

---

## 11. Performance Characteristics

| Metric | Target | Current |
|--------|--------|---------|
| Discovery latency | < 5s | 3.6-3.8s |
| AI Research enrichment | < 30s/company | ~25-30s |
| Worker concurrency | Configurable | 4 workers |
| Max concurrent enrichments | 4 × industry count | 4 simultaneous |
| UI poll interval | 3s | 3s |
| Retry backpressure | Exponential | 0s → 30s → 2m → 10m |

---

## 12. Deployment

### Container Architecture

```
docker-compose.yml:
  postgres  — Database (persistent volume)
  redis     — Celery broker + result backend
  api       — FastAPI (uvicorn, port 8000)
  worker    — Celery worker (4 concurrency, copies API code for model access)
  web       — Next.js 15 (port 3000, proxies /api/* to API)
```

### Environment Variables

```
DEEPSEEK_API_KEY=sk-...    # Required by worker for LLM calls
DATABASE_URL=postgresql...  # Required by worker for model access
REDIS_URL=redis://...       # Required by worker for Celery
```

### Worker Dockerfile

The worker container copies `apps/api/` to access models, database session, and LLM provider — avoiding code duplication:

```dockerfile
COPY apps/api ./api
ENV PYTHONPATH=/app/api:$PYTHONPATH
CMD ["celery", "-A", "tasks.celery_app", "worker", "--loglevel=INFO", "--concurrency=4"]
```

---

## 13. Migration History

| Migration | Date | Change |
|-----------|------|--------|
| `20260722_0002` | 2026-07-22 | Added `pns_fit_score`, `pns_fit_data` to leads |
| `20260722_0003` | 2026-07-22 | Added `enrichment_status`, `enrichment_job_id` to leads; created `enrichment_jobs` table |

---

## 14. Future Roadmap

1. **Multi-stage pipeline** — Split the single `enrich_lead` task into independent stage tasks with dependency resolution.
2. **Intelligence Confidence score** — Calculate an overall confidence percentage based on completed/total stages.
3. **Intelligence Timeline UI** — Show each stage's status in the lead detail page.
4. **Google Maps Provider** — Discovery provider + Maps intelligence stage.
5. **Website Crawling** — Standalone stage that detects tech stack and services.
6. **WebSocket updates** — Replace polling with WebSocket push for real-time enrichment progress.
7. **Stage-level retry UI** — Allow manual retry of individual failed stages from the Intelligence Panel.

---

## 15. Decisions

| Decision | Rationale |
|----------|-----------|
| Celery over async background tasks | Celery provides retry logic, concurrency, monitoring, and queue persistence out of the box. FastAPI background tasks lack these. |
| Polling over WebSockets | Simpler initial implementation. WebSocket upgrade planned for Sprint 21+. |
| Worker copies API code | Avoids maintaining a shared library package. Acceptable for monorepo; will revisit if worker grows substantially. |
| DeepSeek as primary LLM | Compatible with OpenAI API format. Provider-agnostic abstraction allows swapping to Claude/GPT-4o via config change. |
| 4 retries with exponential backoff | Balances transient error recovery against queue bloat. Configurable per-stage in future. |
| `enrichment_status` on Lead vs separate table | Single column simplifies UI queries. Separate `EnrichmentJob` table provides detailed tracking. |

---

*This ADR is the canonical reference for the Intelligence Pipeline architecture. All future providers must integrate through this pipeline. Direct enrichment outside the Celery queue is prohibited.*
