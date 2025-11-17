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

    # Resend
    resend_api_key: str = "hogrider"
    resend_from_email: str = "onboarding@harmoni.com"
    owner_email: str = "harmonifood.main@gmail.com"

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

    # Email Verification
    verification_code_ttl_minutes: int = 10
    verification_code_length: int = 6
    verification_rate_limit_seconds: int = 60
    verification_max_attempts: int = 5

    # Payment Email Templates
    payment_success_email_subject: str = "Оплата успешна - {tariff_name}"
    payment_success_email_body: str = """Здравствуйте, {name}!

Ваш платеж за {tariff_name} прошел успешно!
Сумма: {amount} {currency}

Ваши материалы прикреплены к этому письму.

Спасибо, что выбрали Harmoni!"""

    payment_failure_email_subject: str = "Ошибка оплаты - {tariff_name}"
    payment_failure_email_body: str = """Здравствуйте, {name}!

К сожалению, ваш платеж за {tariff_name} не прошел.
Причина: {reason}

Пожалуйста, попробуйте снова или свяжитесь с поддержкой.

С уважением,
Команда Harmoni"""

    # Contact Form Email Templates
    contact_form_email_subject: str = "Новая заявка на консультацию - {name}"
    contact_form_email_body: str = """Получена новая заявка на индивидуальную консультацию:

Имя: {name}
Email: {email}
Телефон: {phone}
Telegram: {telegram}

Комментарий:
{comment}"""


settings = Settings()
