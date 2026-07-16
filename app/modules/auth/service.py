from app.core.security import (
    hash_password,
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.models.user import User
from app.modules.auth.schemas import (
    UserCreate,
    LoginData,
    UserResponse,
    TokenResponse,
    RegisterResponse,
)
from app.modules.auth.repository import get_by_email, create
from sqlalchemy.orm import Session


def register(db: Session, user_data: UserCreate) -> RegisterResponse:
    if get_by_email(db, user_data.email) is not None:
        raise ValueError("El email ya esta registrado")

    hash_user = hash_password(user_data.password)
    user = User(email=user_data.email, password_hash=hash_user)
    user_created = create(db, user)

    access_token = create_access_token(user_id=user_created.id)
    refresh_token = create_refresh_token(user_id=user_created.id)

    user_response = UserResponse.model_validate(user_created)

    token_response = TokenResponse(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )

    register_response = RegisterResponse(user=user_response, tokens=token_response)

    return register_response


def login(db: Session, login_data: LoginData) -> RegisterResponse:
    user = get_by_email(db, login_data.email)

    if user is None or not verify_password(login_data.password, user.password_hash):
        raise ValueError("Email o contraseña incorrectos")

    access_token = create_access_token(user_id=user.id)
    refresh_token = create_refresh_token(user_id=user.id)

    user_response = UserResponse.model_validate(user)

    token_response = TokenResponse(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )

    register_response = RegisterResponse(user=user_response, tokens=token_response)

    return register_response
