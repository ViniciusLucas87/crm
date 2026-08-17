from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

# Keep PostgreSQL's efficient JSONB in production while allowing the SQLite
# test database to render the same model metadata.
JSON_DOCUMENT = JSON().with_variant(JSONB, "postgresql")


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employees: Mapped[int | None] = mapped_column(Integer, nullable=True)
    revenue: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    primary_contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    # ── Intelligence fields ──
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    locations: Mapped[str | None] = mapped_column(Text, nullable=True)
    founded: Mapped[int | None] = mapped_column(Integer, nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    facebook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    instagram_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    twitter_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    youtube_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    google_business: Mapped[str | None] = mapped_column(String(500), nullable=True)
    business_categories: Mapped[str | None] = mapped_column(Text, nullable=True)
    opportunity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    buying_signals: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    research_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    province: Mapped[str | None] = mapped_column(String(120), nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    business_type: Mapped[str | None] = mapped_column(String(120), nullable=True)


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    job_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(50), nullable=True)
    linkedin: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferred_contact: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_decision_maker: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    confidence: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    discovery_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    company: Mapped["Company"] = relationship("Company", foreign_keys=[company_id])

# ═══════════════════════════════════════════════════════════
# CONVERSATION — business relationship abstraction
# ═══════════════════════════════════════════════════════════

class Conversation(Base):
    """A long-term business relationship with a company.

    Conversations aggregate calls, emails, meetings, tasks, notes, and future
    AI events into a single timeline. This is the permanent memory of the
    customer relationship — CallSession remains the atomic telephony record.
    """
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    primary_contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)

    # ── Status & stage ──
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    relationship_stage: Mapped[str] = mapped_column(String(20), default="new", nullable=False)

    # ── Ownership ──
    opened_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ── Health ──
    health_score: Mapped[int] = mapped_column(Integer, default=50, nullable=False)

    # ── Summary ──
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Timing ──
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    # ── Metadata ──
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ──
    company: Mapped["Company"] = relationship("Company")

class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    activity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    company: Mapped["Company | None"] = relationship("Company")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sla_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recovery_key: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True, index=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True)
    owner_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    company: Mapped["Company"] = relationship("Company")


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    estimated_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    probability: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    expected_close_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stage: Mapped[str] = mapped_column(String(20), default="lead", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    company: Mapped["Company"] = relationship("Company")


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clerk_org_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clerk_user_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class OrganizationMembership(Base):
    __tablename__ = "organization_memberships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="member", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class ProductConfiguration(Base):
    """Per-organization settings for packaged PNS products."""
    __tablename__ = "product_configurations"
    __table_args__ = (
        UniqueConstraint("organization_id", "product_code", name="uq_product_config_org_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    product_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    plan: Mapped[str] = mapped_column(String(30), default="never_miss", nullable=False)
    business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    business_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notification_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recovery_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_hours_json: Mapped[dict | None] = mapped_column(JSON_DOCUMENT, nullable=True)
    monthly_call_limit: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    monthly_message_limit: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    intake_key_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class ProductSubscription(Base):
    """Paid packaged-product subscription and its self-service provisioning state."""
    __tablename__ = "product_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    stripe_checkout_session_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    stripe_payment_link_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    plan: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="paid", nullable=False, index=True)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    existing_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notification_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    assigned_phone: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)
    telnyx_number_order_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    onboarding_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    onboarding_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    redirect_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    redirect_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    onboarding_data_json: Mapped[dict | None] = mapped_column(JSON_DOCUMENT, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class StripeWebhookEvent(Base):
    """Minimal immutable Stripe event ledger used for idempotent fulfillment."""
    __tablename__ = "stripe_webhook_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stripe_event_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    livemode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class LeadCaptureRecord(Base):
    """Normalized inbound inquiry shared by website, phone, SMS, and forms."""
    __tablename__ = "lead_capture_records"
    __table_args__ = (
        UniqueConstraint("organization_id", "source", "external_id", name="uq_lead_capture_source_external"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="new", nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)
    owner_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    next_action: Mapped[str | None] = mapped_column(String(255), nullable=True)
    next_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON_DOCUMENT, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


# ── Telemetry Models ──

class AIRequestLog(Base):
    """Every AI request logged for observability."""
    __tablename__ = "ai_request_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    feature: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float] = mapped_column(Numeric(10, 6), default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    parse_success: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    parse_method: Mapped[str | None] = mapped_column(String(20), nullable=True)  # "json", "markdown", "raw"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)


class MCPToolLog(Base):
    """MCP tool execution log."""
    __tablename__ = "mcp_tool_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    tool_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    arguments: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)


class DailyMetrics(Base):
    """Rolled-up daily metrics for fast dashboard queries."""
    __tablename__ = "daily_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost: Mapped[float] = mapped_column(Numeric(10, 6), default=0)
    avg_latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=100)
    fallback_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0)


# ═══════════════════════════════════════════════════════════
# WORKER RUNTIME PERSISTENCE
# ═══════════════════════════════════════════════════════════

class WorkerSchedule(Base):
    __tablename__ = "worker_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    worker_name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    queue_name: Mapped[str] = mapped_column(String(40), default="normal", nullable=False)
    schedule_type: Mapped[str] = mapped_column(String(30), default="event_triggered", nullable=False)
    cron_expr: Mapped[str | None] = mapped_column(String(120), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_enqueued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class WorkerJob(Base):
    __tablename__ = "worker_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    worker_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    task_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    queue_name: Mapped[str] = mapped_column(String(40), default="normal", nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(30), default="event", nullable=False)
    event_type: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="queued", nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)
    retries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    enqueued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WorkerRun(Base):
    __tablename__ = "worker_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    worker_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    task_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("worker_jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="running", nullable=False, index=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    runtime_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WorkerMetricSnapshot(Base):
    __tablename__ = "worker_metric_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    worker_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    queue_name: Mapped[str] = mapped_column(String(40), default="normal", nullable=False)
    current_job_id: Mapped[int | None] = mapped_column(ForeignKey("worker_jobs.id", ondelete="SET NULL"), nullable=True)
    jobs_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    jobs_succeeded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    jobs_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_runtime_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    facts_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    facts_verified: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    relationships_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    insights_generated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    entities_enriched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    queue_depth: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class WorkerFailure(Base):
    __tablename__ = "worker_failures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    worker_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    task_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("worker_jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    error_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    traceback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)


class WorkerDeadLetter(Base):
    __tablename__ = "worker_dead_letters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    worker_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    task_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    queue_name: Mapped[str] = mapped_column(String(40), default="normal", nullable=False)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="queued", nullable=False)
    failed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
    replayed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    companies_analyzed: Mapped[int] = mapped_column(Integer, default=0)
    proposals_generated: Mapped[int] = mapped_column(Integer, default=0)
    health_score: Mapped[int] = mapped_column(Integer, default=100)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


# ── Lead Intelligence ──

class Lead(Base):
    """AI-powered sales research workspace — discovered companies awaiting approval before CRM import."""
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employees: Mapped[int | None] = mapped_column(Integer, nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    province: Mapped[str | None] = mapped_column(String(120), nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    revenue_estimate: Mapped[str | None] = mapped_column(Text, nullable=True)
    opportunity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    buying_signals: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_services: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_value: Mapped[str | None] = mapped_column(String(50), nullable=True)
    estimated_deal_low: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_deal_high: Mapped[int | None] = mapped_column(Integer, nullable=True)
    technology_maturity: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="new", nullable=False, index=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    pns_fit_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pns_fit_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_stages: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_makers_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    outreach_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_researched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    imported_company_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    enrichment_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    enrichment_job_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    google_maps_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_recommendation_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    website_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviews_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    linkedin_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class FollowUpAction(Base):
    """Immutable audit ledger for every follow-up state transition."""
    __tablename__ = "follow_up_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "task", "lead"
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(30), nullable=False)  # "completed", "rescheduled", "assigned"
    old_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class LeadTimelineEvent(Base):
    """Chronological history for every lead — continues after CRM import."""
    __tablename__ = "lead_timeline_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    lead_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class SavedSearch(Base):
    """User-saved discovery filters for one-click prospect research."""
    __tablename__ = "saved_searches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    filters_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class EnrichmentJob(Base):
    """Tracks background AI enrichment for each lead in the Intelligence Pipeline."""
    __tablename__ = "enrichment_jobs"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    lead_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    discovery_source: Mapped[str] = mapped_column(String(50), default="ai_discovery", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="queued", nullable=False, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CompanyDocument(Base):
    """Documents attached to CRM companies — proposals, contracts, specs, etc."""
    __tablename__ = "company_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    extension: Mapped[str] = mapped_column(String(20), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    uploaded_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


# ═══════════════════════════════════════════════════════════
# TRANSCRIPT — conversation intelligence storage
# ═══════════════════════════════════════════════════════════

class Transcript(Base):
    """A complete transcript of a conversation."""
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    call_id: Mapped[int | None] = mapped_column(ForeignKey("calls.id", ondelete="SET NULL"), nullable=True, index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(50), default="deepgram")
    provider_transcript_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # ── Sprint 42: Full transcript content ──
    full_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    utterance_count: Mapped[int] = mapped_column(Integer, default=0)

    # ── Timing ──
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)

    # ── Recording ──
    recording_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    recording_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    diarization_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── Metadata ──
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class TranscriptSegment(Base):
    """A single utterance within a transcript."""
    __tablename__ = "transcript_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    transcript_id: Mapped[int] = mapped_column(ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False, index=True)
    speaker: Mapped[str] = mapped_column(String(50), default="Speaker 0")
    speaker_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    start_time: Mapped[float] = mapped_column(Numeric(10, 3), default=0.0)
    end_time: Mapped[float] = mapped_column(Numeric(10, 3), default=0.0)
    confidence: Mapped[float] = mapped_column(Numeric(5, 3), default=0.0)
    is_final: Mapped[bool] = mapped_column(Boolean, default=False)
    sequence: Mapped[int] = mapped_column(Integer, default=0)
    words_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    segment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class ConversationInsight(Base):
    """Extracted business intelligence from transcript analysis.

    Every insight has a lifecycle: Detected → Verified → Resolved/Archived.
    Supports future learning and human feedback loops.
    """
    __tablename__ = "conversation_insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    transcript_id: Mapped[int] = mapped_column(ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, default=50)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    speaker: Mapped[str | None] = mapped_column(String(50), nullable=True)
    segment_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Lifecycle ──
    status: Mapped[str] = mapped_column(String(20), default="detected", nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(20), default="transcript", nullable=False)
    created_by: Mapped[str] = mapped_column(String(20), default="ai", nullable=False)
    verified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class Call(Base):
    """Telephony calls — outbound and inbound, associated with CRM companies.

    Sprint 48.1 — Upgraded from partial to full persistent call lifecycle.
    Every Telnyx call creates one Call row that survives process restarts.
    """
    __tablename__ = "calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    public_uuid: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True)
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True)
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    activity_id: Mapped[int | None] = mapped_column(ForeignKey("activities.id", ondelete="SET NULL"), nullable=True)
    owner_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ── Session identity ──
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="telnyx")
    provider_call_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    provider_leg_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # ── Call details ──
    direction: Mapped[str] = mapped_column(String(20), nullable=False, default="outbound")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="idle", index=True)
    outcome: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(50), nullable=False)
    caller_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    normalized_caller_number: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    normalized_destination_number: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    # ── Timing ──
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ringing_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    agent_talk_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prospect_talk_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    silence_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Termination ──
    disconnect_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Recording ──
    recording_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    recording_status: Mapped[str] = mapped_column(String(20), default="none")

    # ── Pipeline stages ──
    transcript_status: Mapped[str] = mapped_column(String(20), default="none")
    post_call_status: Mapped[str] = mapped_column(String(20), default="none")

    # ── Phase 1 Intake ──
    spam_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    spam_reasons: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    sms_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sms_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sms_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ── Metadata ──
    provider_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON_DOCUMENT, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


# ══════════════════════════════════════════════════════════════
# Automation Assessment + Transactional Outbox
# ══════════════════════════════════════════════════════════════

class AutomationAssessment(Base):
    """Website automation assessment — raw answers + calculated results."""
    __tablename__ = "automation_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)

    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True)

    assessment_version: Mapped[str] = mapped_column(String(20), nullable=False)
    scoring_model_version: Mapped[str] = mapped_column(String(20), default="1.0")
    recommendation_model_version: Mapped[str] = mapped_column(String(20), default="1.0")

    raw_answers: Mapped[dict] = mapped_column(JSON_DOCUMENT, nullable=False)
    calculated_output: Mapped[dict] = mapped_column(JSON_DOCUMENT, nullable=False)

    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    employee_range: Mapped[str | None] = mapped_column(String(50), nullable=True)
    automation_score: Mapped[int] = mapped_column(Integer, default=0)
    estimated_annual_savings: Mapped[int] = mapped_column(Integer, default=0)
    estimated_weekly_hours: Mapped[int] = mapped_column(Integer, default=0)
    estimated_annual_hours: Mapped[int] = mapped_column(Integer, default=0)
    estimated_people_count: Mapped[int] = mapped_column(Integer, default=0)
    primary_pain_points: Mapped[list | None] = mapped_column(JSON_DOCUMENT, nullable=True)

    privacy_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    marketing_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    utm_source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    utm_medium: Mapped[str | None] = mapped_column(String(120), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(120), nullable=True)
    referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    landing_page: Mapped[str | None] = mapped_column(String(500), nullable=True)

    idempotency_key: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    assessment_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    pdf_status: Mapped[str] = mapped_column(String(20), default="pending")
    pdf_storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pdf_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Sprint 47.9 — Assessment Intelligence ──
    primary_pain_point: Mapped[str | None] = mapped_column(String(255), nullable=True)
    secondary_pain_points: Mapped[list | None] = mapped_column(JSON_DOCUMENT, nullable=True)
    current_process_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_solution_categories: Mapped[list | None] = mapped_column(JSON_DOCUMENT, nullable=True)
    recommendation_reasons: Mapped[list | None] = mapped_column(JSON_DOCUMENT, nullable=True)
    urgency: Mapped[str | None] = mapped_column(String(20), nullable=True)
    buying_signals: Mapped[list | None] = mapped_column(JSON_DOCUMENT, nullable=True)
    likely_decision_maker: Mapped[str | None] = mapped_column(String(255), nullable=True)
    project_size_band: Mapped[str | None] = mapped_column(String(20), nullable=True)
    next_best_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    discovery_questions: Mapped[list | None] = mapped_column(JSON_DOCUMENT, nullable=True)
    intelligence_json: Mapped[dict | None] = mapped_column(JSON_DOCUMENT, nullable=True)
    intelligence_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    intelligence_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    intelligence_confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)

    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class EmailMessage(Base):
    """Email communications — outbound and inbound, with threading support.

    Sprint 48.2 — New model for email ingestion and delivery logging.
    Supports Zoho Mail SMTP (outbound) and IMAP (inbound) ingestion.
    """
    __tablename__ = "email_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    public_uuid: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id", ondelete="SET NULL"), nullable=True)
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True)
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    activity_id: Mapped[int | None] = mapped_column(ForeignKey("activities.id", ondelete="SET NULL"), nullable=True)
    owner_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ── Threading ──
    provider_message_id: Mapped[str | None] = mapped_column(String(500), nullable=True, unique=True, index=True)
    provider_thread_id: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    internet_message_id: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    in_reply_to: Mapped[str | None] = mapped_column(String(500), nullable=True)
    references: Mapped[str | None] = mapped_column(Text, nullable=True)
    thread_id: Mapped[int | None] = mapped_column(ForeignKey("email_messages.id", ondelete="SET NULL"), nullable=True, index=True)

    # ── Direction + status ──
    direction: Mapped[str] = mapped_column(String(20), nullable=False, default="outbound", index=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="email")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    delivery_status: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # ── Participants ──
    from_address: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    normalized_from: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    to_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    cc_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    bcc_address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Content ──
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    plain_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    html_reference: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Timing ──
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Provider ──
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="zoho")
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    provider_metadata: Mapped[dict | None] = mapped_column(JSON_DOCUMENT, nullable=True)

    # ── Metadata ──
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class OutboxEvent(Base):
    """Transactional outbox — events for async worker processing."""
    __tablename__ = "outbox_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    payload_json: Mapped[dict] = mapped_column(JSON_DOCUMENT, nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True, index=True)

    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    leased_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lease_holder: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class ProviderWebhookEvent(Base):
    """Immutable provider webhook event ledger. Unique on provider event id.
    Each Telnyx webhook is persisted once and never mutated.
    """
    __tablename__ = "provider_webhook_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider_event_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="telnyx")
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    call_control_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    call_leg_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    payload_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    processing_status: Mapped[str] = mapped_column(String(20), nullable=False, default="received", index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class PhoneSuppression(Base):
    """Durable opt-out registry. STOP/START workflow for SMS compliance."""
    __tablename__ = "phone_suppressions"
    __table_args__ = (
        UniqueConstraint("organization_id", "normalized_phone", name="uq_phone_suppressions_org_phone"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(50), nullable=False)
    normalized_phone: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="suppressed")
    reason: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
