"""Core CRM data model: Company and Contact.

Kept deliberately small for now. Email-campaign and activity models arrive in
later phases; the fields here already carry what prospecting hands us.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255))
    website: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)

    city: Mapped[Optional[str]] = mapped_column(String(120))
    region: Mapped[Optional[str]] = mapped_column(String(120))  # state / province
    country: Mapped[Optional[str]] = mapped_column(String(120))

    naics_code: Mapped[Optional[str]] = mapped_column(String(12))
    naics_description: Mapped[Optional[str]] = mapped_column(String(255))
    employee_range: Mapped[Optional[str]] = mapped_column(String(40))
    revenue_range: Mapped[Optional[str]] = mapped_column(String(40))

    category: Mapped[Optional[str]] = mapped_column(String(60))  # Distributor / Brand / Competitor
    status: Mapped[str] = mapped_column(String(40), default="lead")
    source: Mapped[str] = mapped_column(String(40), default="manual")  # manual / explorium
    external_id: Mapped[Optional[str]] = mapped_column(String(80))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    contacts: Mapped[List["Contact"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
        order_by="Contact.last_name",
    )

    @property
    def city_title(self) -> Optional[str]:
        return self.city.title() if self.city else None

    @property
    def region_title(self) -> Optional[str]:
        return self.region.title() if self.region else None

    @property
    def location(self) -> str:
        parts = [p for p in (self.city_title, self.region_title) if p]
        return ", ".join(parts)

    @property
    def initial(self) -> str:
        return (self.name or "?").strip()[:1].upper()


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[Optional[int]] = mapped_column(ForeignKey("companies.id"))

    first_name: Mapped[Optional[str]] = mapped_column(String(120))
    last_name: Mapped[Optional[str]] = mapped_column(String(120))
    full_name: Mapped[Optional[str]] = mapped_column(String(240))
    title: Mapped[Optional[str]] = mapped_column(String(200))
    job_level: Mapped[Optional[str]] = mapped_column(String(80))
    department: Mapped[Optional[str]] = mapped_column(String(80))

    email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(60))
    linkedin: Mapped[Optional[str]] = mapped_column(String(255))

    status: Mapped[str] = mapped_column(String(40), default="lead")
    source: Mapped[str] = mapped_column(String(40), default="manual")
    external_id: Mapped[Optional[str]] = mapped_column(String(80))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    company: Mapped[Optional["Company"]] = relationship(back_populates="contacts")

    @property
    def display_name(self) -> str:
        if self.full_name:
            return self.full_name
        names = [n for n in (self.first_name, self.last_name) if n]
        return " ".join(names) if names else (self.email or "Unknown")


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    subject: Mapped[Optional[str]] = mapped_column(String(300))
    from_name: Mapped[Optional[str]] = mapped_column(String(120))
    from_email: Mapped[Optional[str]] = mapped_column(String(255))
    body: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="draft")  # draft / sent

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    messages: Mapped[List["EmailMessage"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )

    @property
    def recipient_count(self) -> int:
        return len(self.messages)

    @property
    def sent_count(self) -> int:
        return sum(1 for m in self.messages if m.status == "sent")

    @property
    def opened_count(self) -> int:
        return sum(1 for m in self.messages if m.opened_at is not None)

    @property
    def clicked_count(self) -> int:
        return sum(1 for m in self.messages if m.first_clicked_at is not None)

    @property
    def open_rate(self) -> int:
        return round(100 * self.opened_count / self.sent_count) if self.sent_count else 0

    @property
    def click_rate(self) -> int:
        return round(100 * self.clicked_count / self.sent_count) if self.sent_count else 0


class EmailMessage(Base):
    __tablename__ = "email_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))
    contact_id: Mapped[Optional[int]] = mapped_column(ForeignKey("contacts.id"))
    to_email: Mapped[str] = mapped_column(String(255), index=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    status: Mapped[str] = mapped_column(String(40), default="queued")  # queued/sent/failed/skipped
    provider_id: Mapped[Optional[str]] = mapped_column(String(120))
    error: Mapped[Optional[str]] = mapped_column(String(500))

    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    first_clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    open_count: Mapped[int] = mapped_column(default=0)
    click_count: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    campaign: Mapped["Campaign"] = relationship(back_populates="messages")
    events: Mapped[List["EmailEvent"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )

    @property
    def opened(self) -> bool:
        return self.opened_at is not None

    @property
    def clicked(self) -> bool:
        return self.first_clicked_at is not None


class EmailEvent(Base):
    __tablename__ = "email_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("email_messages.id"))
    type: Mapped[str] = mapped_column(String(40))  # open / click / unsubscribe / bounce
    url: Mapped[Optional[str]] = mapped_column(String(1000))
    user_agent: Mapped[Optional[str]] = mapped_column(String(400))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    message: Mapped["EmailMessage"] = relationship(back_populates="events")


class Suppression(Base):
    """Emails that must never be contacted again (unsubscribes, bounces)."""

    __tablename__ = "suppressions"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    reason: Mapped[Optional[str]] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
