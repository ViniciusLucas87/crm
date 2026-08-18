"""Isolated product data for the Never Forget controlled MVP."""

from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class NeverForgetServiceRecord(Base):
    __tablename__ = "never_forget_service_records"
    __table_args__ = (
        UniqueConstraint("organization_id", "public_token_hash", name="uq_never_forget_org_token"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    public_token_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    contractor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contractor_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    contractor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    customer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    service_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    job_summary: Mapped[str] = mapped_column(Text, nullable=False)
    completed_on: Mapped[date] = mapped_column(Date, nullable=False)
    invoice_reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    receipt_url: Mapped[str | None] = mapped_column(String(1200), nullable=True)
    work_photo_urls_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    warranty_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    warranty_expires_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    maintenance_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_service_on: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    customer_consented_to_reminders: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False, index=True)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class NeverForgetReminder(Base):
    __tablename__ = "never_forget_reminders"
    __table_args__ = (
        UniqueConstraint(
            "service_record_id",
            "reminder_type",
            "scheduled_for",
            name="uq_never_forget_reminder_schedule",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    service_record_id: Mapped[int] = mapped_column(
        ForeignKey("never_forget_service_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reminder_type: Mapped[str] = mapped_column(String(40), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), default="sms", nullable=False)
    scheduled_for: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(30), default="scheduled", nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class NeverForgetCustomerAction(Base):
    __tablename__ = "never_forget_customer_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    service_record_id: Mapped[int] = mapped_column(
        ForeignKey("never_forget_service_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="new", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
