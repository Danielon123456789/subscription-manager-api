from datetime import date
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from app.modules.subscriptions import repository
from app.models.subscription import (
    SubscriptionBillingCycle,
    SubscriptionStatus,
    Subscription,
)
from app.modules.subscriptions.schemas import (
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionUpdate,
)

CYCLE_TO_RELATIVEDELTA_UNIT = {
    SubscriptionBillingCycle.MONTHLY: "months",
    SubscriptionBillingCycle.YEARLY: "years",
    SubscriptionBillingCycle.WEEKLY: "weeks",
}


def calculate_next_billing_date(
    start_date: date, billing_cycle: SubscriptionBillingCycle
) -> date:
    unit = CYCLE_TO_RELATIVEDELTA_UNIT[billing_cycle]
    today = date.today()

    cycles = 0
    next_date = start_date

    while next_date < today:
        cycles += 1
        next_date = start_date + relativedelta(**{unit: cycles})

    return next_date


def get_owned_subscription_or_raise(
    db: Session, subscription_id: int, owner_id: int
) -> Subscription:
    subscription = repository.get_by_id(
        db=db, subscription_id=subscription_id, subscription_owner_id=owner_id
    )
    if subscription is None:
        raise ValueError("Subscription not found")
    return subscription


def create_subscription(
    db: Session, owner_id: int, subscription_info: SubscriptionCreate
) -> SubscriptionResponse:
    status = (
        SubscriptionStatus.ACTIVE
        if subscription_info.trial_end_date is None
        else SubscriptionStatus.TRIAL
    )

    next_billing_date = calculate_next_billing_date(
        start_date=subscription_info.start_date,
        billing_cycle=subscription_info.billing_cycle,
    )

    subscription = Subscription(
        **subscription_info.model_dump(),
        owner_id=owner_id,
        status=status,
        next_billing_date=next_billing_date,
    )

    subscription_created = repository.create(db=db, subscription=subscription)

    subscription_response = SubscriptionResponse.model_validate(subscription_created)

    return subscription_response


def get_subscription_by_id(
    db: Session, subscription_id: int, owner_id: int
) -> SubscriptionResponse:
    subscription = get_owned_subscription_or_raise(
        db=db, subscription_id=subscription_id, owner_id=owner_id
    )

    subscription_response = SubscriptionResponse.model_validate(subscription)

    return subscription_response


def get_subscriptions_by_owner(
    db: Session,
    owner_id: int,
    status: SubscriptionStatus | None = None,
    billing_cycle: SubscriptionBillingCycle | None = None,
) -> list[SubscriptionResponse]:
    subscriptions_list = repository.get_by_owner(
        db=db, owner_id=owner_id, status=status, billing_cycle=billing_cycle
    )

    subscriptions_response_list = [
        SubscriptionResponse.model_validate(subscription)
        for subscription in subscriptions_list
    ]

    return subscriptions_response_list


def update_subscription(
    db: Session,
    subscription_id: int,
    owner_id: int,
    subscription_info: SubscriptionUpdate,
) -> SubscriptionResponse:
    subscription = get_owned_subscription_or_raise(
        db=db, subscription_id=subscription_id, owner_id=owner_id
    )

    subscription_items = subscription_info.model_dump(exclude_unset=True)

    if "start_date" in subscription_items or "billing_cycle" in subscription_items:
        start_date = subscription_items.get("start_date", subscription.start_date)
        billing_cycle = subscription_items.get(
            "billing_cycle", subscription.billing_cycle
        )
        next_billing_date = calculate_next_billing_date(
            start_date=start_date, billing_cycle=billing_cycle
        )
        subscription_items["next_billing_date"] = next_billing_date

    subscription_updated = repository.update(
        db=db,
        subscription_id=subscription_id,
        subscription_owner_id=owner_id,
        subscription_items=subscription_items,
    )

    subscription_response = SubscriptionResponse.model_validate(subscription_updated)

    return subscription_response


def cancel_now_subscription(
    db: Session, subscription_id: int, owner_id: int
) -> SubscriptionResponse:
    get_owned_subscription_or_raise(
        db=db, subscription_id=subscription_id, owner_id=owner_id
    )

    subscription_cancelled = repository.cancel_now(
        db=db, subscription_id=subscription_id, subscription_owner_id=owner_id
    )

    subscription_response = SubscriptionResponse.model_validate(subscription_cancelled)

    return subscription_response


def schedule_cancel_subscription(
    db: Session, subscription_id: int, owner_id: int, cancel_date: date
) -> SubscriptionResponse:
    get_owned_subscription_or_raise(
        db=db, subscription_id=subscription_id, owner_id=owner_id
    )

    subscription_cancelled_at = repository.schedule_cancel(
        db=db,
        subscription_id=subscription_id,
        subscription_owner_id=owner_id,
        cancel_date=cancel_date,
    )

    subscription_response = SubscriptionResponse.model_validate(
        subscription_cancelled_at
    )

    return subscription_response


def cancel_due_subscriptions(db: Session, cancel_date: date) -> dict[str, int]:
    subscriptions = repository.get_due_for_cancellation(db=db, cancel_date=cancel_date)

    cancelled_subscriptions = []

    for subscription in subscriptions:
        cancelled_subscriptions.append(
            repository.cancel_now(
                db=db,
                subscription_id=subscription.id,
                subscription_owner_id=subscription.owner_id,
            )
        )

    cancellation_summary = {
        "cancelled_count": len(cancelled_subscriptions),
        "cancelled_ids": [subscription.id for subscription in cancelled_subscriptions],
    }

    return cancellation_summary
