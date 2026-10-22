from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    ENVIRONMENT: str
    SMTP_API_KEY: SecretStr
    SENDER_EMAIL: str

    class Config:
        env_file = ".env"


settings = Settings()
