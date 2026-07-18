from app.core.database import get_db
from app.modules.auth.schemas import UserCreate, LoginData, RefreshRequest
from app.modules.auth.service import register, login, refresh
from app.modules.auth.schemas import RegisterResponse, RefreshResponse
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/auth/register", status_code=201)
def register_endpoint(
    user_data: UserCreate, db: Session = Depends(get_db)
) -> RegisterResponse:
    try:
        user_register = register(db, user_data=user_data)
        return user_register
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.post("/auth/login", status_code=200)
def login_endpoint(
    login_data: LoginData, db: Session = Depends(get_db)
) -> RegisterResponse:
    try:
        user_login = login(db, login_data=login_data)
        return user_login
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


@router.post("/auth/refresh", status_code=200)
def refresh_endpoint(refresh_data: RefreshRequest) -> RefreshResponse:
    try:
        refresh_response = refresh(refresh_data=refresh_data)
        return refresh_response
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
