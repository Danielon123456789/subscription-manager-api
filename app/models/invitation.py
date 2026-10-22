from datetime import datetime, timezone
import enum

from sqlalchemy import DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class StatusInvitation(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Invitation(Base):
    __tablename__ = "invitations"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    inviter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    status: Mapped[StatusInvitation] = mapped_column(
        Enum(
            StatusInvitation,
            native_enum=False,
            create_constraint=True,
            values_callable=lambda enum_class: [values.value for values in enum_class],
        ),
        default=StatusInvitation.PENDING,
    )
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
