import enum
import decimal
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Date, Numeric, Enum, ForeignKey
from datetime import date, datetime, timezone
from app.core.database import Base


class SubscriptionStatus(enum.Enum):
    ACTIVE = "active"
    TRIAL = "trial"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class SubscriptionBillingCycle(enum.Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"
    WEEKLY = "weekly"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    amount: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10))
    billing_cycle: Mapped[SubscriptionBillingCycle] = mapped_column(
        Enum(
            SubscriptionBillingCycle,
            native_enum=False,
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        nullable=False,
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(
            SubscriptionStatus,
            native_enum=False,
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    next_billing_date: Mapped[date] = mapped_column(Date, nullable=False)
    cancel_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    trial_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
