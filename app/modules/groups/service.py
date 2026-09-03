from sqlalchemy.orm import Session
from app.modules.groups import repository
from app.models.group_member import GroupRole, GroupMember
from app.models.group import Group
from app.core.exceptions import InsufficientPermissionError
from app.modules.groups.exceptions import (
    GroupNotFoundError,
    GroupAlreadyMemberError,
    GroupSelfTransferError,
    GroupOwnerMustTransferError,
)
from app.modules.groups.schemas import GroupUpdate


def validate_member(
    db: Session, group_id: int, user_id: int, role: GroupRole | None = None
) -> GroupMember:
    membership = repository.get_membership(db=db, group_id=group_id, user_id=user_id)

    if membership is None:
        raise GroupNotFoundError(
            "Group not found or user is not a member of this group"
        )

    if role is not None and role != membership.role:
        raise InsufficientPermissionError(
            f"User does not have the required role: {role.value}"
        )

    return membership


def create_group(
    db: Session, user_id: int, name: str, description: str | None = None
) -> Group:
    group = Group(name=name, description=description)
    group_created = repository.create_group(db=db, group=group)

    repository.add_member(
        db=db, group_id=group_created.id, user_id=user_id, role=GroupRole.OWNER
    )

    db.commit()

    return group_created


def get_group(db: Session, group_id: int, user_id: int) -> Group:
    validate_member(db=db, group_id=group_id, user_id=user_id)

    group = repository.get_group_by_id(db=db, group_id=group_id)

    return group


def update_group(
    db: Session, group_id: int, user_id: int, group_info: GroupUpdate
) -> Group:
    validate_member(db=db, group_id=group_id, user_id=user_id, role=GroupRole.OWNER)

    group = repository.get_group_by_id(db=db, group_id=group_id)

    group_items = group_info.model_dump(exclude_unset=True)

    for key, value in group_items.items():
        setattr(group, key, value)

    db.commit()

    return group


def add_member(
    db: Session, group_id: int, user_id: int, new_member_id: int
) -> GroupMember:
    validate_member(db=db, group_id=group_id, user_id=user_id, role=GroupRole.OWNER)

    is_member = repository.get_membership(
        db=db, group_id=group_id, user_id=new_member_id
    )

    if is_member is not None:
        raise GroupAlreadyMemberError("User already is a member of this group")

    member = repository.add_member(
        db=db, group_id=group_id, user_id=new_member_id, role=GroupRole.MEMBER
    )

    db.commit()

    return member


def transfer_owner(
    db: Session, group_id: int, user_id: int, new_member_owner_id: int
) -> GroupMember:
    validate_member(db=db, group_id=group_id, user_id=user_id, role=GroupRole.OWNER)

    if user_id == new_member_owner_id:
        raise GroupSelfTransferError("User can't transfer role to himself")

    validate_member(db=db, group_id=group_id, user_id=new_member_owner_id)

    repository.update_member_role(
        db=db, group_id=group_id, user_id=user_id, role=GroupRole.MEMBER
    )

    new_owner = repository.update_member_role(
        db=db, group_id=group_id, user_id=new_member_owner_id, role=GroupRole.OWNER
    )

    db.commit()

    return new_owner


def remove_member(
    db: Session, group_id: int, user_id: int, user_remove_id: int
) -> None:
    user = validate_member(db=db, group_id=group_id, user_id=user_id)

    validate_member(db=db, group_id=group_id, user_id=user_remove_id)

    if user_id == user_remove_id:
        if user.role == GroupRole.OWNER:
            raise GroupOwnerMustTransferError(
                "Owner must transfer ownership before leaving the group"
            )

        repository.remove_member(db=db, group_id=group_id, user_id=user_remove_id)
        db.commit()
        return

    if user.role != GroupRole.OWNER:
        raise InsufficientPermissionError(
            "Only the group owner can remove other members"
        )

    repository.remove_member(db=db, group_id=group_id, user_id=user_remove_id)
    db.commit()
