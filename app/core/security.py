import bcrypt 
import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings

def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"),bcrypt.gensalt())
    return hashed.decode()

def verify_password(plain_password: str,hashed_password: str) -> bool: 
    return bcrypt.checkpw(plain_password.encode("utf-8"),hashed_password.encode("utf-8"))

def create_access_token(user_id: int) -> str:
    
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc)+timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    
    return token
    
def create_refresh_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc)+timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh",
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    
    return token
    
def decode_token(token: str) -> dict:
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    return decoded