from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.modules.auth.repository import get_by_id
from app.models.user import User
import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    try:
        payload = decode_token(token=token)

        if payload["type"] != "access":
            raise HTTPException(status_code=401, detail="Sin autorizacion")

    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail="Token no valido") from e

    user = get_by_id(db=db, user_id=int(payload["sub"]))

    if user is None:
        raise HTTPException(status_code=401, detail="Usuario no existente")

    return user
