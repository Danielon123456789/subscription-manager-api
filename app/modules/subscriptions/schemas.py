from pydantic import BaseModel, Field, field_validator
from datetime import date
from app.models.subscription import SubscriptionBillingCycle, SubscriptionStatus
from decimal import Decimal


class SubscriptionCreate(BaseModel):
    name: str
    description: str | None = None
    amount: Decimal = Field(gt=0)
    currency: str
    billing_cycle: SubscriptionBillingCycle
    start_date: date = Field(default_factory=date.today)
    trial_end_date: date | None = None
    payment_method: str | None = None
    category: str | None = None
    website_url: str | None = None


class SubscriptionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    currency: str | None = None
    billing_cycle: SubscriptionBillingCycle | None = None
    start_date: date | None = None
    trial_end_date: date | None = None
    payment_method: str | None = None
    category: str | None = None
    website_url: str | None = None


class SubscriptionResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    amount: Decimal
    currency: str
    billing_cycle: SubscriptionBillingCycle
    status: SubscriptionStatus
    start_date: date
    next_billing_date: date | None = None
    cancel_at: date | None = None
    trial_end_date: date | None = None
    payment_method: str | None = None
    category: str | None = None
    website_url: str | None = None

    model_config = {"from_attributes": True}


class ScheduleCancelRequest(BaseModel):
    cancel_at: date

    @field_validator("cancel_at")
    @classmethod
    def validate_future_date(cls, value: date) -> date:
        if value <= date.today():
            raise ValueError("cancel_at must be a future date")
        return value
