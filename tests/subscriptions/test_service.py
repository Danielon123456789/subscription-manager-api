from datetime import date

from app.models.subscription import SubscriptionBillingCycle
from app.modules.subscriptions.schemas import SubscriptionCreate
from app.modules.subscriptions.service import create_subscription
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
