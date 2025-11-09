"""Application settings and configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "HarmoniAPI"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost/harmoni"

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Stripe
    stripe_secret_key: str = ""
    stripe_public_key: str = ""
    stripe_webhook_secret: str = ""

    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Admin
    first_admin_email: str
    first_admin_password: str

    # File Upload
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 10

    # Calculator
    calculator_calorie_deficit: int = 500
    calculator_calorie_surplus: int = 300
    calculator_min_age: int = 15
    calculator_max_age: int = 120
    calculator_min_weight_kg: int = 30
    calculator_max_weight_kg: int = 300
    calculator_min_height_cm: int = 100
    calculator_max_height_cm: int = 250


settings = Settings()
