from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram Bot
    BOT_TOKEN: str = Field(default="dummy_token")

    # PostgreSQL Database
    DB_HOST: str = Field(default="localhost")
    DB_PORT: int = Field(default=5433)
    DB_USER: str = Field(default="adad_user")
    DB_PASSWORD: str = Field(default="adad_secure_password")
    DB_NAME: str = Field(default="adad_db")

    # LLM Settings
    LLM_API_KEY: str = Field(default="")
    LLM_MODEL: str = Field(default="gpt-4o-mini")
    LLM_BASE_URL: str | None = Field(default=None)

    # Schedule Configuration
    EVENING_CRON_HOUR: int = Field(default=19)
    EVENING_CRON_MINUTE: int = Field(default=0)
    MORNING_CRON_HOUR: int = Field(default=9)
    MORNING_CRON_MINUTE: int = Field(default=0)
    TIMEZONE: str = Field(default="Asia/Tashkent")

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
