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

    # Cookies
    cookie_domain: str = ""  # empty for localhost, ".arcadeforge.io" for prod
    cookie_secure: str = ""  # empty = auto-detect from app_env; "true"/"false" to override

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/arcadeforge"
    database_ssl: bool = False  # set True for Neon / cloud Postgres

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Storage
    storage_driver: str = "local"  # "local" or "s3"
    storage_local_path: str = "./data"

    # S3-compatible storage (MinIO / AWS S3 / Cloudflare R2)
    s3_bucket: str = "arcadeforge"
    s3_region: str = "us-east-1"
    s3_endpoint_url: str = ""  # e.g. "http://localhost:9000" for MinIO
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""

    # Sandbox
    sandbox_driver: str = "docker"  # "docker" or "fly"
    sandbox_image_name: str = "arcadeforge-sandbox:latest"
    sandbox_session_ttl_seconds: int = 1800
    sandbox_cpu_limit: float = 1.0
    sandbox_mem_limit_mb: int = 1024
    sandbox_disable_network: bool = True
    sandbox_ws_base_url: str = "ws://localhost"

    # Fly.io Machines (used when sandbox_driver == "fly")
    fly_api_token: str = ""
    fly_sandbox_app: str = "arcadeforge-sandbox"
    fly_sandbox_region: str = "iad"

    # Logging
    log_level: str = "INFO"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",")]


settings = Settings()
