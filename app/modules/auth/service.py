from app.core.security import (
    hash_password,
    create_access_token,
    create_refresh_token,
    verify_password,
    decode_token,
)
from app.models.user import User
from app.modules.auth.schemas import (
    UserCreate,
    LoginData,
    UserResponse,
    TokenResponse,
    RegisterResponse,
    RefreshRequest,
    RefreshResponse,
)
from app.modules.auth.repository import get_by_email, create
from sqlalchemy.orm import Session
import jwt


def register(db: Session, user_data: UserCreate) -> RegisterResponse:
    if get_by_email(db, user_data.email) is not None:
        raise ValueError("Email already registered")

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
        raise ValueError("Invalid email or password")

    access_token = create_access_token(user_id=user.id)
    refresh_token = create_refresh_token(user_id=user.id)

    user_response = UserResponse.model_validate(user)

    token_response = TokenResponse(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )

    register_response = RegisterResponse(user=user_response, tokens=token_response)

    return register_response


def refresh(refresh_data: RefreshRequest) -> RefreshResponse:
    try:
        payload = decode_token(token=refresh_data.refresh_token)

        if payload["type"] != "refresh":
            raise ValueError("Invalid token type")

        access_token = create_access_token(user_id=int(payload["sub"]))

        refresh_response = RefreshResponse(
            access_token=access_token, token_type="bearer"
        )

        return refresh_response

    except (jwt.PyJWTError, ValueError) as e:
        raise ValueError("Invalid token") from e
