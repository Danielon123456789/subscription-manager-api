from sqlalchemy.orm import Session
from app.modules.subscriptions import repository as repositorySubscriptions
from app.modules.groups import repository as repositoryGroup
from app.modules.groups import service


def get_user_summary(db: Session, user_id: int) -> int:
    summary = repositorySubscriptions.get_total_amount_by_owner(db=db, owner_id=user_id)
    return summary


def get_group_summary(db: Session, group_id: int, user_id: int) -> tuple[int, int]:
    service.validate_member(db=db, group_id=group_id, user_id=user_id)

    members_info = repositoryGroup.get_members(db=db, group_id=group_id)

    members_ids = [member.user_id for member in members_info]

    summary = repositorySubscriptions.get_total_amount_by_owners(
        db=db, owner_ids=members_ids
    )

    return summary, len(members_ids)
