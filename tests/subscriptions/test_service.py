from datetime import date
from decimal import Decimal


from app.models.subscription import (
    SubscriptionBillingCycle,
    Subscription,
    SubscriptionStatus,
)
from app.modules.subscriptions.schemas import SubscriptionCreate, SubscriptionUpdate
from app.modules.subscriptions.service import (
    create_subscription,
    update_subscription,
    cancel_due_subscriptions,
    cancel_now_subscription,
)
from app.models.user import User


def test_create_subscription_uses_owner_id_argument_not_payload(db_session):
    user = User(email="owner@test.com", password_hash="fake")
    db_session.add(user)
    db_session.commit()

    payload = SubscriptionCreate(
        name="Netflix",
        amount=199,
        currency="MXN",
        billing_cycle=SubscriptionBillingCycle.MONTHLY,
        start_date=date(2026, 1, 31),
    )

    result = create_subscription(
        db=db_session, owner_id=user.id, subscription_info=payload
    )

    assert result.next_billing_date.day == 31


def test_partial_update_does_not_overwrite_unsent_fields(db_session):
    user = User(email="patch@test.com", password_hash="fake")
    db_session.add(user)
    db_session.commit()

    subscription = Subscription(
        owner_id=user.id,
        name="Netflix",
        description="Plan familiar",
        amount=Decimal("199.00"),
        currency="MXN",
        billing_cycle=SubscriptionBillingCycle.MONTHLY,
        status=SubscriptionStatus.ACTIVE,
        start_date=date(2026, 1, 15),
        next_billing_date=date(2026, 8, 15),
        payment_method="Visa 4242",
        category="Entretenimiento",
        website_url="https://netflix.com",
    )
    db_session.add(subscription)
    db_session.commit()

    result = update_subscription(
        db=db_session,
        subscription_id=subscription.id,
        owner_id=user.id,
        subscription_info=SubscriptionUpdate(amount=Decimal("250.00")),
    )

    assert result.amount == Decimal("250.00")
    assert result.name == "Netflix"
    assert result.description == "Plan familiar"
    assert result.currency == "MXN"
    assert result.billing_cycle == SubscriptionBillingCycle.MONTHLY
    assert result.start_date == date(2026, 1, 15)
    assert result.payment_method == "Visa 4242"
    assert result.category == "Entretenimiento"
    assert result.website_url == "https://netflix.com"


def test_cancel_due_subscriptions_only_cancels_due_and_active_ones(db_session):
    user = User(email="celery@test.com", password_hash="fake")
    db_session.add(user)
    db_session.commit()

    def make_subscription(name, cancel_at, status):
        return Subscription(
            owner_id=user.id,
            name=name,
            amount=Decimal("100.00"),
            currency="MXN",
            billing_cycle=SubscriptionBillingCycle.MONTHLY,
            status=status,
            start_date=date(2026, 1, 1),
            next_billing_date=date(2026, 7, 1),
            cancel_at=cancel_at,
        )

    due_active = make_subscription(
        "Due active", date(2026, 6, 10), SubscriptionStatus.ACTIVE
    )
    due_already_cancelled = make_subscription(
        "Due already cancelled", date(2026, 6, 10), SubscriptionStatus.CANCELLED
    )
    future_cancel = make_subscription(
        "Future cancel", date(2026, 12, 31), SubscriptionStatus.ACTIVE
    )
    never_scheduled = make_subscription(
        "Never scheduled", None, SubscriptionStatus.ACTIVE
    )

    db_session.add_all(
        [due_active, due_already_cancelled, future_cancel, never_scheduled]
    )
    db_session.commit()

    result = cancel_due_subscriptions(db=db_session, cancel_date=date(2026, 6, 15))

    db_session.expire_all()

    assert due_active.status == SubscriptionStatus.CANCELLED
    assert due_already_cancelled.status == SubscriptionStatus.CANCELLED
    assert future_cancel.status == SubscriptionStatus.ACTIVE
    assert never_scheduled.status == SubscriptionStatus.ACTIVE

    assert result["cancelled_count"] == 1
    assert result["cancelled_ids"] == [due_active.id]


def test_cancel_now_is_idempotent(db_session):
    user = User(email="idempotent@test.com", password_hash="fake")
    db_session.add(user)
    db_session.commit()

    subscription = Subscription(
        owner_id=user.id,
        name="Spotify",
        amount=Decimal("129.00"),
        currency="MXN",
        billing_cycle=SubscriptionBillingCycle.MONTHLY,
        status=SubscriptionStatus.ACTIVE,
        start_date=date(2026, 1, 1),
        next_billing_date=date(2026, 8, 1),
    )
    db_session.add(subscription)
    db_session.commit()

    first = cancel_now_subscription(
        db=db_session, subscription_id=subscription.id, owner_id=user.id
    )
    second = cancel_now_subscription(
        db=db_session, subscription_id=subscription.id, owner_id=user.id
    )

    assert first.status == SubscriptionStatus.CANCELLED
    assert second.status == SubscriptionStatus.CANCELLED


def test_create_subscription_with_trial_end_date_sets_trial_status(db_session):
    user = User(email="trial@test.com", password_hash="fake")
    db_session.add(user)
    db_session.commit()

    payload = SubscriptionCreate(
        name="Disney+",
        amount=Decimal("159.00"),
        currency="MXN",
        billing_cycle=SubscriptionBillingCycle.MONTHLY,
        start_date=date(2026, 3, 1),
        trial_end_date=date(2026, 3, 31),
    )

    result = create_subscription(
        db=db_session, owner_id=user.id, subscription_info=payload
    )

    assert result.status == SubscriptionStatus.TRIAL


def test_update_start_date_recalculates_next_billing_date(db_session):
    user = User(email="recalc@test.com", password_hash="fake")
    db_session.add(user)
    db_session.commit()

    subscription = Subscription(
        owner_id=user.id,
        name="HBO Max",
        amount=Decimal("149.00"),
        currency="MXN",
        billing_cycle=SubscriptionBillingCycle.MONTHLY,
        status=SubscriptionStatus.ACTIVE,
        start_date=date(2026, 1, 5),
        next_billing_date=date(2026, 8, 5),
    )
    db_session.add(subscription)
    db_session.commit()

    result = update_subscription(
        db=db_session,
        subscription_id=subscription.id,
        owner_id=user.id,
        subscription_info=SubscriptionUpdate(start_date=date(2027, 3, 20)),
    )

    assert result.next_billing_date == date(2027, 3, 20)
