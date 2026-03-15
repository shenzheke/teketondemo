from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "tekton-demo-api"
    app_version: str = "2.0.0"
    jwt_secret: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    database_url: str = "sqlite:///./tekton_demo.db"

    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")


settings = Settings()
