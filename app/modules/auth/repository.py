from sqlalchemy import select
from app.models.user import User
from sqlalchemy.orm import Session


def get_by_email(db: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    result = db.execute(stmt).scalar_one_or_none()
    return result


def create(db: Session, user: User) -> User:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
