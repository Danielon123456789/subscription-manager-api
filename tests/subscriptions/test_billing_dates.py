from datetime import date

from app.models.subscription import SubscriptionBillingCycle
from app.modules.subscriptions.service import calculate_next_billing_date


def test_monthly_cycle_does_not_drift_after_february():
    result = calculate_next_billing_date(
        start_date=date(2026, 1, 31),
        billing_cycle=SubscriptionBillingCycle.MONTHLY,
        reference_date=date(2026, 8, 5),
    )

    assert result == date(2026, 8, 31)


def test_future_start_date_returns_start_date_unchanged():
    result = calculate_next_billing_date(
        start_date=date(2026, 12, 1),
        billing_cycle=SubscriptionBillingCycle.MONTHLY,
        reference_date=date(2026, 8, 5),
    )

    assert result == date(2026, 12, 1)


def test_leap_day_yearly_clamps_to_february_28():
    result = calculate_next_billing_date(
        start_date=date(2024, 2, 29),
        billing_cycle=SubscriptionBillingCycle.YEARLY,
        reference_date=date(2025, 6, 1),
    )

    assert result == date(2026, 2, 28)


def test_weekly_cycle_advances_seven_days():
    result = calculate_next_billing_date(
        start_date=date(2026, 8, 10),
        billing_cycle=SubscriptionBillingCycle.WEEKLY,
        reference_date=date(2026, 8, 12),
    )
    assert result == date(2026, 8, 17)
