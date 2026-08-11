from app.modules.auth.schemas import UserCreate, LoginData
from app.modules.auth.service import register, login
import pytest


def test_register_rejects_duplicate_email(db_session):
    payload = UserCreate(email="duplicate@test.com", password="password123")

    register(db=db_session, user_data=payload)

    with pytest.raises(ValueError):
        register(db=db_session, user_data=payload)


def test_login_with_wrong_password_raises(db_session):
    register(
        db=db_session,
        user_data=UserCreate(email="login@test.com", password="correct-password"),
    )

    with pytest.raises(ValueError):
        login(
            db=db_session,
            login_data=LoginData(email="login@test.com", password="wrong-password"),
        )
