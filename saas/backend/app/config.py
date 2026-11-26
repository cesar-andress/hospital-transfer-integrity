"""Application settings loaded from environment variables."""

import os


class Settings:
    """Central configuration for the FastAPI backend."""

    PROJECT_NAME: str = "SaaS Multi-Tenant MVP"
    # Override SECRET_KEY in every non-demo environment.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "secreto_super_seguro_mvp_tfg")
    ALGORITHM: str = "HS256"
    # Long-lived demo token (30 days). Shorten for production.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30

    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "saas_db")

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
