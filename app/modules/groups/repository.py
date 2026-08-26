from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from app.models.group import Group
from app.models.group_member import GroupMember, GroupRole


def get_groups_by_user(db: Session, user_id: int) -> list[Group]:
    stmt = (
        select(Group)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .where(
            GroupMember.user_id == user_id,
            Group.deleted_at.is_(None),
        )
    )
    result = db.execute(stmt).scalars().all()
    return result


def get_group_by_id(db: Session, group_id: int) -> Group | None:
    stmt = select(Group).where(Group.id == group_id, Group.deleted_at.is_(None))
    result = db.execute(stmt).scalar_one_or_none()
    return result


def create_group(db: Session, group: Group) -> Group:
    db.add(group)
    db.flush()
    return group


def add_member(
    db: Session, group_id: int, user_id: int, role: GroupRole
) -> GroupMember:
    member = GroupMember(group_id=group_id, user_id=user_id, role=role)
    db.add(member)
    db.flush()
    return member


def get_members(db: Session, group_id: int) -> list[GroupMember]:
    stmt = select(GroupMember).where(GroupMember.group_id == group_id)
    result = db.execute(stmt).scalars().all()
    return result


def get_membership(db: Session, group_id: int, user_id: int) -> GroupMember | None:
    stmt = select(GroupMember).where(
        GroupMember.group_id == group_id, GroupMember.user_id == user_id
    )
    result = db.execute(stmt).scalar_one_or_none()
    return result


def remove_member(db: Session, group_id: int, user_id: int) -> None:
    stmt = delete(GroupMember).where(
        GroupMember.group_id == group_id, GroupMember.user_id == user_id
    )
    db.execute(stmt)


def update_member_role(
    db: Session, group_id: int, user_id: int, role: GroupRole
) -> GroupMember | None:
    member = get_membership(db=db, group_id=group_id, user_id=user_id)
    if member is None:
        return None
    member.role = role
    db.flush()
    return member


def soft_delete_group(db: Session, group_id: int) -> Group | None:
    group = get_group_by_id(db=db, group_id=group_id)
    if group is None:
        return None
    group.deleted_at = datetime.now(timezone.utc)
    db.flush()
    return group
