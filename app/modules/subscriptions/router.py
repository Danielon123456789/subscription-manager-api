from app.core.database import get_db
from app.models.user import User
from app.modules.auth.dependencies import get_current_user
from app.modules.subscriptions import service
from app.modules.subscriptions.schemas import (
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionStatus,
    SubscriptionBillingCycle,
    SubscriptionUpdate,
    ScheduleCancelRequest,
)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/subscriptions", status_code=201)
def subscription_create_endpoint(
    subscription_info: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubscriptionResponse:
    new_subscription = service.create_subscription(
        db=db, owner_id=current_user.id, subscription_info=subscription_info
    )
    return new_subscription


@router.get("/subscriptions", status_code=200)
def subscription_by_owner_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: SubscriptionStatus | None = None,
    billing_cycle: SubscriptionBillingCycle | None = None,
) -> list[SubscriptionResponse]:
    subscriptions = service.get_subscriptions_by_owner(
        db=db, owner_id=current_user.id, status=status, billing_cycle=billing_cycle
    )

    return subscriptions


@router.get("/subscriptions/{subscription_id}", status_code=200)
def subscriptions_by_id_endpoint(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubscriptionResponse:
    try:
        subscription = service.get_subscription_by_id(
            db=db, subscription_id=subscription_id, owner_id=current_user.id
        )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.patch("/subscriptions/{subscription_id}", status_code=200)
def update_subscription_endpoint(
    subscription_info: SubscriptionUpdate,
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubscriptionResponse:
    try:
        subscription = service.update_subscription(
            db=db,
            subscription_id=subscription_id,
            owner_id=current_user.id,
            subscription_info=subscription_info,
        )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/subscriptions/{subscription_id}", status_code=200)
def delete_subscription_endpoint(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubscriptionResponse:
    try:
        subscription = service.cancel_now_subscription(
            db=db, subscription_id=subscription_id, owner_id=current_user.id
        )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/subscriptions/{subscription_id}/schedule-cancel", status_code=200)
def schedule_cancel_subscriptions_endpoint(
    subscription_id: int,
    cancel_request: ScheduleCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubscriptionResponse:
    try:
        cancel_date = cancel_request.cancel_at
        subscription = service.schedule_cancel_subscription(
            db=db,
            subscription_id=subscription_id,
            owner_id=current_user.id,
            cancel_date=cancel_date,
        )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
