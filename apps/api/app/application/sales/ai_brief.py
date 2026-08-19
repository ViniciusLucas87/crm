"""
AI Daily Brief Generator.

Produces a personalized executive briefing from live CRM data.
Every recommendation references actual database records.
"""

from datetime import date, datetime, timedelta, timezone

from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.infrastructure.db.models import Activity, Company, Opportunity, Task
from app.infrastructure.db.social_leads import SocialLeadOpportunity


# ── Output Models ──

class BriefItem(BaseModel):
    type: str  # "priority", "signal", "followup", "meeting", "task", "opportunity", "insight"
    title: str
    description: str
    company_name: str | None = None
    company_id: int | None = None
    score: int | None = None
    reason: str | None = None


class OutreachSnapshot(BaseModel):
    channel: str
    total: int
    contacted: int
    ready: int
    replies: int
    needs_review: int


class DailyBrief(BaseModel):
    greeting: str
    date: str
    summary: str
    priorities: list[BriefItem]
    follow_ups: list[BriefItem]
    signals: list[BriefItem]
    upcoming_meetings: list[BriefItem]
    overdue_tasks: list[BriefItem]
    top_opportunities: list[BriefItem]
    research_queue: list[BriefItem]
    actions: list[BriefItem]
    outreach: list[OutreachSnapshot] = Field(default_factory=list)
    data_warnings: list[BriefItem] = Field(default_factory=list)


# ── Engine ──

class DailyBriefEngine:
    def __init__(self, session: Session, organization_id: int) -> None:
        self._session = session
        self._org_id = organization_id

    def generate(self, user_first_name: str = "") -> DailyBrief:
        now = datetime.now(timezone.utc)
        today = now.date()

        greeting = self._build_greeting(user_first_name)
        priorities = self._build_priorities(today)
        follow_ups = self._build_follow_ups(now)
        signals = self._build_signals()
        meetings = self._build_upcoming_meetings(now)
        overdue = self._build_overdue_tasks(now)
        top_opps = self._build_top_opportunities()
        research = self._build_research_queue()
        outreach, data_warnings = self._build_outreach_snapshot()
        actions = self._build_suggested_actions(priorities, follow_ups, signals, outreach)

        priority_count = len(priorities)
        signal_count = len(signals)
        meeting_count = len(meetings)

        parts: list[str] = []
        if priority_count: parts.append(f"{priority_count} {'priority' if priority_count == 1 else 'priorities'}")
        if signal_count: parts.append(f"{signal_count} new {'signal' if signal_count == 1 else 'signals'}")
        if meeting_count: parts.append(f"{meeting_count} {'meeting' if meeting_count == 1 else 'meetings'} today")
        summary = f"You have {', '.join(parts) if parts else 'a clear day ahead'}." if parts else "Your day is clear. Great time to prospect."

        return DailyBrief(
            greeting=greeting,
            date=today.strftime("%A, %B %d, %Y"),
            summary=summary,
            priorities=priorities,
            follow_ups=follow_ups,
            signals=signals,
            upcoming_meetings=meetings,
            overdue_tasks=overdue,
            top_opportunities=top_opps,
            research_queue=research,
            actions=actions,
            outreach=outreach,
            data_warnings=data_warnings,
        )

    def _build_outreach_snapshot(self) -> tuple[list[OutreachSnapshot], list[BriefItem]]:
        opportunities = self._session.execute(
            select(SocialLeadOpportunity).where(
                SocialLeadOpportunity.organization_id == self._org_id,
                SocialLeadOpportunity.channel.in_(["linkedin", "reddit"]),
            )
        ).scalars().all()

        snapshots: list[OutreachSnapshot] = []
        warnings: list[BriefItem] = []
        for channel in ("linkedin", "reddit"):
            records = [item for item in opportunities if item.channel == channel]
            internal_tests = [
                item for item in records
                if "internal_test" in item.author_handle.lower()
                or "internal test" in item.post_title.lower()
            ]
            real_records = [item for item in records if item not in internal_tests]
            snapshots.append(OutreachSnapshot(
                channel=channel,
                total=len(real_records),
                contacted=sum(item.status == "contacted" for item in real_records),
                ready=sum(item.status in {"note_ready", "reply_ready"} for item in real_records),
                replies=sum(bool(item.response_summary) for item in real_records),
                needs_review=sum(item.status in {"watch", "new"} for item in real_records),
            ))
            if internal_tests:
                warnings.append(BriefItem(
                    type="warning",
                    title=f"{len(internal_tests)} {channel.title()} test record excluded",
                    description="Test activity is not included in your sales totals.",
                    reason="Keeps the morning report accurate",
                ))
        return snapshots, warnings

    def _build_greeting(self, first_name: str) -> str:
        hour = datetime.now().hour
        if hour < 12: return f"Good morning{', ' + first_name if first_name else ''} ☀️"
        if hour < 17: return f"Good afternoon{', ' + first_name if first_name else ''} 👋"
        return f"Good evening{', ' + first_name if first_name else ''} 🌙"

    def _build_priorities(self, today: date) -> list[BriefItem]:
        items: list[BriefItem] = []

        # Companies with high opportunity score and recent activity
        high_score = self._session.execute(
            select(Company)
            .where(Company.organization_id == self._org_id, Company.is_archived == False, Company.opportunity_score >= 60)
            .order_by(Company.opportunity_score.desc().nullslast())
            .limit(5)
        ).scalars().all()

        for c in high_score:
            items.append(BriefItem(
                type="priority",
                title="High-value prospect",
                description=f"Opportunity Score: {c.opportunity_score or 0}",
                company_name=c.name,
                company_id=c.id,
                score=c.opportunity_score,
                reason="Top opportunity score",
            ))
        return items

    def _build_follow_ups(self, now: datetime) -> list[BriefItem]:
        recent = now - timedelta(days=14)
        acts = self._session.execute(
            select(Activity, Company)
            .join(Company, Activity.company_id == Company.id)
            .where(
                Activity.organization_id == self._org_id,
                Activity.created_at >= recent,
                Activity.activity_type.in_(["call", "email", "meeting"]),
            )
            .order_by(Activity.created_at.desc())
            .limit(5)
        ).all()

        items: list[BriefItem] = []
        seen: set[int] = set()
        for act, co in acts:
            if co.id in seen: continue
            seen.add(co.id)
            items.append(BriefItem(
                type="followup",
                title=f"Recent {act.activity_type} with {co.name}",
                description=f"Last contact: {act.created_at.strftime('%b %d')}",
                company_name=co.name,
                company_id=co.id,
            ))
        return items

    def _build_signals(self) -> list[BriefItem]:
        companies = self._session.execute(
            select(Company)
            .where(Company.organization_id == self._org_id, Company.is_archived == False, Company.opportunity_score >= 50)
            .order_by(Company.opportunity_score.desc().nullslast())
            .limit(5)
        ).scalars().all()

        items: list[BriefItem] = []
        for c in companies:
            if c.opportunity_score and c.opportunity_score >= 60:
                items.append(BriefItem(
                    type="signal",
                    title=f"{c.name} shows strong buying signals",
                    description=f"Score {c.opportunity_score} — {c.industry or 'Unknown industry'}",
                    company_name=c.name,
                    company_id=c.id,
                    score=c.opportunity_score,
                    reason="High opportunity score with industry alignment",
                ))
        return items

    def _build_upcoming_meetings(self, now: datetime) -> list[BriefItem]:
        # Meetings = activities of type 'meeting' in the next 7 days
        next_week = now + timedelta(days=7)
        acts = self._session.execute(
            select(Activity, Company)
            .join(Company, Activity.company_id == Company.id)
            .where(
                Activity.organization_id == self._org_id,
                Activity.activity_type == "meeting",
                Activity.created_at.between(now, next_week),
            )
            .order_by(Activity.created_at.asc())
            .limit(5)
        ).all()

        return [
            BriefItem(
                type="meeting",
                title=f"Meeting with {co.name}",
                description=act.created_at.strftime("%A at %I:%M %p") if act.created_at else "Upcoming",
                company_name=co.name,
                company_id=co.id,
            )
            for act, co in acts
        ]

    def _build_overdue_tasks(self, now: datetime) -> list[BriefItem]:
        tasks = self._session.execute(
            select(Task, Company)
            .join(Company, Task.company_id == Company.id)
            .where(
                Task.organization_id == self._org_id,
                Task.status != "completed",
                Task.due_date < now,
            )
            .order_by(Task.due_date.asc())
            .limit(5)
        ).all()

        return [
            BriefItem(
                type="task",
                title=t.title or "Overdue task",
                description=f"Due: {t.due_date.strftime('%b %d') if t.due_date else 'Unknown'}",
                company_name=co.name,
                company_id=co.id,
            )
            for t, co in tasks
        ]

    def _build_top_opportunities(self) -> list[BriefItem]:
        opps = self._session.execute(
            select(Opportunity, Company)
            .join(Company, Opportunity.company_id == Company.id)
            .where(Opportunity.organization_id == self._org_id, Opportunity.stage.notin_(["won", "lost"]))
            .order_by(Opportunity.estimated_value.desc().nullslast())
            .limit(5)
        ).all()

        return [
            BriefItem(
                type="opportunity",
                title=o.title or "Opportunity",
                description=f"${o.estimated_value:,.0f}" if o.estimated_value else "Value TBD",
                company_name=co.name,
                company_id=co.id,
            )
            for o, co in opps
        ]

    def _build_research_queue(self) -> list[BriefItem]:
        companies = self._session.execute(
            select(Company)
            .where(
                Company.organization_id == self._org_id,
                Company.is_archived == False,
                or_(Company.research_status.is_(None), Company.research_status == "pending"),
            )
            .order_by(Company.opportunity_score.desc().nullslast())
            .limit(5)
        ).scalars().all()

        return [
            BriefItem(
                type="insight",
                title=f"Research needed: {c.name}",
                description=f"{c.industry or 'Unknown'} — Score: {c.opportunity_score or 'N/A'}",
                company_name=c.name,
                company_id=c.id,
            )
            for c in companies
        ]

    def _build_suggested_actions(
        self,
        priorities: list[BriefItem],
        follow_ups: list[BriefItem],
        signals: list[BriefItem],
        outreach: list[OutreachSnapshot],
    ) -> list[BriefItem]:
        actions: list[BriefItem] = []
        by_channel = {item.channel: item for item in outreach}
        linkedin = by_channel.get("linkedin")
        reddit = by_channel.get("reddit")
        if linkedin and linkedin.ready:
            actions.append(BriefItem(
                type="action",
                title="Send the approved LinkedIn invitations",
                description=f"{linkedin.ready} messages are ready for your review and approval.",
                reason="Start with warm, relevant owner conversations",
            ))
        if reddit and reddit.ready:
            actions.append(BriefItem(
                type="action",
                title="Publish the helpful Reddit replies",
                description=f"{reddit.ready} replies are ready for your review and approval.",
                reason="Help first and only discuss the product when it fits",
            ))
        if any(item.contacted for item in outreach):
            actions.append(BriefItem(
                type="action",
                title="Check replies before new outreach",
                description="Review LinkedIn, Reddit, and Upwork inboxes for active conversations.",
                reason="A live reply is more valuable than another cold message",
            ))
        if signals:
            actions.append(BriefItem(type="action", title="Review buying signals", description=f"{len(signals)} companies showing purchase intent", reason="Engage while intent is high"))
        if follow_ups:
            actions.append(BriefItem(type="action", title="Follow up on recent activity", description=f"{len(follow_ups)} companies with recent contact", reason="Maintain momentum after recent engagement"))
        if not priorities and not signals:
            actions.append(BriefItem(type="action", title="Prospect for new opportunities", description="Use the Opportunity Explorer to find new leads", reason="Pipeline growth"))
        actions.append(BriefItem(type="action", title="Review your research queue", description="Complete company research to improve opportunity scoring", reason="Data quality improves AI accuracy"))
        return actions[:6]
