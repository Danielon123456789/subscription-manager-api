from datetime import datetime, timezone
import enum

from sqlalchemy import DateTime, ForeignKey, Enum, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class GroupRole(enum.Enum):
    OWNER = "owner"
    MEMBER = "member"


class GroupMember(Base):
    __tablename__ = "group_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[GroupRole] = mapped_column(
        Enum(
            GroupRole,
            native_enum=False,
            create_constraint=True,
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_member"),)
