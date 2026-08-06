from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.modules.auth.repository import get_by_id
from app.models.user import User
import jwt

security_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_token(token=token)

        if payload["type"] != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")

    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e

    user = get_by_id(db=db, user_id=int(payload["sub"]))

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user
