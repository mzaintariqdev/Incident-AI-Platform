from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://incident_user:incident_pass@localhost:5432/incident_db"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    webhook_secret: str = "dev-webhook-secret"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
