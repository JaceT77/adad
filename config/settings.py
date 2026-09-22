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

    # Database Configuration (Defaults to clean SQLite file)
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///adad.db")

    # LLM Settings
    LLM_API_KEY: str = Field(default="")
    LLM_MODEL: str = Field(default="gemini-3.6-flash")
    LLM_BASE_URL: str | None = Field(default=None)

    # Schedule Configuration
    EVENING_CRON_HOUR: int = Field(default=19)
    EVENING_CRON_MINUTE: int = Field(default=0)
    MORNING_CRON_HOUR: int = Field(default=9)
    MORNING_CRON_MINUTE: int = Field(default=0)
    TIMEZONE: str = Field(default="Asia/Tashkent")

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL


settings = Settings()
