from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_env: str = "development"
    app_base_url: str = "http://localhost:3000"
    api_base_url: str = "http://localhost:8000"
    app_secret_key: str = "change-me-please-long-random"

    # CORS
    cors_allowed_origins: str = "http://localhost:3000"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/arcadeforge"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Storage
    storage_driver: str = "local"
    storage_local_path: str = "./data"

    # Logging
    log_level: str = "INFO"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",")]


settings = Settings()
