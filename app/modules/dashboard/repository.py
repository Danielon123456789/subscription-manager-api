from sqlalchemy import select
from app.models.subscription import (
    Subscription,
    SubscriptionStatus,
    SubscriptionBillingCycle,
)
from sqlalchemy.orm import Session
from datetime import date


def create(db: Session, subscription: Subscription) -> Subscription:
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


def get_by_id(
    db: Session, subscription_id: int, subscription_owner_id: int
) -> Subscription | None:
    stmt = select(Subscription).where(
        Subscription.id == subscription_id,
        Subscription.owner_id == subscription_owner_id,
    )
    result = db.execute(stmt).scalar_one_or_none()
    return result


def get_by_owner(
    db: Session,
    owner_id: int,
    status: SubscriptionStatus | None = None,
    billing_cycle: SubscriptionBillingCycle | None = None,
) -> list[Subscription]:
    stmt = select(Subscription).where(Subscription.owner_id == owner_id)

    if status is not None:
        stmt = stmt.where(Subscription.status == status)
    if billing_cycle is not None:
        stmt = stmt.where(Subscription.billing_cycle == billing_cycle)

    result = db.execute(stmt).scalars().all()

    return result


def update(
    db: Session,
    subscription_id: int,
    subscription_owner_id: int,
    subscription_items: dict,
) -> Subscription | None:
    subscription = get_by_id(
        db=db,
        subscription_id=subscription_id,
        subscription_owner_id=subscription_owner_id,
    )

    if subscription is None:
        return None

    for key, value in subscription_items.items():
        setattr(subscription, key, value)

    db.commit()
    db.refresh(subscription)
    return subscription


def cancel_now(
    db: Session, subscription_id: int, subscription_owner_id: int
) -> Subscription | None:
    subscription = update(
        db=db,
        subscription_id=subscription_id,
        subscription_owner_id=subscription_owner_id,
        subscription_items={"status": SubscriptionStatus.CANCELLED},
    )
    return subscription


def schedule_cancel(
    db: Session, subscription_id: int, subscription_owner_id: int, cancel_date: date
) -> Subscription | None:
    subscription = update(
        db=db,
        subscription_id=subscription_id,
        subscription_owner_id=subscription_owner_id,
        subscription_items={"cancel_at": cancel_date},
    )
    return subscription


def get_due_for_cancellation(db: Session, cancel_date: date) -> list[Subscription]:
    stmt = select(Subscription).where(
        Subscription.cancel_at <= cancel_date,
        Subscription.status != SubscriptionStatus.CANCELLED,
    )
    result = db.execute(stmt).scalars().all()
    return result
