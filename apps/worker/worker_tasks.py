"""
Autonomous Knowledge Workers — Celery Tasks

All 12 workers run as Celery tasks, NOT inside FastAPI.
FastAPI enqueues work. Celery executes it.

Architecture:
    FastAPI → Event Emitter → KnowledgeEvent (DB) + Celery Task (Redis)
    Celery Worker → consume event → execute → write to Knowledge Graph

Workers:
    1. company_enrichment     — enrich companies with fresh data
    2. fact_verification      — cross-source fact validation
    3. entity_resolution      — duplicate detection
    4. relationship_discovery — infer relationships
    5. technology_detection   — detect tech stacks
    6. buying_signal_detector — detect buying intent
    7. knowledge_decay        — age stale facts
    8. reasoning              — generate insights from graph
    9. timeline_generator     — auto-build company history
    10. opportunity_scoring   — continuous scoring
    11. search_indexer        — maintain search index
    12. recommendation_engine — generate recommendations
"""

import logging
import hashlib
import os
import smtplib
import imaplib
import email as email_lib
import httpx
from datetime import UTC, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from celery import Task as CeleryTask
from celery import Celery
from celery.signals import task_failure, task_postrun, task_prerun, task_retry, worker_process_init
from celery.schedules import crontab

logger = logging.getLogger(__name__)


# ── Bounded deterministic ID helpers ──
# correlation_id is VARCHAR(64), idempotency_key is VARCHAR(128).
# Use short prefix + SHA-256 hex digest to stay within limits without truncation.


def bounded_correlation_id(prefix: str, unique_part: str) -> str:
    """Bounded correlation ID: prefix[:4] + SHA256 hex (fits in 64)."""
    digest = hashlib.sha256(f"{prefix}:{unique_part}".encode()).hexdigest()
    return f"{prefix[:4]}:{digest[:59]}"  # 4 + 1 + 59 = 64


def bounded_idempotency_key(prefix: str, unique_part: str) -> str:
    """Bounded idempotency key: prefix[:8] + SHA256 hex (fits in 128)."""
    digest = hashlib.sha256(f"{prefix}:{unique_part}".encode()).hexdigest()
    return f"{prefix[:8]}_{digest[:119]}"  # 8 + 1 + 119 = 128


# ── Shared Celery app ──
_redis_password = os.getenv("REDIS_PASSWORD", "redis_dev")
_broker_url = os.getenv("REDIS_URL", f"redis://:{_redis_password}@redis:6379/0")
_result_backend = os.getenv("REDIS_RESULT_URL", _broker_url)
celery_app = Celery("pns_worker", broker=_broker_url, backend=_result_backend)

# ── Lazy DB factory ──
_db_factory = None
_active_runs: dict[str, tuple[int | None, int | None]] = {}

@worker_process_init.connect
def init_worker(**kwargs):
    global _db_factory
    from app.infrastructure.db.session import SessionLocal
    _db_factory = SessionLocal
    logger.info("Celery worker initialized — DB factory ready")


_active_runs: dict[str, tuple[int | None, int | None]] = {}
_overlap_locks_held: dict[str, str] = {}  # task_id → lock_key


def _release_overlap_lock(task_id: str) -> None:
    """Release overlap lock if this task held one. Safe no-op if not."""
    lock_key = _overlap_locks_held.pop(task_id, None)
    if lock_key:
        r = _get_redis_sync()
        if r:
            try:
                # Atomic compare-delete via Lua
                r.eval(
                    "if redis.call('GET', KEYS[1]) == ARGV[1] then return redis.call('DEL', KEYS[1]) else return 0 end",
                    1, lock_key, str(task_id),
                )
            except Exception:
                pass  # Redis down — lock will expire via TTL


def _get_db():
    """Get a new DB session."""
    if _db_factory is None:
        from app.infrastructure.db.session import SessionLocal
        return SessionLocal()
    return _db_factory()


# ═══════════════════════════════════════════════════════════
# Overlap Prevention — Redis lock per scheduled task
# ═══════════════════════════════════════════════════════════

def _get_redis_sync():
    """Synchronous Redis for Celery signals."""
    import redis
    url = os.getenv("REDIS_URL", "")
    if not url:
        return None
    try:
        return redis.from_url(url, socket_timeout=2, socket_connect_timeout=2)
    except Exception:
        return None

OVERLAP_LOCKS: dict[str, int] = {
    "workers.company_enrichment": 1800,     # 30m
    "workers.fact_verification": 86400,     # daily
    "workers.entity_resolution": 3600,      # 1h
    "workers.relationship_discovery": 1800,
    "workers.technology_detection": 1800,
    "workers.buying_signal_detector": 600,
    "workers.knowledge_decay": 7200,
    "workers.reasoning": 1800,
    "workers.timeline_generator": 3600,
    "workers.opportunity_scoring": 900,
    "workers.search_indexer": 3600,
    "workers.recommendation_engine": 1800,
    "workers.outbox_process_email": 30,
    "workers.knowledge_assessment_ingestion": 60,
    "workers.call_timeline_projection": 30,
    "workers.call_metrics_recalculation": 60,
    "workers.call_knowledge_ingestion": 60,
    "workers.email_timeline_projection": 30,
    "workers.email_metrics_recalculation": 60,
    "workers.imap_ingestion": 120,
    "workers.call_missed_call_recovery": 30,
    "workers.sms_missed_call_recovery": 30,
    "workers.sms_inbound_webhook": 30,
    "workers.operational_cleanup": 7200,
}


def _worker_name_from_task(task_name: str) -> str:
    return task_name.replace("workers.", "") if task_name.startswith("workers.") else task_name


class _UniqueTask(CeleryTask):
    """Task base that prevents overlapping scheduled runs via Redis lock.

    The lock is acquired in __call__ BEFORE the task body executes.
    Release happens in on_success/on_failure/after_return via atomic Lua.
    If Redis is down, the lock defaults to open (tasks run normally).
    Lock TTL ensures stale locks expire without manual intervention.
    """

    def __call__(self, *args, **kwargs):
        task_id = self.request.id
        task_name = self.name

        if task_id is not None and task_name.startswith("workers."):
            r = _get_redis_sync()
            if r:
                lock_ttl = OVERLAP_LOCKS.get(task_name, 60)
                lock_key = f"celery:overlap:{task_name}"
                acquired = r.set(lock_key, str(task_id), nx=True, ex=lock_ttl)
                if not acquired:
                    logger.info("Skipping overlapping run of %s (lock held)", task_name)
                    return {"skipped": "overlap", "task": task_name}
                _overlap_locks_held[task_id] = lock_key

        return super().__call__(*args, **kwargs)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        _release_overlap_lock(task_id)
        super().after_return(status, retval, task_id, args, kwargs, einfo)


celery_app.Task = _UniqueTask

# Scheduled pollers often find no work. Recording a job and run for every
# empty 15-second poll produced hundreds of thousands of audit rows. Direct
# event dispatches still carry an event/job identifier and remain tracked.
UNTRACKED_EMPTY_POLLERS = {
    "workers.outbox_process_email",
    "workers.knowledge_assessment_ingestion",
    "workers.call_timeline_projection",
    "workers.call_metrics_recalculation",
    "workers.call_knowledge_ingestion",
    "workers.call_missed_call_recovery",
    "workers.sms_missed_call_recovery",
    "workers.sms_inbound_webhook",
    "workers.email_timeline_projection",
    "workers.email_metrics_recalculation",
    "workers.outbox_process_assessment_lifecycle",
    "workers.imap_ingestion",
}


@task_prerun.connect
def _record_task_prerun(task_id=None, task=None, args=None, kwargs=None, **_extras):
    if task is None or not task.name.startswith("workers."):
        return
    payload = kwargs or {}
    if task.name in UNTRACKED_EMPTY_POLLERS and not any(
        payload.get(key) is not None for key in ("event_id", "job_id", "event_type")
    ):
        return
    db = _get_db()
    try:
        from app.application.workers.persistence import create_worker_job, ensure_worker_schedule, start_worker_run

        worker_name = _worker_name_from_task(task.name)
        queue_name = getattr(task.request, "delivery_info", {}).get("routing_key", "normal") if getattr(task, "request", None) else "normal"
        job_id = payload.get("job_id")
        if job_id is None:
            job = create_worker_job(
                db,
                worker_name=worker_name,
                queue_name=queue_name,
                trigger_type="schedule" if not payload.get("event_type") else "event",
                event_type=payload.get("event_type"),
                entity_type=payload.get("entity_type"),
                entity_id=payload.get("entity_id"),
                payload=payload,
                priority=queue_name,
                task_id=task_id,
            )
            job_id = job.id
        run = start_worker_run(db, worker_name=worker_name, task_id=task_id, job_id=job_id)
        _active_runs[task_id] = (job_id, run.id)
    finally:
        db.close()


@task_postrun.connect
def _record_task_postrun(task_id=None, task=None, retval=None, state=None, **_extras):
    if task is None or not task.name.startswith("workers."):
        return
    db = _get_db()
    try:
        from app.application.workers.persistence import finish_worker_run

        run_info = _active_runs.pop(task_id, (None, None))
        _job_id, run_id = run_info
        if run_id is not None:
            finish_worker_run(
                db,
                run_id=run_id,
                success=state == "SUCCESS",
                result=retval if isinstance(retval, dict) else {},
                error_message=None if state == "SUCCESS" else f"Task ended with state={state}",
            )
    finally:
        db.close()


@task_retry.connect
def _record_task_retry(request=None, reason=None, einfo=None, **_extras):
    if request is None or not request.task.startswith("workers."):
        return
    db = _get_db()
    try:
        from app.application.workers.persistence import record_worker_failure

        job_id, _run_id = _active_runs.get(request.id, (None, None))
        record_worker_failure(
            db,
            worker_name=_worker_name_from_task(request.task),
            task_id=request.id,
            job_id=job_id,
            error_type=type(reason).__name__ if reason else None,
            error_message=str(reason) if reason else "retry",
            traceback_text=str(einfo) if einfo else None,
            retry_count=int(getattr(request, "retries", 0)),
            payload=getattr(request, "kwargs", {}) if request else {},
            queue_name=getattr(request, "delivery_info", {}).get("routing_key", "normal"),
        )
    finally:
        db.close()


@celery_app.task(
    name="workers.operational_cleanup",
    bind=True,
    max_retries=0,
    queue="low",
)
def operational_cleanup(self, dry_run: bool = False, **_context):
    """Nightly retention for generated operational records only."""
    if os.getenv("OPERATIONAL_CLEANUP_ENABLED", "true").lower() not in ("true", "1", "yes"):
        return {"skipped": "disabled"}

    from operational_cleanup import cleanup_operational_history

    db = _get_db()
    try:
        result = cleanup_operational_history(db, dry_run=dry_run)
        logger.info("Operational cleanup complete: %s", result)
        return result
    except Exception:
        db.rollback()
        logger.exception("Operational cleanup failed")
        raise
    finally:
        db.close()


@task_failure.connect
def _record_task_failure(task_id=None, exception=None, traceback=None, sender=None, args=None, kwargs=None, einfo=None, **_extras):
    if sender is None or not sender.name.startswith("workers."):
        return
    db = _get_db()
    try:
        from app.application.workers.persistence import record_worker_failure

        job_id, _run_id = _active_runs.get(task_id, (None, None))
        request = getattr(sender, "request", None)
        record_worker_failure(
            db,
            worker_name=_worker_name_from_task(sender.name),
            task_id=task_id,
            job_id=job_id,
            error_type=type(exception).__name__ if exception else None,
            error_message=str(exception) if exception else "failure",
            traceback_text=str(einfo) if einfo else None,
            retry_count=int(getattr(request, "retries", 0)) if request else 0,
            payload=kwargs or {},
            queue_name=getattr(request, "delivery_info", {}).get("routing_key", "normal") if request else "normal",
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# WORKER 1 — COMPANY ENRICHMENT
# ═══════════════════════════════════════════════════════════

@celery_app.task(
    name="workers.company_enrichment",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
    queue="normal",
)
def company_enrichment(self, company_id: int | None = None, **context):
    """Enrich a company with fresh intelligence data."""
    db = _get_db()
    try:
        from app.application.knowledge.service import KnowledgeService
        from app.infrastructure.db.knowledge_graph import KnowledgeFact

        knowledge = KnowledgeService(db)

        if company_id:
            # Specific company enrichment
            facts = {
                "last_enriched_at": datetime.now(UTC).isoformat(),
                "enrichment_status": "completed",
            }
        else:
            # Bulk: find companies never enriched
            existing = db.query(KnowledgeFact).filter(
                KnowledgeFact.entity_type == "company",
                KnowledgeFact.key == "last_enriched_at",
            ).all()
            enriched_ids = {f.entity_id for f in existing}

            facts = {}
            # Will set enrichment marker for any unenriched companies
            if not enriched_ids:
                facts["enrichment_status"] = "pending_initial"

        for key, value in facts.items():
            target_id = company_id or 0
            try:
                knowledge.set_fact(
                    entity_type="company", entity_id=target_id,
                    key=key, value=value,
                    source="company_enrichment_worker", confidence=0.8,
                )
            except Exception:
                pass

        return {"enriched": True, "company_id": company_id, "facts_set": len(facts)}
    except Exception as exc:
        logger.error(f"Company enrichment failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# WORKER 2 — FACT VERIFICATION
# ═══════════════════════════════════════════════════════════

@celery_app.task(
    name="workers.fact_verification",
    bind=True,
    max_retries=0,
    default_retry_delay=60,
    queue="high",
)
def fact_verification(self, **context):
    """Verify facts by cross-referencing sources, adjust confidence."""
    db = _get_db()
    try:
        from app.infrastructure.db.knowledge_graph import KnowledgeFact

        facts = db.query(KnowledgeFact).filter(
            KnowledgeFact.confidence < 0.7,
        ).order_by(KnowledgeFact.confidence.asc()).limit(20).all()

        verified = 0
        for fact in facts:
            corroborated = db.query(KnowledgeFact).filter(
                KnowledgeFact.entity_type == fact.entity_type,
                KnowledgeFact.entity_id == fact.entity_id,
                KnowledgeFact.key == fact.key,
                KnowledgeFact.source != fact.source,
                KnowledgeFact.id != fact.id,
            ).first()

            fact.confidence = min(1.0, fact.confidence + 0.15) if corroborated else max(0.1, fact.confidence - 0.02)
            verified += 1

        # Commit once so a batch cannot create a burst of persistence events.
        if verified:
            db.commit()
        return {"verified": verified}
    except Exception as exc:
        logger.error(f"Fact verification failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# WORKER 3 — ENTITY RESOLUTION
# ═══════════════════════════════════════════════════════════

@celery_app.task(
    name="workers.entity_resolution",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    queue="normal",
)
def entity_resolution(self, **context):
    """Detect duplicate companies and flag for merging."""
    db = _get_db()
    try:
        from app.infrastructure.db.knowledge_graph import KnowledgeFact
        from app.application.knowledge.service import KnowledgeService

        knowledge = KnowledgeService(db)
        names = db.query(KnowledgeFact).filter(
            KnowledgeFact.entity_type == "company",
            KnowledgeFact.key == "name",
        ).all()

        seen: dict[str, list] = {}
        for f in names:
            n = f.value.lower().strip().rstrip(".")
            for s in [" inc", " ltd", " llc", " corp", " limited", " incorporated"]:
                n = n.replace(s, "")
            seen.setdefault(n, []).append(f)

        duplicates = 0
        for n, facts in seen.items():
            if len(facts) > 1:
                ids = set(f.entity_id for f in facts)
                if len(ids) > 1:
                    knowledge.set_fact(
                        entity_type="system", entity_id=0,
                        key="potential_duplicate",
                        value=f"companies:{','.join(map(str, sorted(ids)))}",
                        source="entity_resolution_worker", confidence=0.6,
                    )
                    duplicates += 1

        return {"duplicates_found": duplicates}
    except Exception as exc:
        logger.error(f"Entity resolution failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# WORKER 4-12 (condensed — production would have full implementations)
# ═══════════════════════════════════════════════════════════

@celery_app.task(name="workers.relationship_discovery", bind=True, max_retries=3, queue="normal")
def relationship_discovery(self, **context):
    """Discover relationships between entities."""
    db = _get_db()
    try:
        from app.infrastructure.db.knowledge_graph import KnowledgeFact
        from app.application.knowledge.service import KnowledgeService
        knowledge = KnowledgeService(db)
        contacts = db.query(KnowledgeFact).filter(
            KnowledgeFact.entity_type == "contact",
            KnowledgeFact.key == "company_name",
        ).limit(20).all()
        count = 0
        for fact in contacts:
            company = db.query(KnowledgeFact).filter(
                KnowledgeFact.entity_type == "company",
                KnowledgeFact.key == "name",
                KnowledgeFact.value == fact.value,
            ).first()
            if company:
                knowledge.add_relationship(
                    from_type="contact", from_id=fact.entity_id,
                    to_type="company", to_id=company.entity_id,
                    rel_type="works_for",
                    properties={"discovered_by": "relationship_discovery"},
                )
                count += 1
        return {"relationships_created": count}
    except Exception as exc:
        raise self.retry(exc=exc)
    finally:
        db.close()


KNOWN_TECH = ["QuickBooks", "Procore", "Jobber", "Buildertrend", "ServiceTitan",
              "Microsoft 365", "Google Workspace", "HubSpot", "Salesforce",
              "Azure", "AWS", "Cloudflare", "Slack", "Zoom", "Monday.com"]


@celery_app.task(name="workers.technology_detection", bind=True, max_retries=3, queue="normal")
def technology_detection(self, **context):
    """Detect technologies from facts and content."""
    db = _get_db()
    try:
        from app.infrastructure.db.knowledge_graph import KnowledgeFact
        from app.application.knowledge.service import KnowledgeService
        knowledge = KnowledgeService(db)
        facts = db.query(KnowledgeFact).filter(
            KnowledgeFact.entity_type.in_(["company", "signal", "lead"]),
            KnowledgeFact.created_at.isnot(None),
        ).order_by(KnowledgeFact.created_at.desc()).limit(50).all()
        count = 0
        for fact in facts:
            text = f"{fact.key} {fact.value}".lower()
            for tech in KNOWN_TECH:
                if tech.lower() in text:
                    knowledge.set_fact(entity_type=fact.entity_type, entity_id=fact.entity_id,
                                       key="uses_technology", value=tech,
                                       source="technology_detection", confidence=0.65)
                    count += 1
        return {"technologies_detected": count}
    except Exception as exc:
        raise self.retry(exc=exc)
    finally:
        db.close()


SIGNAL_KW = {
    "budget_approved": ["budget approved", "funding secured", "we have budget"],
    "urgent_need": ["urgent", "asap", "immediately", "this quarter"],
    "growing": ["growing fast", "expanding", "hiring", "scaling"],
    "digital_transformation": ["digital transformation", "modernize", "automate"],
    "manual_processes": ["manual process", "spreadsheet", "paper", "excel"],
    "evaluating": ["evaluating", "looking at", "comparing", "researching"],
    "replacing": ["replacing", "migrating from", "switching from"],
}


@celery_app.task(name="workers.buying_signal_detector", bind=True, max_retries=3, queue="high")
def buying_signal_detector(self, **context):
    """Detect buying signals from content."""
    db = _get_db()
    try:
        from app.infrastructure.db.knowledge_graph import KnowledgeFact
        from app.application.knowledge.service import KnowledgeService
        knowledge = KnowledgeService(db)
        facts = db.query(KnowledgeFact).filter(
            KnowledgeFact.entity_type.in_(["company", "signal", "transcript"]),
            KnowledgeFact.created_at.isnot(None),
        ).order_by(KnowledgeFact.created_at.desc()).limit(30).all()
        count = 0
        for fact in facts:
            text = f"{fact.key} {fact.value}".lower()
            for sig_type, keywords in SIGNAL_KW.items():
                for kw in keywords:
                    if kw in text:
                        knowledge.set_fact(entity_type=fact.entity_type, entity_id=fact.entity_id,
                                           key=f"buying_signal_{sig_type}", value="true",
                                           source="buying_signal_detector", confidence=0.6)
                        count += 1
                        break
        return {"signals_detected": count}
    except Exception as exc:
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(name="workers.knowledge_decay", bind=True, max_retries=3, queue="low")
def knowledge_decay(self, **context):
    """Age knowledge — reduce confidence on stale facts."""
    db = _get_db()
    try:
        from app.infrastructure.db.knowledge_graph import KnowledgeFact
        threshold = datetime.now(UTC) - timedelta(days=7)
        stale = db.query(KnowledgeFact).filter(
            KnowledgeFact.confidence > 0.2,
            KnowledgeFact.updated_at < threshold,
        ).order_by(KnowledgeFact.updated_at.asc()).limit(20).all()
        for fact in stale:
            days_old = (datetime.now(UTC) - fact.updated_at).days
            decay = min(0.05, days_old * 0.005)
            fact.confidence = max(0.1, fact.confidence - decay)
            db.commit()
        return {"decayed": len(stale)}
    except Exception as exc:
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(name="workers.reasoning", bind=True, max_retries=3, queue="normal")
def reasoning(self, **context):
    """Generate AI insights from graph patterns."""
    db = _get_db()
    try:
        from app.infrastructure.db.knowledge_graph import KnowledgeFact
        from app.application.knowledge.service import KnowledgeService
        knowledge = KnowledgeService(db)
        companies = db.query(KnowledgeFact).filter(
            KnowledgeFact.entity_type == "company",
        ).distinct(KnowledgeFact.entity_id).limit(20).all()
        seen = set()
        insights = 0
        for fact in companies:
            if fact.entity_id in seen:
                continue
            seen.add(fact.entity_id)
            facts = db.query(KnowledgeFact).filter(
                KnowledgeFact.entity_type == "company",
                KnowledgeFact.entity_id == fact.entity_id,
            ).all()
            fmap = {f.key: f.value for f in facts}
            values_lower = " ".join(str(v).lower() for v in fmap.values())
            if "hiring" in values_lower:
                knowledge.set_fact(entity_type="company", entity_id=fact.entity_id,
                                   key="insight_growth", value="Company showing hiring signals",
                                   source="reasoning", confidence=0.55)
                insights += 1
            has_manual = "manual" in values_lower or "spreadsheet" in values_lower
            has_growth = any(k.startswith("buying_signal_grow") for k in fmap)
            if has_manual and has_growth:
                knowledge.set_fact(entity_type="company", entity_id=fact.entity_id,
                                   key="insight_digital_transformation",
                                   value="Manual processes + growth signals",
                                   source="reasoning", confidence=0.6)
                insights += 1
        return {"insights_generated": insights}
    except Exception as exc:
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(name="workers.timeline_generator", bind=True, max_retries=3, queue="low")
def timeline_generator(self, **context):
    """Auto-build company history from events."""
    db = _get_db()
    try:
        from app.infrastructure.db.knowledge_graph import KnowledgeEvent
        from app.application.knowledge.service import KnowledgeService
        knowledge = KnowledgeService(db)
        events = db.query(KnowledgeEvent).filter(
            KnowledgeEvent.entity_type == "company",
        ).order_by(KnowledgeEvent.created_at.desc()).limit(50).all()
        for event in events:
            knowledge.set_fact(entity_type="company", entity_id=event.entity_id,
                               key=f"timeline_{event.event_type}",
                               value=event.description or event.event_type,
                               source="timeline_generator", confidence=0.95)
        return {"timeline_entries": len(events)}
    except Exception as exc:
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(name="workers.opportunity_scoring", bind=True, max_retries=3, queue="high")
def opportunity_scoring(self, **context):
    """Continuously score opportunities."""
    db = _get_db()
    try:
        from app.infrastructure.db.knowledge_graph import KnowledgeFact
        from app.application.knowledge.service import KnowledgeService
        knowledge = KnowledgeService(db)
        opps = db.query(KnowledgeFact).filter(
            KnowledgeFact.entity_type == "opportunity",
            KnowledgeFact.key == "status",
        ).limit(20).all()
        for opp in opps:
            facts = db.query(KnowledgeFact).filter(
                KnowledgeFact.entity_type == "opportunity",
                KnowledgeFact.entity_id == opp.entity_id,
            ).all()
            fmap = {f.key: f.value for f in facts}
            score = 50 + len([k for k in fmap if k.startswith("buying_signal_")]) * 10
            if any("budget" in k for k in fmap): score += 15
            if any("urgent" in str(v).lower() for v in fmap.values()): score += 20
            score = min(100, max(0, score))
            for key, val in [("opportunity_score", score), ("health_score", 70), ("risk_score", 30)]:
                knowledge.set_fact(entity_type="opportunity", entity_id=opp.entity_id,
                                   key=key, value=str(val),
                                   source="opportunity_scoring", confidence=0.7)
        return {"opportunities_scored": len(opps)}
    except Exception as exc:
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(name="workers.search_indexer", bind=True, max_retries=3, queue="background")
def search_indexer(self, **context):
    """Maintain semantic search index."""
    db = _get_db()
    try:
        from app.infrastructure.db.knowledge_graph import KnowledgeFact
        from app.application.knowledge.service import KnowledgeService
        knowledge = KnowledgeService(db)
        facts = db.query(KnowledgeFact).filter(
            KnowledgeFact.key == "search_indexed",
            KnowledgeFact.value == "false",
        ).limit(30).all()
        for fact in facts:
            fact.value = "true"
            db.commit()
        if facts:
            knowledge.set_fact(entity_type="system", entity_id=0,
                               key="search_index_size",
                               value=str(db.query(KnowledgeFact).count()),
                               source="search_indexer", confidence=1.0)
        return {"indexed": len(facts)}
    except Exception as exc:
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(name="workers.recommendation_engine", bind=True, max_retries=3, queue="normal")
def recommendation_engine(self, **context):
    """Generate actionable recommendations."""
    db = _get_db()
    try:
        from app.infrastructure.db.knowledge_graph import KnowledgeFact
        from app.application.knowledge.service import KnowledgeService
        knowledge = KnowledgeService(db)
        opps = db.query(KnowledgeFact).filter(
            KnowledgeFact.entity_type == "opportunity",
        ).distinct(KnowledgeFact.entity_id).limit(20).all()
        seen = set()
        recs = 0
        for opp in opps:
            if opp.entity_id in seen: continue
            seen.add(opp.entity_id)
            facts = db.query(KnowledgeFact).filter(
                KnowledgeFact.entity_type == "opportunity",
                KnowledgeFact.entity_id == opp.entity_id,
            ).all()
            fmap = {f.key: f.value for f in facts}
            has_signals = any(k.startswith("buying_signal_") for k in fmap)
            score = int(fmap.get("opportunity_score", "0"))
            rec = "monitor"
            if score >= 70 and has_signals: rec = "call_soon"
            elif 40 <= score < 70: rec = "research_more"
            knowledge.set_fact(entity_type="opportunity", entity_id=opp.entity_id,
                               key="recommendation", value=rec,
                               source="recommendation_engine", confidence=0.7)
            recs += 1
        return {"recommendations": recs}
    except Exception as exc:
        raise self.retry(exc=exc)
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# CELERY BEAT SCHEDULE
# ═══════════════════════════════════════════════════════════

celery_app.conf.beat_schedule = {
    # 11:15 UTC is approximately 3–4 a.m. in Vancouver, depending on DST.
    "operational-cleanup-nightly": {
        "task": "workers.operational_cleanup",
        "schedule": crontab(hour=11, minute=15),
        "options": {"queue": "low"},
    },
    "company-enrichment-every-30m": {
        "task": "workers.company_enrichment",
        "schedule": crontab(minute="*/30"),
        "options": {"queue": "normal"},
    },
    "fact-verification-daily": {
        "task": "workers.fact_verification",
        "schedule": crontab(hour=1, minute=30),
        "options": {"queue": "high"},
    },
    "entity-resolution-daily": {
        "task": "workers.entity_resolution",
        "schedule": crontab(hour=3, minute=0),
        "options": {"queue": "normal"},
    },
    "relationship-discovery-every-30m": {
        "task": "workers.relationship_discovery",
        "schedule": crontab(minute="*/30"),
        "options": {"queue": "normal"},
    },
    "technology-detection-every-30m": {
        "task": "workers.technology_detection",
        "schedule": crontab(minute="*/30"),
        "options": {"queue": "normal"},
    },
    "buying-signal-detector-every-10m": {
        "task": "workers.buying_signal_detector",
        "schedule": crontab(minute="*/10"),
        "options": {"queue": "high"},
    },
    "knowledge-decay-daily": {
        "task": "workers.knowledge_decay",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "low"},
    },
    "reasoning-every-30m": {
        "task": "workers.reasoning",
        "schedule": crontab(minute="*/30"),
        "options": {"queue": "normal"},
    },
    "timeline-generator-hourly": {
        "task": "workers.timeline_generator",
        "schedule": crontab(minute=0),
        "options": {"queue": "low"},
    },
    "opportunity-scoring-every-15m": {
        "task": "workers.opportunity_scoring",
        "schedule": crontab(minute="*/15"),
        "options": {"queue": "high"},
    },
    "search-indexer-hourly": {
        "task": "workers.search_indexer",
        "schedule": crontab(minute=30),
        "options": {"queue": "background"},
    },
    "recommendation-engine-every-30m": {
        "task": "workers.recommendation_engine",
        "schedule": crontab(minute="*/30"),
        "options": {"queue": "normal"},
    },
    # Outbox email — polls every 15s for pending email events
    "outbox-email-every-15s": {
        "task": "workers.outbox_process_email",
        "schedule": 15.0,
        "options": {"queue": "high"},
    },
    # Knowledge graph assessment ingestion — polls every 30s
    "knowledge-assessment-ingestion-every-30s": {
        "task": "workers.knowledge_assessment_ingestion",
        "schedule": 30.0,
        "options": {"queue": "normal"},
    },
    # Sprint 48.1 — Call outbox consumers (poll frequently)
    "call-timeline-projection-every-15s": {
        "task": "workers.call_timeline_projection",
        "schedule": 15.0,
        "options": {"queue": "high"},
    },
    "call-metrics-recalc-every-30s": {
        "task": "workers.call_metrics_recalculation",
        "schedule": 30.0,
        "options": {"queue": "normal"},
    },
    "call-kg-ingestion-every-30s": {
        "task": "workers.call_knowledge_ingestion",
        "schedule": 30.0,
        "options": {"queue": "normal"},
    },
    "missed-call-reconciliation-every-5s": {
        "task": "workers.call_missed_call_recovery",
        "schedule": 5.0,
        "options": {"queue": "high"},
    },
    "missed-call-sms-recovery-every-5s": {
        "task": "workers.sms_missed_call_recovery",
        "schedule": 5.0,
        "options": {"queue": "high"},
    },
    # Sprint 48.2 — Email projectors
    "email-timeline-projection-every-15s": {
        "task": "workers.email_timeline_projection",
        "schedule": 15.0,
        "options": {"queue": "high"},
    },
    "email-metrics-recalc-every-30s": {
        "task": "workers.email_metrics_recalculation",
        "schedule": 30.0,
        "options": {"queue": "normal"},
    },
    # Assessment lifecycle — polls every 30s for pending lifecycle events
    "assessment-lifecycle-every-30s": {
        "task": "workers.outbox_process_assessment_lifecycle",
        "schedule": 30.0,
        "options": {"queue": "high"},
    },
    # IMAP ingestion — polls every 60s for new inbound emails
    "imap-ingestion-every-60s": {
        "task": "workers.imap_ingestion",
        "schedule": 60.0,
        "options": {"queue": "normal"},
    },
}

# ── Queue definitions ──
celery_app.conf.task_routes = {
    "workers.*": {"queue": "normal"},
    "workers.outbox_process_email": {"queue": "high"},
    "workers.outbox_process_assessment_lifecycle": {"queue": "high"},
    "workers.call_missed_call_recovery": {"queue": "high"},
    "workers.sms_missed_call_recovery": {"queue": "high"},
}
celery_app.conf.task_queues = {
    "critical": {"exchange": "critical", "routing_key": "critical"},
    "high": {"exchange": "high", "routing_key": "high"},
    "normal": {"exchange": "normal", "routing_key": "normal"},
    "low": {"exchange": "low", "routing_key": "low"},
    "background": {"exchange": "background", "routing_key": "background"},
}


# ═══════════════════════════════════════════════════════════
# OUTBOX EMAIL WORKER — Sprint 47.7
# Processes assessment.internal_notification.requested and
# assessment.visitor_email.requested outbox events.
# Uses Zoho Mail SMTP. Idempotent — never double-sends.
# ═══════════════════════════════════════════════════════════

@celery_app.task(
    name="workers.outbox_process_email",
    bind=True,
    max_retries=5,
    default_retry_delay=30,
    queue="high",
)
def outbox_process_email(self, event_id: int | None = None, **context):
    """Process a single email outbox event. Consumes from outbox_events table."""

    db = _get_db()
    try:
        from app.infrastructure.db.models import OutboxEvent

        # Stale processing recovery: reset events stuck in "processing" longer
        # than STALE_PROCESSING_MINUTES back to "pending".  Leaves "failed"
        # events untouched, so old test failures are never automatically resent.
        stale_cutoff = datetime.now(UTC) - timedelta(minutes=STALE_PROCESSING_MINUTES)
        stale_events = db.query(OutboxEvent).filter(
            OutboxEvent.event_type.in_([
                "assessment.internal_notification.requested",
                "assessment.visitor_email.requested",
            ]),
            OutboxEvent.status == "processing",
            OutboxEvent.last_attempt_at < stale_cutoff,
        ).all()
        for se in stale_events:
            se.status = "pending"
            se.lease_holder = None
            se.leased_at = None
            logger.info("Stale email event reset to pending: event_id=%s type=%s", se.id, se.event_type)
        if stale_events:
            db.commit()

        # ── Fetch pending email events ──
        if event_id:
            events = [db.query(OutboxEvent).filter(OutboxEvent.id == event_id).first()]
        else:
            events = db.query(OutboxEvent).filter(
                OutboxEvent.event_type.in_([
                    "assessment.internal_notification.requested",
                    "assessment.visitor_email.requested",
                ]),
                OutboxEvent.status == "pending",
            ).order_by(OutboxEvent.created_at.asc()).limit(10).all()

        if not events:
            return {"processed": 0}

        smtp_config = {
            "host": os.getenv("SMTP_HOST", "smtp.zoho.com"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "user": os.getenv("SMTP_USER", ""),
            "password": os.getenv("SMTP_PASS", ""),
            "from_email": os.getenv("SMTP_FROM_EMAIL", "hello@pacificnorthsystems.com"),
            "from_name": os.getenv("SMTP_FROM_NAME", "Pacific North Systems"),
            "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
            "internal_email": os.getenv("INTERNAL_NOTIFICATION_EMAIL", "hello@pacificnorthsystems.com"),
            "resend_api_key": os.getenv("RESEND_API_KEY", ""),
        }

        if not smtp_config["resend_api_key"] and (
            not smtp_config["user"] or not smtp_config["password"]
        ):
            logger.warning("SMTP not configured — skipping email delivery")
            return {"processed": 0, "reason": "smtp_not_configured"}

        processed = 0
        for event in events:
            try:
                event.status = "processing"
                event.attempt_count += 1
                event.last_attempt_at = datetime.now(UTC)
                db.commit()

                payload = event.payload_json or {}

                if event.event_type == "assessment.visitor_email.requested":
                    _send_visitor_email(smtp_config, payload, db)
                elif event.event_type == "assessment.internal_notification.requested":
                    _send_internal_notification(smtp_config, payload, db)

                event.status = "completed"
                db.commit()
                processed += 1

                # ── Sprint 48.2: Log EmailMessage for every sent email ──
                _log_email_message(db, event.event_type, payload, smtp_config)
                db.commit()

                logger.info("Email sent: event_id=%s type=%s", event.id, event.event_type)

            except Exception as exc:
                db.rollback()
                event.status = "failed" if event.attempt_count >= event.max_attempts else "pending"
                event.last_error = str(exc)[:500]
                db.commit()
                logger.error("Email failed: event_id=%s attempt=%s error=%s", event.id, event.attempt_count, str(exc)[:200])
                if event.attempt_count < event.max_attempts:
                    raise self.retry(exc=exc, countdown=min(60 * (2 ** (event.attempt_count - 1)), 3600))

        return {"processed": processed}

    except Exception as exc:
        logger.error("Outbox email worker failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


def _send_visitor_email(smtp_config: dict, payload: dict, db):
    """Send enhanced assessment results to the visitor (Sprint 47.9)."""
    contact_email = payload.get("contact_email", "")
    contact_name = payload.get("contact_name", "there")
    company_name = payload.get("company_name", "your company")
    score = payload.get("automation_score", 0)
    interpretation = payload.get("score_interpretation", "")
    savings = payload.get("estimated_annual_savings", 0)
    weekly_hours = payload.get("estimated_weekly_hours", 0)
    primary_pain = payload.get("primary_pain_point", "")
    solutions = payload.get("recommended_solutions", [])

    if not contact_email:
        logger.warning("No visitor email in payload — skipping")
        return

    solutions_html = "".join(f"<li>{s}</li>" for s in solutions[:3]) if solutions else ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F4F6F8;font-family:system-ui,-apple-system,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden">
  <tr>
    <td style="background:#0B1526;padding:24px 32px">
      <h1 style="color:#fff;font-size:20px;margin:0;font-weight:700">Pacific North Systems</h1>
      <p style="color:#8B9DC3;font-size:13px;margin:4px 0 0">Your Business Efficiency Assessment</p>
    </td>
  </tr>
  <tr>
    <td style="padding:32px">
      <p style="margin:0 0 16px;font-size:16px;color:#1A1A2E">Hi {contact_name.split()[0] if contact_name else "there"},</p>
      <p style="margin:0 0 24px;font-size:15px;color:#3D3D5C;line-height:1.6">
        Thanks for completing the Business Efficiency Assessment for <strong>{company_name}</strong>.
        Here is a summary of what we found.
      </p>

      <!-- Score Card -->
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#F0F4FF;border-radius:10px;margin:0 0 24px">
        <tr>
          <td style="padding:20px 24px">
            <p style="margin:0 0 4px;font-size:12px;color:#526372;text-transform:uppercase;letter-spacing:.5px">Automation Opportunity Score</p>
            <p style="margin:0;font-size:36px;font-weight:700;color:#0B1526">{score}<span style="font-size:20px;color:#526372">/100</span></p>
            <p style="margin:8px 0 0;font-size:14px;color:#3D3D5C;line-height:1.5">{interpretation}</p>
          </td>
        </tr>
      </table>

      <!-- Key Findings -->
      <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 24px">
        <tr><td style="padding:0 0 12px"><h3 style="margin:0;font-size:16px;color:#0B1526">Key Findings</h3></td></tr>
        <tr><td style="padding:8px 0;border-bottom:1px solid #E8ECF0;font-size:14px;color:#3D3D5C"><strong>Primary pain point:</strong> {primary_pain}</td></tr>
        <tr><td style="padding:8px 0;border-bottom:1px solid #E8ECF0;font-size:14px;color:#3D3D5C"><strong>Weekly time opportunity:</strong> ~{weekly_hours} hours/week</td></tr>
        <tr><td style="padding:8px 0;border-bottom:1px solid #E8ECF0;font-size:14px;color:#3D3D5C"><strong>Estimated annual savings:</strong> ${savings:,} CAD</td></tr>
    """ + (f"""<tr><td style="padding:8px 0;font-size:14px;color:#3D3D5C"><strong>Recommended approach:</strong> {', '.join(solutions[:2])}</td></tr>""" if solutions else "") + f"""
      </table>

      <!-- CTA -->
      <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 16px">
        <tr>
          <td align="center">
            <a href="https://calendly.com/vinidias-pacificnorthsystems-operations-audit/30min" 
               style="display:inline-block;background:#0B1526;color:#fff;padding:14px 36px;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px">
               Book Your Free Operations Audit →
            </a>
          </td>
        </tr>
      </table>
      <p style="margin:0;font-size:13px;color:#526372;text-align:center">
        A 30-minute session to map your workflow and identify the highest-value improvements — no obligation.
      </p>
    </td>
  </tr>
  <tr>
    <td style="padding:20px 32px;border-top:1px solid #E8ECF0">
      <p style="margin:0;font-size:12px;color:#8B9DC3">
        Pacific North Systems · Vancouver, BC<br>
        <a href="https://pacificnorthsystems.com" style="color:#8B9DC3">pacificnorthsystems.com</a>
      </p>
    </td>
  </tr>
</table>
</body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Your Operations Assessment Results — {company_name}"
    msg["From"] = f"{smtp_config['from_name']} <{smtp_config['from_email']}>"
    msg["To"] = contact_email
    msg.attach(MIMEText(html, "html"))

    _send_email(smtp_config, msg)


def _send_internal_notification(smtp_config: dict, payload: dict, db):
    """Send rich internal notification with full sales intelligence (Sprint 47.9)."""
    internal_email = smtp_config.get("internal_email", "hello@pacificnorthsystems.com")
    company = payload.get("company_name", "Unknown")
    contact_name = payload.get("contact_name", "")
    contact_email = payload.get("contact_email", "")
    contact_phone = payload.get("contact_phone", "")
    industry = payload.get("industry", "")
    employee_range = payload.get("employee_range", "")
    lead_priority = payload.get("lead_priority", "medium")
    lead_score = payload.get("lead_score", 0)
    answers = payload.get("answers", {})
    results = payload.get("results", {})
    intelligence = payload.get("intelligence", {})
    assessment_id = payload.get("assessment_id", "")

    score = intelligence.get("automation_score", results.get("opportunityScore", 0))
    interpretation = intelligence.get("score_interpretation", "")
    savings = intelligence.get("estimated_annual_savings", 0)
    labour_cost = intelligence.get("estimated_annual_labour_cost", 0)
    weekly_hours = intelligence.get("estimated_weekly_hours", 0)
    annual_hours = intelligence.get("estimated_annual_hours", 0)
    primary_pain = intelligence.get("primary_pain_point", "")
    current_process = intelligence.get("current_process_summary", "")
    solutions = intelligence.get("recommended_solution_categories", [])
    reasons = intelligence.get("recommendation_reasons", [])
    urgency = intelligence.get("urgency", "unknown")
    urgency_msg = intelligence.get("urgency_message", "")
    buying_signals = intelligence.get("buying_signals", [])
    root_cause = intelligence.get("root_cause", "")
    business_impact = intelligence.get("business_impact", "")
    decision_maker = intelligence.get("likely_decision_maker", "")
    project_size = intelligence.get("project_size_band", "")
    next_action = intelligence.get("next_best_action", "")
    questions = intelligence.get("discovery_questions", [])
    lead_reasons = payload.get("lead_reasons", [])

    # Priority badge styling
    pri_colors = {"high": ("#DC2626", "#FEF2F2"), "medium": ("#D97706", "#FFFBEB"), "low": ("#059669", "#ECFDF5")}
    pri_color, pri_bg = pri_colors.get(lead_priority, ("#526372", "#F4F6F8"))

    # Main problems list
    main_problems = answers.get("mainProblems", answers.get("main_problems", []))
    problems_text = ", ".join(main_problems) if main_problems else "—"
    weekly_time = answers.get("weeklyTimeSpent", answers.get("weekly_time_spent", "—"))
    people = answers.get("peopleInvolved", answers.get("people_involved", "—"))
    additional = answers.get("additionalDetails", answers.get("additional_details", ""))

    # Solutions with reasons
    solutions_rows = ""
    for i, sol in enumerate(solutions[:4]):
        reason = reasons[i] if i < len(reasons) else ""
        solutions_rows += f'<tr><td style="padding:6px 12px;font-size:13px;color:#1A1A2E"><strong>{sol}</strong></td><td style="padding:6px 12px;font-size:12px;color:#526372">{reason[:100]}</td></tr>\n'

    # Buying signals
    signals_html = "".join(f'<li style="font-size:13px;color:#3D3D5C;margin-bottom:4px">{s}</li>' for s in buying_signals[:3])

    # Discovery questions
    questions_html = "".join(f'<li style="font-size:13px;color:#3D3D5C;margin-bottom:6px;line-height:1.5">"{q}"</li>' for q in questions[:5])

    # Lead reasons
    reasons_html = "".join(f'<li style="font-size:13px;color:#3D3D5C;margin-bottom:3px">{r}</li>' for r in lead_reasons)

    crm_app_url = os.getenv("CRM_APP_URL", "http://localhost:3000")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F4F6F8;font-family:system-ui,-apple-system,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:640px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden">
  <!-- Header -->
  <tr>
    <td style="background:#0B1526;padding:20px 28px">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td><h1 style="color:#fff;font-size:18px;margin:0;font-weight:700">Pacific North Systems</h1></td>
          <td align="right"><span style="display:inline-block;background:{pri_bg};color:{pri_color};padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;text-transform:uppercase">{lead_priority} Priority</span></td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- Subject Line -->
  <tr>
    <td style="padding:20px 28px 0">
      <h2 style="margin:0;font-size:18px;color:#0B1526">New Assessment Lead — {company} — Score {score}/100</h2>
    </td>
  </tr>

  <!-- ═══ LEAD SUMMARY ═══ -->
  <tr>
    <td style="padding:24px 28px 12px">
      <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #E8ECF0;border-radius:8px">
        <tr><td style="background:#F8FAFB;padding:10px 16px;border-radius:8px 8px 0 0"><h3 style="margin:0;font-size:13px;color:#0B1526;text-transform:uppercase;letter-spacing:.5px">Lead Summary</h3></td></tr>
        <tr><td style="padding:12px 16px">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr><td style="padding:3px 0;font-size:13px;color:#526372;width:120px">Company</td><td style="padding:3px 0;font-size:13px;color:#1A1A2E"><strong>{company}</strong></td></tr>
            <tr><td style="padding:3px 0;font-size:13px;color:#526372">Contact</td><td style="padding:3px 0;font-size:13px;color:#1A1A2E">{contact_name}</td></tr>
            <tr><td style="padding:3px 0;font-size:13px;color:#526372">Email</td><td style="padding:3px 0;font-size:13px;color:#1A1A2E"><a href="mailto:{contact_email}" style="color:#0B1526">{contact_email}</a></td></tr>
            <tr><td style="padding:3px 0;font-size:13px;color:#526372">Phone</td><td style="padding:3px 0;font-size:13px;color:#1A1A2E">{contact_phone or "—"}</td></tr>
            <tr><td style="padding:3px 0;font-size:13px;color:#526372">Industry</td><td style="padding:3px 0;font-size:13px;color:#1A1A2E">{industry or "—"}</td></tr>
            <tr><td style="padding:3px 0;font-size:13px;color:#526372">Company size</td><td style="padding:3px 0;font-size:13px;color:#1A1A2E">{employee_range or "—"}</td></tr>
            <tr><td style="padding:3px 0;font-size:13px;color:#526372">Lead score</td><td style="padding:3px 0;font-size:13px;color:#1A1A2E"><strong>{lead_score}/100</strong></td></tr>
            <tr><td style="padding:3px 0;font-size:13px;color:#526372">Source</td><td style="padding:3px 0;font-size:13px;color:#1A1A2E">Website Assessment</td></tr>
          </table>
        </td></tr>
      </table>
    </td>
  </tr>

  <!-- ═══ ASSESSMENT SUMMARY ═══ -->
  <tr>
    <td style="padding:12px 28px">
      <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #E8ECF0;border-radius:8px">
        <tr><td style="background:#F8FAFB;padding:10px 16px;border-radius:8px 8px 0 0"><h3 style="margin:0;font-size:13px;color:#0B1526;text-transform:uppercase;letter-spacing:.5px">Assessment Summary</h3></td></tr>
        <tr><td style="padding:12px 16px">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr><td style="padding:3px 0;font-size:13px;color:#526372;width:140px">Opportunity score</td><td style="padding:3px 0;font-size:14px;color:#0B1526"><strong>{score}/100</strong></td></tr>
            <tr><td style="padding:3px 0;font-size:13px;color:#526372">Interpretation</td><td style="padding:3px 0;font-size:13px;color:#3D3D5C">{interpretation}</td></tr>
            <tr><td style="padding:3px 0;font-size:13px;color:#526372">Primary problems</td><td style="padding:3px 0;font-size:13px;color:#1A1A2E">{problems_text}</td></tr>
            <tr><td style="padding:3px 0;font-size:13px;color:#526372">Current process</td><td style="padding:3px 0;font-size:13px;color:#1A1A2E">{current_process}</td></tr>
            <tr><td style="padding:3px 0;font-size:13px;color:#526372">Weekly time spent</td><td style="padding:3px 0;font-size:13px;color:#1A1A2E">{weekly_time}</td></tr>
            <tr><td style="padding:3px 0;font-size:13px;color:#526372">People involved</td><td style="padding:3px 0;font-size:13px;color:#1A1A2E">{people}</td></tr>
        """ + (f'<tr><td style="padding:3px 0;font-size:13px;color:#526372">Additional</td><td style="padding:3px 0;font-size:13px;color:#3D3D5C">{additional[:200]}</td></tr>' if additional else "") + f"""
          </table>
        </td></tr>
      </table>
    </td>
  </tr>

  <!-- ═══ ESTIMATED OPPORTUNITY ═══ -->
  <tr>
    <td style="padding:12px 28px">
      <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #E8ECF0;border-radius:8px">
        <tr><td style="background:#F8FAFB;padding:10px 16px;border-radius:8px 8px 0 0"><h3 style="margin:0;font-size:13px;color:#0B1526;text-transform:uppercase;letter-spacing:.5px">Estimated Opportunity</h3></td></tr>
        <tr><td style="padding:12px 16px">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr><td style="padding:3px 0;font-size:13px;color:#526372;width:160px">Est. weekly hours</td><td style="padding:3px 0;font-size:13px;color:#1A1A2E">{weekly_hours}</td></tr>
            <tr><td style="padding:3px 0;font-size:13px;color:#526372">Est. annual hours</td><td style="padding:3px 0;font-size:13px;color:#1A1A2E">{annual_hours:,}</td></tr>
            <tr><td style="padding:3px 0;font-size:13px;color:#526372">Est. annual labour cost</td><td style="padding:3px 0;font-size:13px;color:#1A1A2E">${labour_cost:,} CAD</td></tr>
            <tr><td style="padding:3px 0;font-size:13px;color:#526372"><strong>Est. annual savings</strong></td><td style="padding:3px 0;font-size:14px;color:#059669"><strong>${savings:,} CAD</strong></td></tr>
          </table>
        </td></tr>
      </table>
    </td>
  </tr>

  <!-- ═══ RECOMMENDED PNS SOLUTIONS ═══ -->
  <tr>
    <td style="padding:12px 28px">
      <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #E8ECF0;border-radius:8px">
        <tr><td style="background:#F8FAFB;padding:10px 16px;border-radius:8px 8px 0 0"><h3 style="margin:0;font-size:13px;color:#0B1526;text-transform:uppercase;letter-spacing:.5px">Recommended PNS Solutions</h3></td></tr>
        <tr><td style="padding:8px 16px">
          <table width="100%" cellpadding="0" cellspacing="0">{solutions_rows}</table>
        </td></tr>
      </table>
    </td>
  </tr>

  <!-- ═══ SALES INTELLIGENCE ═══ -->
  <tr>
    <td style="padding:12px 28px">
      <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #E8ECF0;border-radius:8px">
        <tr><td style="background:#F8FAFB;padding:10px 16px;border-radius:8px 8px 0 0"><h3 style="margin:0;font-size:13px;color:#0B1526;text-transform:uppercase;letter-spacing:.5px">Sales Intelligence</h3></td></tr>
        <tr><td style="padding:12px 16px">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr><td style="padding:3px 0;font-size:13px;color:#526372;width:160px">Primary pain point</td><td style="padding:3px 0;font-size:13px;color:#1A1A2E"><strong>{primary_pain}</strong></td></tr>
            <tr><td style="padding:4px 0;font-size:13px;color:#526372">Likely root cause</td><td style="padding:4px 0;font-size:13px;color:#3D3D5C">{root_cause[:180]}</td></tr>
            <tr><td style="padding:4px 0;font-size:13px;color:#526372">Business impact</td><td style="padding:4px 0;font-size:13px;color:#3D3D5C">{business_impact[:180]}</td></tr>
            <tr><td style="padding:3px 0;font-size:13px;color:#526372">Decision-maker role</td><td style="padding:3px 0;font-size:13px;color:#1A1A2E">{decision_maker}</td></tr>
            <tr><td style="padding:3px 0;font-size:13px;color:#526372">Urgency</td><td style="padding:3px 0;font-size:13px;color:#1A1A2E"><strong>{urgency.upper()}</strong> — {urgency_msg}</td></tr>
            <tr><td style="padding:3px 0;font-size:13px;color:#526372">Project size band</td><td style="padding:3px 0;font-size:13px;color:#1A1A2E">{project_size}</td></tr>
            <tr><td style="padding:3px 0;font-size:13px;color:#526372;vertical-align:top">Buying signals</td><td style="padding:3px 0;font-size:13px;color:#3D3D5C"><ul style="margin:4px 0;padding-left:18px">{signals_html or '<li>Initial inquiry</li>'}</ul></td></tr>
            <tr><td style="padding:3px 0;font-size:13px;color:#526372;vertical-align:top">Lead priority reasons</td><td style="padding:3px 0;font-size:13px;color:#3D3D5C"><ul style="margin:4px 0;padding-left:18px">{reasons_html}</ul></td></tr>
            <tr><td style="padding:8px 0 0;font-size:14px;color:#0B1526"><strong>Suggested next action:</strong> {next_action}</td></tr>
          </table>
        </td></tr>
      </table>
    </td>
  </tr>

  <!-- ═══ DISCOVERY QUESTIONS ═══ -->
  <tr>
    <td style="padding:12px 28px">
      <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #E8ECF0;border-radius:8px">
        <tr><td style="background:#F8FAFB;padding:10px 16px;border-radius:8px 8px 0 0"><h3 style="margin:0;font-size:13px;color:#0B1526;text-transform:uppercase;letter-spacing:.5px">Discovery Questions</h3></td></tr>
        <tr><td style="padding:12px 16px"><ol style="margin:0;padding-left:18px">{questions_html}</ol></td></tr>
      </table>
    </td>
  </tr>

  <!-- ═══ CRM ACTIONS ═══ -->
  <tr>
    <td style="padding:20px 28px">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="padding-right:10px">
            <a href="{crm_app_url}/leads" style="display:inline-block;background:#0B1526;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:600">View in CRM →</a>
          </td>
          <td style="padding-right:10px">
            <a href="mailto:{contact_email}" style="display:inline-block;background:#3D3D5C;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:600">Email Contact</a>
          </td>
          <td>
            <a href="https://calendly.com/vinidias-pacificnorthsystems-operations-audit/30min" style="display:inline-block;background:#059669;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:600">Book Follow-up</a>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- Footer -->
  <tr>
    <td style="padding:16px 28px;border-top:1px solid #E8ECF0;background:#F8FAFB;border-radius:0 0 12px 12px">
      <p style="margin:0;font-size:11px;color:#8B9DC3">
        Assessment ID: {assessment_id} · Generated by PNS Assessment Intelligence v1.0<br>
        <span style="color:#526372">Rule-based intelligence · AI enrichment pending</span>
      </p>
    </td>
  </tr>
</table>
</body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"New Assessment Lead — {company} — Score {score}/100"
    msg["From"] = f"{smtp_config['from_name']} <{smtp_config['from_email']}>"
    msg["To"] = internal_email
    # ── Policy A: X-PNS headers for IMAP filtering ──
    msg["X-PNS-Message-Type"] = "assessment-internal-notification"
    msg["X-PNS-System-Generated"] = "true"
    msg["X-PNS-Correlation-ID"] = assessment_id or ""
    msg.attach(MIMEText(html, "html"))

    _send_email(smtp_config, msg)


def _send_email(config: dict, msg):
    """Send through an HTTPS provider when configured, otherwise use SMTP."""
    if config.get("resend_api_key"):
        html = ""
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                html = payload.decode(part.get_content_charset() or "utf-8") if payload else ""
                break

        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {config['resend_api_key']}",
                "Content-Type": "application/json",
                "User-Agent": "PacificNorthSystems-CRM/1.0",
            },
            json={
                "from": str(msg["From"]),
                "to": [str(msg["To"])],
                "subject": str(msg["Subject"]),
                "html": html,
            },
            timeout=15,
        )
        response.raise_for_status()
        return

    import ssl
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(config["host"], config["port"], timeout=30, context=ctx) as server:
        server.login(config["user"], config["password"])
        server.send_message(msg)


def _log_email_message(db, event_type: str, payload: dict, smtp_config: dict):
    """Sprint 48.2: Persist sent email as EmailMessage + emit projection outbox events."""
    import uuid as _uuid
    from datetime import UTC as _UTC, datetime as _dt
    from app.infrastructure.db.models import EmailMessage, OutboxEvent

    contact_email = payload.get("contact_email", "")
    from_addr = smtp_config.get("from_email", "")
    company_name = payload.get("company_name", "")

    try:
        # Resolve company by name (best-effort)
        from app.infrastructure.db.models import Company
        company = db.query(Company).filter(Company.name == company_name).first()

        email = EmailMessage(
            public_uuid=str(_uuid.uuid4()),
            organization_id=1,
            company_id=company.id if company else None,
            direction="outbound",
            status="sent",
            delivery_status="delivered",
            from_address=from_addr,
            normalized_from=from_addr.lower(),
            to_address=contact_email,
            subject=f"Assessment notification for {company_name}",
            provider="zoho",
            provider_message_id=f"pns-{_uuid.uuid4().hex[:16]}",
            sent_at=_dt.now(_UTC),
            correlation_id=payload.get("assessment_id", ""),
        )
        if event_type == "assessment.internal_notification.requested":
            email.subject = f"New Assessment Lead — {company_name}"
            email.to_address = smtp_config.get("internal_email", from_addr)
        elif event_type == "assessment.visitor_email.requested":
            email.subject = f"Your Operations Assessment Results — {company_name}"
            email.to_address = contact_email

        db.add(email)
        db.flush()

        # Emit projection events
        for evt_type in ["email.timeline_projection.requested", "email.metrics_recalculation.requested"]:
            db.add(OutboxEvent(event_type=evt_type, payload_json={
                "email_uuid": email.public_uuid, "company_id": email.company_id,
                "contact_email": contact_email, "direction": "outbound",
                "correlation_id": email.correlation_id,
            }))

        logger.info("EmailMessage logged: uuid=%s company=%s", email.public_uuid, company_name)
    except Exception as exc:
        logger.warning("Failed to log EmailMessage: %s", exc)


# ═══════════════════════════════════════════════════════════
# SPRINT 48.2 — EMAIL PROJECTOR WORKERS
# ═══════════════════════════════════════════════════════════

@celery_app.task(name="workers.email_timeline_projection", bind=True, max_retries=3, default_retry_delay=30, queue="high")
def email_timeline_projection(self, event_id: int | None = None, **context):
    """Project sent/received emails into timeline."""
    db = _get_db()
    try:
        events = _fetch_outbox_events(db, "email.timeline_projection.requested", event_id)
        processed = 0
        for event in events:
            try:
                event.status = "processing"; event.attempt_count += 1; event.last_attempt_at = datetime.now(UTC); db.commit()
                payload = event.payload_json or {}
                from app.infrastructure.db.models import Activity, Conversation, EmailMessage
                email = db.query(EmailMessage).filter(
                    EmailMessage.public_uuid == payload.get("email_uuid")
                ).first()
                if email and email.company_id:
                    conv = db.query(Conversation).filter(
                        Conversation.organization_id == email.organization_id,
                        Conversation.company_id == email.company_id,
                        Conversation.status == "active",
                    ).order_by(Conversation.updated_at.desc()).first()
                    if not conv:
                        conv = Conversation(
                            organization_id=email.organization_id,
                            company_id=email.company_id,
                            primary_contact_id=email.contact_id,
                            status="active",
                            relationship_stage="contacted",
                            last_activity_at=email.sent_at or email.received_at or email.created_at,
                        )
                        db.add(conv)
                        db.flush()
                    email.conversation_id = conv.id
                    if not conv.primary_contact_id and email.contact_id:
                        conv.primary_contact_id = email.contact_id
                    conv.last_activity_at = email.sent_at or email.received_at or email.created_at
                    if conv.relationship_stage == "new":
                        conv.relationship_stage = "contacted"
                    if not email.activity_id:
                        activity = Activity(
                            organization_id=email.organization_id,
                            company_id=email.company_id,
                            contact_id=email.contact_id,
                            conversation_id=conv.id,
                            activity_type="email",
                            subject=email.subject,
                            body=email.plain_text,
                            created_at=email.sent_at or email.received_at or email.created_at,
                        )
                        db.add(activity)
                        db.flush()
                        email.activity_id = activity.id
                from app.infrastructure.db.knowledge_graph import KnowledgeEvent
                ke = KnowledgeEvent(
                    entity_type="company", entity_id=payload.get("company_id", 0) or 0,
                    event_type="email_sent",
                    description=f"Email sent to {payload.get('contact_email', '')}. Direction: {payload.get('direction', 'outbound')}."
                )
                db.add(ke)
                event.status = "completed"; db.commit(); processed += 1
            except Exception as exc:
                db.rollback(); _mark_event_failed(db, event, exc)
        return {"processed": processed}
    except Exception as exc: raise self.retry(exc=exc)
    finally: db.close()


@celery_app.task(name="workers.email_metrics_recalculation", bind=True, max_retries=3, default_retry_delay=30, queue="normal")
def email_metrics_recalculation(self, event_id: int | None = None, **context):
    """Recalculate email counts for conversation metrics."""
    db = _get_db()
    try:
        events = _fetch_outbox_events(db, "email.metrics_recalculation.requested", event_id)
        processed = 0
        for event in events:
            try:
                event.status = "processing"; event.attempt_count += 1; event.last_attempt_at = datetime.now(UTC); db.commit()
                payload = event.payload_json or {}
                company_id = payload.get("company_id")
                if company_id:
                    from app.infrastructure.db.models import EmailMessage, Conversation
                    email_count = db.query(EmailMessage).filter(EmailMessage.company_id == company_id).count()
                    conv = db.query(Conversation).filter(Conversation.company_id == company_id).first()
                    if conv:
                        existing = conv.summary or ""
                        conv.summary = f"{existing} Emails: {email_count}." if existing else f"Emails: {email_count}."
                event.status = "completed"; db.commit(); processed += 1
            except Exception as exc:
                db.rollback(); _mark_event_failed(db, event, exc)
        return {"processed": processed}
    except Exception as exc: raise self.retry(exc=exc)
    finally: db.close()


# ═══════════════════════════════════════════════════════════
# SPRINT 48.2 — IMAP INGESTION WORKER (Zoho Mail)
# Polls Zoho Mail IMAP for inbound emails, creates EmailMessage
# records, resolves entities, and queues projection events.
# ═══════════════════════════════════════════════════════════

@celery_app.task(
    name="workers.imap_ingestion",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
    queue="normal",
)
def imap_ingestion(self, **context):
    """Poll Zoho Mail IMAP for new inbound emails. Idempotent by UID."""
    db = _get_db()
    try:
        imap_host = os.getenv("IMAP_HOST", "imap.zohocloud.ca")
        imap_port = int(os.getenv("IMAP_PORT", "993"))
        imap_user = os.getenv("SMTP_USER", "")
        imap_pass = os.getenv("SMTP_PASS", "")

        if not imap_user or not imap_pass:
            return {"processed": 0, "reason": "IMAP not configured"}

        import ssl
        ctx = ssl.create_default_context()
        mail = imaplib.IMAP4_SSL(imap_host, imap_port, ssl_context=ctx, timeout=30)
        mail.login(imap_user, imap_pass)
        mail.select("INBOX")

        # Search for unseen emails (last 10)
        status, data = mail.search(None, "UNSEEN")
        if status != "OK" or not data[0]:
            mail.logout()
            return {"processed": 0}

        uids = data[0].split()[-10:]  # Last 10 unseen
        processed = 0

        for uid in uids:
            try:
                status, msg_data = mail.fetch(uid, "(RFC822)")
                if status != "OK":
                    continue

                raw = email_lib.message_from_bytes(msg_data[0][1])
                from_addr = raw.get("From", "")
                subject = raw.get("Subject", "")
                in_reply_to = raw.get("In-Reply-To", "")
                references = raw.get("References", "")
                message_id = raw.get("Message-ID", "")

                # Extract normalized from address
                from_email = _extract_email(from_addr) or from_addr

                # ── Policy A: Detect system-generated PNS emails ──
                is_system = (
                    raw.get("X-PNS-System-Generated", "").lower() == "true" or
                    raw.get("X-PNS-Message-Type", "") == "assessment-internal-notification"
                )
                pns_correlation_id = raw.get("X-PNS-Correlation-ID", "")

                # Idempotency check
                from app.infrastructure.db.models import EmailMessage
                existing = db.query(EmailMessage).filter(
                    (EmailMessage.internet_message_id == message_id) |
                    (EmailMessage.provider_message_id == uid.decode())
                ).first()
                if existing:
                    continue

                # Resolve entity (skip CRM linking for system emails)
                if is_system:
                    company_id, contact_id = None, None
                else:
                    company_id, contact_id = _resolve_email_entity(db, from_email)

                # Create EmailMessage
                import uuid as _uuid
                email_record = EmailMessage(
                    public_uuid=str(_uuid.uuid4()),
                    organization_id=1,
                    company_id=company_id,
                    contact_id=contact_id,
                    direction="inbound",
                    status="received" if not is_system else "received-internal",
                    from_address=from_addr[:255],
                    normalized_from=from_email[:255] if from_email else None,
                    to_address=raw.get("To", ""),
                    subject=subject[:500] if subject else None,
                    provider="zoho",
                    provider_message_id=uid.decode(),
                    internet_message_id=message_id[:500] if message_id else None,
                    in_reply_to=in_reply_to[:500] if in_reply_to else None,
                    references=references[:1000] if references else None,
                    received_at=datetime.now(UTC),
                    correlation_id=pns_correlation_id or str(_uuid.uuid4()),
                )
                db.add(email_record)
                db.flush()

                # Policy A: Only emit CRM projection events for non-system emails
                if not is_system and company_id:
                    from app.infrastructure.db.models import OutboxEvent
                    for evt_type in ["email.timeline_projection.requested", "email.metrics_recalculation.requested"]:
                        db.add(OutboxEvent(event_type=evt_type, payload_json={
                            "email_uuid": email_record.public_uuid, "company_id": company_id,
                            "contact_email": from_email, "direction": "inbound",
                            "correlation_id": email_record.correlation_id,
                        }))

                db.commit()
                processed += 1
                if is_system:
                    logger.info("IMAP ingested internal: from=%s type=%s", from_email, raw.get("X-PNS-Message-Type", "unknown"))
                else:
                    logger.info("IMAP ingested: from=%s subject=%s company=%s", from_email, subject, company_id)

            except Exception as exc:
                db.rollback()
                logger.warning("IMAP ingestion failed for uid %s: %s", uid.decode() if uid else "?", str(exc)[:100])

        mail.logout()
        return {"processed": processed}
    except Exception as exc:
        logger.error("IMAP worker failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


def _extract_email(from_header: str) -> str | None:
    """Extract email address from a From header like 'Name <email>'."""
    import re
    match = re.search(r'<([^>]+)>', from_header)
    if match:
        return match.group(1).strip().lower()
    # Fallback: just the email
    if "@" in from_header:
        return from_header.strip().lower()
    return None


def _resolve_email_entity(db, email_addr: str) -> tuple[int | None, int | None]:
    """Resolve an email address to Company + Contact."""
    from app.infrastructure.db.models import Contact, Company
    if not email_addr:
        return None, None
    normalized = email_addr.lower().strip()
    contact = db.query(Contact).filter(
        Contact.email == normalized, Contact.status == "active"
    ).first()
    if contact:
        return contact.company_id, contact.id
    # Try domain-level company match
    domain = normalized.split("@")[1] if "@" in normalized else None
    if domain:
        company = db.query(Company).filter(
            Company.website.ilike(f"%{domain}%"), Company.is_archived == False
        ).first()
        if company:
            return company.id, None
    return None, None


# ═══════════════════════════════════════════════════════════
# KNOWLEDGE GRAPH INGESTION WORKER — Sprint 47.9
# Writes assessment facts to the knowledge graph.
# ═══════════════════════════════════════════════════════════

@celery_app.task(
    name="workers.knowledge_assessment_ingestion",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="normal",
)
def knowledge_assessment_ingestion(self, event_id: int | None = None, **context):
    """Write assessment intelligence facts to the knowledge graph."""
    db = _get_db()
    try:
        from app.infrastructure.db.models import OutboxEvent
        from app.infrastructure.db.knowledge_graph import KnowledgeFact
        from app.application.knowledge.service import KnowledgeService

        if event_id:
            events = [db.query(OutboxEvent).filter(OutboxEvent.id == event_id).first()]
        else:
            events = db.query(OutboxEvent).filter(
                OutboxEvent.event_type == "knowledge.assessment_ingestion.requested",
                OutboxEvent.status == "pending",
            ).order_by(OutboxEvent.created_at.asc()).limit(10).all()

        if not events:
            return {"processed": 0}

        knowledge = KnowledgeService(db)
        processed = 0

        for event in events:
            try:
                event.status = "processing"
                event.attempt_count += 1
                event.last_attempt_at = datetime.now(UTC)
                db.commit()

                payload = event.payload_json or {}
                intelligence = payload.get("intelligence", {})
                company_id = payload.get("company_id", 0)
                assessment_id = payload.get("assessment_id", "")

                facts_to_write = [
                    ("has_assessment", assessment_id, "website_assessment", 1.0, "submitted"),
                    ("primary_pain_point", intelligence.get("primary_pain_point", ""), "website_assessment", 0.9, "submitted"),
                    ("estimated_annual_savings", str(intelligence.get("estimated_annual_savings", 0)), "website_assessment", 0.85, "calculated"),
                    ("automation_score", str(intelligence.get("automation_score", 0)), "website_assessment", 0.85, "calculated"),
                    ("recommended_solution", ", ".join(intelligence.get("recommended_solution_categories", [])[:2]), "website_assessment", 0.8, "inferred"),
                    ("lead_source", "website_assessment", "website_assessment", 1.0, "submitted"),
                    ("project_size_band", intelligence.get("project_size_band", ""), "website_assessment", 0.75, "inferred"),
                    ("urgency", intelligence.get("urgency", ""), "website_assessment", 0.8, "inferred"),
                ]

                for key, value, source, confidence, fact_type in facts_to_write:
                    if value:
                        knowledge.set_fact(
                            entity_type="company",
                            entity_id=company_id,
                            key=key,
                            value=value,
                            source=source,
                            confidence=confidence,
                        )

                # Also write process facts
                process = intelligence.get("current_process_summary", "")
                if process:
                    knowledge.set_fact(
                        entity_type="company", entity_id=company_id,
                        key="current_process", value=process,
                        source="website_assessment", confidence=0.9,
                    )

                # Buying signals
                for signal in intelligence.get("buying_signals", []):
                    knowledge.set_fact(
                        entity_type="company", entity_id=company_id,
                        key="buying_signal", value=signal,
                        source="website_assessment", confidence=0.7,
                    )

                event.status = "completed"
                db.commit()
                processed += 1
                logger.info("Knowledge graph ingested: assessment=%s company=%s facts=%d", assessment_id, company_id, len(facts_to_write))

            except Exception as exc:
                db.rollback()
                event.status = "failed" if event.attempt_count >= event.max_attempts else "pending"
                event.last_error = str(exc)[:500]
                db.commit()
                logger.error("Knowledge ingestion failed: event_id=%s error=%s", event.id, str(exc)[:200])
                if event.attempt_count < event.max_attempts:
                    raise self.retry(exc=exc, countdown=min(120 * (2 ** (event.attempt_count - 1)), 3600))

        return {"processed": processed}

    except Exception as exc:
        logger.error("Knowledge assessment ingestion worker failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# AI ENRICHMENT OUTBOX EVENT — Sprint 47.9
# Enqueued by assessment service for async AI enrichment.
# ═══════════════════════════════════════════════════════════

# (The AI enrichment worker will be implemented in a future sprint.
#  For now, the outbox event is written by the assessment service
#  and consumed when the worker is ready.)


# ═══════════════════════════════════════════════════════════
# SPRINT 48.1 — CALL OUTBOX CONSUMERS
# ═══════════════════════════════════════════════════════════

@celery_app.task(name="workers.call_timeline_projection", bind=True, max_retries=3, default_retry_delay=30, queue="high")
def call_timeline_projection(self, event_id: int | None = None, **context):
    """Project call events into timeline via KnowledgeEvent."""
    db = _get_db()
    try:
        from app.infrastructure.db.models import OutboxEvent, Call
        from app.infrastructure.db.knowledge_graph import KnowledgeEvent
        events = _fetch_outbox_events(db, "call.timeline_projection.requested", event_id)
        processed = 0
        for event in events:
            try:
                event.status = "processing"; event.attempt_count += 1; event.last_attempt_at = datetime.now(UTC); db.commit()
                payload = event.payload_json or {}
                call = db.query(Call).filter(Call.public_uuid == payload.get("call_uuid", "")).first()
                if call:
                    ke = KnowledgeEvent(entity_type="company", entity_id=call.company_id or 0,
                        event_type=f"call_{call.status.lower()}",
                        description=f"{'Outbound' if call.direction == 'outbound' else 'Inbound'} call {call.status.lower()}. Duration: {call.duration_seconds}s. UUID: {call.public_uuid}")
                    db.add(ke)
                event.status = "completed"; db.commit(); processed += 1
            except Exception as exc:
                db.rollback(); _mark_event_failed(db, event, exc)
        return {"processed": processed}
    except Exception as exc: raise self.retry(exc=exc)
    finally: db.close()


@celery_app.task(name="workers.call_metrics_recalculation", bind=True, max_retries=3, default_retry_delay=30, queue="normal")
def call_metrics_recalculation(self, event_id: int | None = None, **context):
    """Recalculate conversation metrics from persisted calls."""
    db = _get_db()
    try:
        from app.infrastructure.db.models import OutboxEvent, Call, Conversation
        events = _fetch_outbox_events(db, "call.metrics_recalculation.requested", event_id)
        processed = 0
        for event in events:
            try:
                event.status = "processing"; event.attempt_count += 1; event.last_attempt_at = datetime.now(UTC); db.commit()
                payload = event.payload_json or {}
                company_id = payload.get("company_id")
                if company_id:
                    calls = db.query(Call).filter(Call.company_id == company_id).all()
                    conv = db.query(Conversation).filter(Conversation.company_id == company_id).first()
                    if conv:
                        total = len(calls)
                        connected = [c for c in calls if c.status == "COMPLETED"]
                        total_dur = sum(c.duration_seconds or 0 for c in connected)
                        last = max((c.ended_at for c in calls if c.ended_at), default=None)
                        conv.summary = f"Calls: {total} ({len(connected)} connected). Talk: {total_dur}s. Last: {last.isoformat() if last else 'N/A'}."
                event.status = "completed"; db.commit(); processed += 1
            except Exception as exc:
                db.rollback(); _mark_event_failed(db, event, exc)
        return {"processed": processed}
    except Exception as exc: raise self.retry(exc=exc)
    finally: db.close()


@celery_app.task(name="workers.call_knowledge_ingestion", bind=True, max_retries=3, default_retry_delay=60, queue="normal")
def call_knowledge_ingestion(self, event_id: int | None = None, **context):
    """Write call facts to knowledge graph."""
    db = _get_db()
    try:
        from app.infrastructure.db.models import OutboxEvent, Call
        from app.application.knowledge.service import KnowledgeService
        events = _fetch_outbox_events(db, "knowledge.call_ingestion.requested", event_id)
        knowledge = KnowledgeService(db)
        processed = 0
        for event in events:
            try:
                event.status = "processing"; event.attempt_count += 1; event.last_attempt_at = datetime.now(UTC); db.commit()
                payload = event.payload_json or {}
                company_id = payload.get("company_id", 0)
                call = db.query(Call).filter(Call.public_uuid == payload.get("call_uuid", "")).first()
                if company_id:
                    knowledge.set_fact("company", company_id, "has_call_activity", "true", "call_worker", 1.0)
                    if call:
                        knowledge.set_fact("company", company_id, "last_call_status", call.status, "call_worker", 0.9)
                        knowledge.set_fact("company", company_id, "last_call_direction", call.direction, "call_worker", 0.9)
                event.status = "completed"; db.commit(); processed += 1
            except Exception as exc:
                db.rollback(); _mark_event_failed(db, event, exc)
        return {"processed": processed}
    except Exception as exc: raise self.retry(exc=exc)
    finally: db.close()


def _fetch_outbox_events(db, event_type: str, event_id: int | None = None, lock: bool = False):
    """Fetch pending outbox events. Optionally uses SELECT FOR UPDATE SKIP LOCKED
    for concurrency-safe claiming across multiple workers."""
    from app.infrastructure.db.models import OutboxEvent

    if event_id:
        query = db.query(OutboxEvent).filter(OutboxEvent.id == event_id)
        if lock:
            query = query.with_for_update(skip_locked=True)
        evt = query.first()
        return [evt] if evt else []

    query = db.query(OutboxEvent).filter(
        OutboxEvent.event_type == event_type,
        OutboxEvent.status == "pending",
    ).order_by(OutboxEvent.created_at.asc()).limit(10)

    if lock:
        query = query.with_for_update(skip_locked=True)

    return query.all()


# Canonical event names used across route, dispatcher, worker, and tests
RECONCILIATION_EVENT = "call.reconciliation.requested"
SMS_RECOVERY_EVENT = "sms.missed_call_recovery.requested"

# Canonical bounded-ID prefixes — MUST be used consistently everywhere
MISSED_CALL_CORR_PREFIX = "missed_call"
SMS_MISSED_CALL_IDEM_PREFIX = "sms_missed_call"
SMS_PROVIDER_IDEM_PREFIX = "pns_missed"

# Assessment lifecycle event types — consumed by outbox_process_assessment_lifecycle
ASSESSMENT_COMPLETED_EVENT = "assessment.completed"
ASSESSMENT_REPORT_REQUESTED_EVENT = "assessment.report.requested"
LEAD_FOLLOWUP_REQUESTED_EVENT = "lead.followup.requested"
ASSESSMENT_LIFECYCLE_EVENTS = [
    ASSESSMENT_COMPLETED_EVENT,
    ASSESSMENT_REPORT_REQUESTED_EVENT,
    LEAD_FOLLOWUP_REQUESTED_EVENT,
]
# Stale processing threshold: events stuck in "processing" longer than this are reset to "pending"
STALE_PROCESSING_MINUTES = 15

# Worker dispatch mapping — used by routing tests and Celery task routing
WORKER_DISPATCH: dict[str, str] = {
    RECONCILIATION_EVENT: "workers.call_missed_call_recovery",
    SMS_RECOVERY_EVENT: "workers.sms_missed_call_recovery",
}


def _claim_event(db, event, lease_holder: str) -> bool:
    """Claim an outbox event with a row-level lock and COMMIT immediately.

    Uses SELECT FOR UPDATE SKIP LOCKED and a status guard: only pending
    events (or retryable events that _recover_stale_leases reset) can be
    claimed.  Once committed, no other worker may claim until the lease
    is explicitly recovered.

    Returns True if the event was claimed; False if locked, lost, or
    already in a non-claimable state.
    """
    from app.infrastructure.db.models import OutboxEvent

    locked = db.query(OutboxEvent).filter(
        OutboxEvent.id == event.id,
    ).with_for_update(skip_locked=True).first()

    if locked is None:
        return False

    # Only claim events that are ready to be processed
    if locked.status != "pending":
        return False

    locked.status = "processing"
    locked.attempt_count += 1
    locked.last_attempt_at = datetime.now(UTC)
    locked.leased_at = datetime.now(UTC)
    locked.lease_holder = lease_holder
    db.commit()
    return True


def _mark_event_completed(db, event):
    """Mark an outbox event completed.  Re-fetches to avoid detached-instance
    mutations when the caller passes an event from a different session."""
    from app.infrastructure.db.models import OutboxEvent
    fresh = db.query(OutboxEvent).filter(OutboxEvent.id == event.id).first()
    if fresh is None:
        return
    fresh.status = "completed"
    fresh.leased_at = None
    fresh.lease_holder = None
    db.commit()


def _mark_event_failed(db, event, exc):
    """Mark an outbox event failed (retryable if under max_attempts).
    Re-fetches to avoid detached-instance mutations."""
    from app.infrastructure.db.models import OutboxEvent
    fresh = db.query(OutboxEvent).filter(OutboxEvent.id == event.id).first()
    if fresh is None:
        return
    fresh.status = "failed" if fresh.attempt_count >= fresh.max_attempts else "pending"
    fresh.last_error = str(exc)[:500]
    fresh.leased_at = None
    fresh.lease_holder = None
    db.commit()


def _mark_event_failed_permanent(db, event, error_message: str):
    """Terminal permanent failure for invalid/malformed events.
    Sets status='failed' regardless of attempt_count."""
    from app.infrastructure.db.models import OutboxEvent
    fresh = db.query(OutboxEvent).filter(OutboxEvent.id == event.id).first()
    if fresh is None:
        return
    fresh.status = "failed"
    fresh.last_error = error_message[:500]
    fresh.leased_at = None
    fresh.lease_holder = None
    db.commit()


def _mark_event_pending(db, event):
    """Revert a claimed event back to pending (e.g. missing provider config)."""
    from app.infrastructure.db.models import OutboxEvent
    fresh = db.query(OutboxEvent).filter(OutboxEvent.id == event.id).first()
    if fresh is None:
        return
    fresh.status = "pending"
    fresh.leased_at = None
    fresh.lease_holder = None
    db.commit()


def _recover_stale_leases(db, lease_timeout_seconds: int = 300) -> int:
    """Reset any outbox event that has been stuck in 'processing' longer
    than lease_timeout_seconds back to 'pending'.

    Guards against workers that die after claiming but before completing.
    Returns the number of events recovered."""
    from app.infrastructure.db.models import OutboxEvent

    cutoff = datetime.now(UTC) - timedelta(seconds=lease_timeout_seconds)
    stale = (
        db.query(OutboxEvent)
        .filter(
            OutboxEvent.status == "processing",
            OutboxEvent.leased_at.isnot(None),
            OutboxEvent.leased_at < cutoff,
        )
        .all()
    )
    for event in stale:
        event.status = "pending"
        event.leased_at = None
        event.lease_holder = None
    if stale:
        db.commit()
    return len(stale)


# Grace period before reconciliation worker processes a hangup event.
# This allows late call.answered or call.bridged events to arrive.
GRACE_PERIOD_SECONDS = int(os.getenv("RECONCILIATION_GRACE_PERIOD_SECONDS", "30"))


def _reconcile_from_ledger(db, provider_call_id: str, grace_seconds: int = GRACE_PERIOD_SECONDS) -> bool:
    """Check the ProviderWebhookEvent ledger for a late answer or bridge event.

    A call is truly missed only if no call.answered or call.bridged event
    arrived within the grace period after the hangup.

    Returns True if the call was truly missed (no answer/bridge in ledger).
    """
    from app.infrastructure.db.models import ProviderWebhookEvent

    cutoff = datetime.now(UTC) - timedelta(seconds=grace_seconds)

    answered = db.query(ProviderWebhookEvent).filter(
        ProviderWebhookEvent.call_control_id == provider_call_id,
        ProviderWebhookEvent.event_type.in_(["call.answered", "call.bridged"]),
        ProviderWebhookEvent.created_at >= cutoff,
    ).first()

    return answered is None


def _format_phone_friendly(normalized: str) -> str:
    """Format a normalized E.164 number for human-readable display.

    '+16045551234' becomes '(604) 555-1234'.
    Falls back to the raw input if parsing fails.
    """
    import re as _re
    if not normalized:
        return "unknown"
    digits = _re.sub(r"\D", "", normalized)
    if len(digits) == 11 and digits.startswith("1"):
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:10]}"
    return normalized


@celery_app.task(
    name="workers.call_missed_call_recovery",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="high",
)
def call_missed_call_recovery(self, event_id: int | None = None, **context):
    """Reconcile a completed call and create recovery tasks if truly missed.

    Consumes call.reconciliation.requested outbox events.
    Checks the ProviderWebhookEvent ledger for late answer/bridge events
    after a configurable grace period. Only creates callback tasks,
    missed activities, and SMS outbox events when the call was truly missed.

    Converts the Call status from COMPLETED to MISSED only after ledger
    reconciliation confirms no answer event arrived.
    """
    db = _get_db()
    try:
        from app.infrastructure.db.models import Activity, Call, LeadCaptureRecord, OutboxEvent, ProviderWebhookEvent, Task
        from app.application.intake.sms import can_send_sms

        events = _fetch_outbox_events(db, RECONCILIATION_EVENT, event_id, lock=False)
        if not events:
            return {"processed": 0}

        task_id = self.request.id
        processed = 0

        for event in events:
            # Do not claim the event until Telnyx's late answer/bridge window
            # has elapsed. Leaving it pending lets the next scheduled pass
            # reconcile it safely without creating a false missed call.
            created_at = event.created_at
            if event_id is None and created_at is not None:
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=UTC)
                if datetime.now(UTC) - created_at < timedelta(seconds=GRACE_PERIOD_SECONDS):
                    continue

            db_session_clean = _get_db()
            try:
                if not _claim_event(db_session_clean, event, task_id):
                    continue

                payload = event.payload_json or {}
                call_id = payload.get("call_id")
                call_uuid = payload.get("call_public_uuid", "")
                normalized_caller = payload.get("normalized_caller_number", "")
                org_id = payload.get("organization_id")
                contact_id = payload.get("contact_id")
                company_id = payload.get("company_id")

                if not org_id:
                    _mark_event_failed(db_session_clean, event, ValueError("No organization_id in payload"))
                    continue

                call = db_session_clean.query(Call).filter(Call.id == call_id).first()
                if not call:
                    _mark_event_failed(db_session_clean, event, ValueError(f"Call {call_id} not found"))
                    continue

                if call.status == "MISSED":
                    _mark_event_completed(db_session_clean, event)
                    continue

                provider_call_id = call.provider_call_id
                if not provider_call_id:
                    _mark_event_failed(db_session_clean, event, ValueError("No provider_call_id on call"))
                    continue

                if not _reconcile_from_ledger(db_session_clean, provider_call_id):
                    logger.info(
                        "Reconciliation cancelled: call=%s had late answer/bridge in ledger",
                        call_uuid,
                    )
                    _mark_event_completed(db_session_clean, event)
                    continue

                call.status = "MISSED"
                call.outcome = "missed"
                call.updated_at = datetime.now(UTC)

                caller_display = _format_phone_friendly(normalized_caller)
                spam_score = call.spam_score or 0

                recovery_key = f"missed_call_{call.public_uuid}"

                existing = db_session_clean.query(Task).filter(
                    Task.recovery_key == recovery_key,
                ).first()
                if existing:
                    logger.info(
                        "Recovery task already exists for call=%s task=%s",
                        call_uuid, existing.id,
                    )
                    _mark_event_completed(db_session_clean, event)
                    continue

                task = Task(
                    organization_id=org_id,
                    contact_id=contact_id,
                    company_id=company_id,
                    title=f"Return missed call from {caller_display}",
                    description=(
                        f"Missed inbound call from {caller_display}. "
                        f"Spam score: {spam_score}/100."
                    ),
                    priority="high",
                    status="open",
                    source="missed_call",
                    sla_deadline=datetime.now(UTC) + timedelta(hours=4),
                    due_date=(datetime.now(UTC) + timedelta(hours=2)).date(),
                    recovery_key=recovery_key,
                )
                db_session_clean.add(task)
                db_session_clean.flush()

                activity = Activity(
                    organization_id=org_id,
                    contact_id=contact_id,
                    company_id=company_id,
                    activity_type="call_missed",
                    subject=f"Missed call from {caller_display}",
                    body="Missed inbound call. Callback task created.",
                )
                db_session_clean.add(activity)
                db_session_clean.flush()

                captured = db_session_clean.query(LeadCaptureRecord).filter(
                    LeadCaptureRecord.organization_id == org_id,
                    LeadCaptureRecord.source == "phone",
                    LeadCaptureRecord.external_id == call.public_uuid,
                ).first()
                if captured is None:
                    db_session_clean.add(LeadCaptureRecord(
                        organization_id=org_id,
                        source="phone",
                        external_id=call.public_uuid,
                        phone=normalized_caller,
                        summary="Missed inbound call. Callback required.",
                        status="new",
                        priority="high",
                        next_action="Return the missed call",
                        next_action_at=datetime.now(UTC) + timedelta(hours=2),
                        metadata_json={"call_id": call.id, "spam_score": spam_score},
                    ))

                sms_outbox = OutboxEvent(
                    event_type=SMS_RECOVERY_EVENT,
                    payload_json={
                        "call_id": call_id,
                        "call_public_uuid": call_uuid,
                        "normalized_caller_number": normalized_caller,
                        "organization_id": org_id,
                        "contact_id": contact_id,
                    },
                    correlation_id=bounded_correlation_id(MISSED_CALL_CORR_PREFIX, call_uuid),
                    idempotency_key=bounded_idempotency_key(SMS_MISSED_CALL_IDEM_PREFIX, call.public_uuid),
                )
                db_session_clean.add(sms_outbox)

                _mark_event_completed(db_session_clean, event)
                processed += 1
                logger.info(
                    "Recovery complete: call=%s task=%s activity=%s",
                    call_uuid, task.id, activity.id,
                )

            except Exception as exc:
                db_session_clean.rollback()
                _mark_event_failed(db_session_clean, event, exc)
                if event.attempt_count < event.max_attempts:
                    raise self.retry(
                        exc=exc,
                        countdown=min(60 * (2 ** (event.attempt_count - 1)), 1800),
                    )
            finally:
                db_session_clean.close()

        return {"processed": processed}
    except Exception as exc:
        logger.error("Reconciliation worker failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(
    name="workers.sms_missed_call_recovery",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
    queue="high",
)
def sms_missed_call_recovery(self, event_id: int | None = None, **context):
    """Send one recovery SMS for a missed call. Uses provider idempotency
    and durable send-attempt tracking to prevent duplicate delivery.

    Events are claimed and validated before provider configuration is
    checked — a malformed event (no tenant, suppressed, spam) is resolved
    immediately.  A valid event with a missing provider configuration is
    left pending/retryable so an operator can configure the key.
    """
    db = _get_db()
    try:
        from app.infrastructure.db.models import Call, ProductConfiguration
        from app.application.intake.sms import can_send_sms, MISSED_CALL_SMS_MESSAGE

        events = _fetch_outbox_events(db, SMS_RECOVERY_EVENT, event_id, lock=False)
        if not events:
            return {"processed": 0}

        task_id = self.request.id
        processed = 0

        for event in events:
            db_session_clean = _get_db()
            try:
                if not _claim_event(db_session_clean, event, task_id):
                    continue

                payload = event.payload_json or {}
                call_id = payload.get("call_id")
                normalized = payload.get("normalized_caller_number", "")
                org_id = payload.get("organization_id")

                # ── Validation (resolve immediately) ──
                if not org_id:
                    logger.error(
                        "SMS worker: no organization_id for event=%s, failing permanently",
                        event.id,
                    )
                    _mark_event_failed_permanent(
                        db_session_clean, event, "No organization_id in payload"
                    )
                    continue

                if not normalized:
                    logger.info("SMS skipped: event=%s no phone number", event.id)
                    _mark_event_completed(db_session_clean, event)
                    continue

                can_send, reason = can_send_sms(db_session_clean, org_id, normalized)
                if not can_send:
                    logger.info(
                        "SMS skipped: reason=%s org=%s",
                        reason, org_id,
                    )
                    _mark_event_completed(db_session_clean, event)
                    continue

                call = db_session_clean.query(Call).filter(Call.id == call_id).first()

                # Packaged-product configuration is tenant-specific. Existing
                # PNS organizations without a product row retain the proven
                # legacy behavior during migration.
                product_config = db_session_clean.query(ProductConfiguration).filter(
                    ProductConfiguration.organization_id == org_id,
                    ProductConfiguration.product_code == "never_miss",
                ).first()
                if product_config and not product_config.enabled:
                    logger.info("SMS skipped: Never Miss disabled for org=%s", org_id)
                    _mark_event_completed(db_session_clean, event)
                    continue

                if product_config:
                    month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    messages_this_month = db_session_clean.query(Call).filter(
                        Call.organization_id == org_id,
                        Call.sms_sent_at.isnot(None),
                        Call.sms_sent_at >= month_start,
                    ).count()
                    if messages_this_month >= product_config.monthly_message_limit:
                        logger.warning("SMS skipped: monthly message limit reached for org=%s", org_id)
                        if call:
                            call.sms_status = "limit_reached"
                        _mark_event_completed(db_session_clean, event)
                        continue

                # ── Spam quarantine ──
                if call and (call.spam_score or 0) >= 30:
                    logger.info(
                        "SMS skipped: spam_score=%s >= 30 for call=%s",
                        call.spam_score, call.public_uuid,
                    )
                    _mark_event_completed(db_session_clean, event)
                    continue

                if call and call.sms_status == "sent":
                    _mark_event_completed(db_session_clean, event)
                    continue

                # ── Provider configuration ──
                telnyx_api_key = os.getenv("TELNYX_API_KEY", "")
                telnyx_messaging_profile_id = os.getenv("TELNYX_MESSAGING_PROFILE_ID", "")
                pns_phone = (
                    product_config.business_phone
                    if product_config and product_config.business_phone
                    else os.getenv("PNS_PHONE_NUMBER", "")
                )
                recovery_message = (
                    product_config.recovery_message.strip()
                    if product_config and product_config.recovery_message
                    else MISSED_CALL_SMS_MESSAGE
                )

                if not telnyx_api_key:
                    logger.error(
                        "SMS worker: TELNYX_API_KEY not configured — "
                        "event=%s reverted to pending for retry",
                        event.id,
                    )
                    _mark_event_pending(db_session_clean, event)
                    continue

                provider_idem_key = (
                    bounded_idempotency_key(SMS_PROVIDER_IDEM_PREFIX, call.public_uuid)
                    if call
                    else f"pns_missed_{event.idempotency_key or event.id}"
                )

                msg_id = _send_telnyx_sms(
                    api_key=telnyx_api_key,
                    messaging_profile_id=telnyx_messaging_profile_id,
                    from_phone=pns_phone,
                    to_phone=normalized,
                    message=recovery_message,
                    idempotency_key=provider_idem_key,
                )

                if call:
                    call.sms_status = "sent"
                    call.sms_sent_at = datetime.now(UTC)
                    call.sms_message_id = msg_id

                _mark_event_completed(db_session_clean, event)
                processed += 1
                logger.info(
                    "Recovery SMS sent: call=%s msg_id=%s",
                    call.public_uuid if call else "unknown",
                    msg_id[:12] if msg_id else "none",
                )

            except Exception as exc:
                db_session_clean.rollback()
                _mark_event_failed(db_session_clean, event, exc)
                logger.error(
                    "SMS send failed: event=%s attempt=%s error=%s",
                    event.id, event.attempt_count, str(exc)[:200],
                )
                if event.attempt_count < event.max_attempts:
                    raise self.retry(
                        exc=exc,
                        countdown=min(120 * (2 ** (event.attempt_count - 1)), 3600),
                    )
            finally:
                db_session_clean.close()

        return {"processed": processed}
    except Exception as exc:
        logger.error("SMS worker failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


def _send_telnyx_sms(
    api_key: str,
    messaging_profile_id: str,
    from_phone: str,
    to_phone: str,
    message: str,
    idempotency_key: str | None = None,
) -> str:
    """Send SMS via Telnyx Messaging API.

    Supports provider-level idempotency to prevent duplicate delivery
    when a timeout occurs after Telnyx accepts the message.
    Returns the Telnyx message ID on success.
    """
    if not api_key:
        raise RuntimeError("TELNYX_API_KEY not configured")

    body: dict = {
        "from": from_phone,
        "to": to_phone,
        "text": message,
        "messaging_profile_id": messaging_profile_id,
    }
    api_public_url = os.getenv(
        "API_PUBLIC_URL", os.getenv("CRM_APP_URL", "")
    ).rstrip("/")
    if api_public_url:
        body["webhook_url"] = f"{api_public_url}/api/v1/telephony/sms/webhook"

    if idempotency_key:
        body["idempotency_key"] = idempotency_key

    resp = httpx.post(
        "https://api.telnyx.com/v2/messages",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=15,
    )
    if resp.status_code not in (200, 201, 202):
        raise RuntimeError(
            f"Telnyx SMS API returned {resp.status_code}: {resp.text[:200]}"
        )

    data = resp.json().get("data", {})
    return data.get("id", "")


@celery_app.task(
    name="workers.sms_inbound_webhook",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    queue="high",
)
def sms_inbound_webhook(self, event_id: int | None = None, **context):
    """Process inbound SMS webhook events from the outbox.
    Handles STOP/START suppression and normal replies.
    Currently inbound SMS is handled synchronously in the webhook route;
    this worker exists for retry/async processing of failed deliveries."""
    db = _get_db()
    try:
        events = _fetch_outbox_events(db, "sms.inbound_webhook.requested", event_id, lock=False)
        processed = 0
        for event in events:
            try:
                _mark_event_completed(db, event)
                processed += 1
            except Exception as exc:
                db.rollback()
                _mark_event_failed(db, event, exc)
        return {"processed": processed}
    except Exception as exc:
        logger.error("SMS inbound worker failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(
    name="workers.outbox_process_assessment_lifecycle",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    queue="high",
)
def outbox_process_assessment_lifecycle(self, event_id: int | None = None, **context):
    """Process assessment lifecycle outbox events.

    Consumes three event types:
      - assessment.completed: verify Assessment, Company, Lead exist from payload
      - assessment.report.requested: verify Assessment has intelligence to build a report
      - lead.followup.requested: verify the referenced Lead and Task exist

    Each handler validates invariants before marking the event completed.
    Missing invariants cause a permanent failure (no retry).
    Does NOT create duplicate business records and does NOT mutate business state.

    In event_id mode (single event):
      - Completed events are a clean no-op (already processed)
      - Events with event_type NOT in ASSESSMENT_LIFECYCLE_EVENTS are skipped
      - Only pending events of valid types are processed
    """
    db = _get_db()
    try:
        from app.infrastructure.db.models import OutboxEvent

        if event_id:
            event = db.query(OutboxEvent).filter(OutboxEvent.id == event_id).first()
            if event is None:
                return {"processed": 0}
            if event.status == "completed":
                return {"processed": 0, "note": "event already completed"}
            if event.event_type not in ASSESSMENT_LIFECYCLE_EVENTS:
                return {"processed": 0, "note": f"event_type {event.event_type} not a lifecycle event"}
            if event.status != "pending":
                return {"processed": 0, "note": f"event status is {event.status}, not pending"}
            events = [event]
        else:
            events = db.query(OutboxEvent).filter(
                OutboxEvent.event_type.in_(ASSESSMENT_LIFECYCLE_EVENTS),
                OutboxEvent.status == "pending",
            ).order_by(OutboxEvent.created_at.asc()).limit(10).all()

        if not events:
            return {"processed": 0}

        processed = 0
        for event in events:
            try:
                event.status = "processing"
                event.attempt_count += 1
                event.last_attempt_at = datetime.now(UTC)
                db.commit()

                payload = event.payload_json or {}
                etype = event.event_type

                if etype == ASSESSMENT_COMPLETED_EVENT:
                    _handle_assessment_completed(db, payload, event)
                elif etype == ASSESSMENT_REPORT_REQUESTED_EVENT:
                    _handle_assessment_report_requested(db, payload, event)
                elif etype == LEAD_FOLLOWUP_REQUESTED_EVENT:
                    _handle_lead_followup_requested(db, payload, event)

                _mark_event_completed(db, event)
                processed += 1
                logger.info("Assessment lifecycle processed: event_id=%s type=%s", event.id, etype)

            except _InvariantFailure as exc:
                db.rollback()
                _mark_event_failed_permanent(db, event, str(exc))
                logger.warning("Assessment lifecycle invariant failed: event_id=%s type=%s error=%s", event.id, event.event_type, exc)
            except Exception as exc:
                db.rollback()
                _mark_event_failed(db, event, exc)
                logger.error("Assessment lifecycle failed: event_id=%s type=%s error=%s", event.id, event.event_type, str(exc)[:200])

        return {"processed": processed}

    except Exception as exc:
        logger.error("Assessment lifecycle worker failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


class _InvariantFailure(Exception):
    """Raised when a lifecycle event's required invariants are not satisfied."""


def _handle_assessment_completed(db, payload: dict, event):
    """Verify the Assessment, Company, and Lead referenced in payload exist.
    All three references are required since the producer always emits them."""
    from app.infrastructure.db.models import AutomationAssessment, Company, Lead

    assessment_id = payload.get("assessment_id")
    company_id = payload.get("company_id")
    lead_id = payload.get("lead_id")

    if not assessment_id:
        raise _InvariantFailure("Missing assessment_id in payload")
    if not company_id:
        raise _InvariantFailure("Missing company_id in payload")
    if not lead_id:
        raise _InvariantFailure("Missing lead_id in payload")

    assessment = db.query(AutomationAssessment).filter(
        AutomationAssessment.public_id == assessment_id
    ).first()
    if not assessment:
        raise _InvariantFailure(f"Assessment public_id={assessment_id} not found")

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise _InvariantFailure(f"Company id={company_id} not found for assessment {assessment_id}")

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise _InvariantFailure(f"Lead id={lead_id} not found for assessment {assessment_id}")


def _handle_assessment_report_requested(db, payload: dict, event):
    """Verify the Assessment exists and has intelligence results.
    Does NOT generate a report or mutate business state."""
    from app.infrastructure.db.models import AutomationAssessment

    assessment_id = payload.get("assessment_id")
    if not assessment_id:
        raise _InvariantFailure("Missing assessment_id in payload")

    assessment = db.query(AutomationAssessment).filter(
        AutomationAssessment.public_id == assessment_id
    ).first()
    if not assessment:
        raise _InvariantFailure(f"Assessment public_id={assessment_id} not found")

    has_intelligence = (
        assessment.intelligence_json is not None
        or assessment.intelligence_generated_at is not None
    )
    if not has_intelligence:
        raise _InvariantFailure(
            f"Assessment public_id={assessment_id} has no intelligence to build a report from"
        )


def _handle_lead_followup_requested(db, payload: dict, event):
    """Verify the referenced Lead and Task exist for follow-up.
    Both references are required since the producer always emits them."""
    from app.infrastructure.db.models import Lead, Task

    lead_id = payload.get("lead_id")
    task_id = payload.get("task_id")

    if not lead_id:
        raise _InvariantFailure("Missing lead_id in payload")
    if not task_id:
        raise _InvariantFailure("Missing task_id in payload")

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise _InvariantFailure(f"Lead id={lead_id} not found")

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise _InvariantFailure(f"Task id={task_id} not found for lead {lead_id}")

    # Lead follow-up is now validated; no duplicate records created
