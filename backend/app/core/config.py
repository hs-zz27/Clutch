from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    GEMINI_API_KEY: str = ""
    DATABASE_URL: str = ""
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # Echo SQL to logs. Keep False outside local debugging - it is noisy and can
    # leak row/parameter values into application logs.
    SQL_ECHO: bool = False

    # Optional Gmail SMTP sending for renegotiation messages. When unset, drafts
    # are generated and stored but must be sent manually (graceful degradation).
    # Use a Gmail App Password, NOT your account password.
    GMAIL_SENDER: str = ""
    GMAIL_APP_PASSWORD: str = ""

    # Capacity model. Available focus time is computed inside this daily window
    # (local to TIMEZONE), capped at MAX_FOCUS_HOURS_PER_DAY, minus busy blocks.
    TIMEZONE: str = "Asia/Calcutta"
    WORK_DAY_START_HOUR: int = 9   # 0-23, local time
    WORK_DAY_END_HOUR: int = 23    # 0-23, local time, must be > start
    MAX_FOCUS_HOURS_PER_DAY: float = 10.0

    # Optional read-only calendar feed (.ics). Used to import busy blocks without
    # any OAuth. Leave empty to disable ICS sync.
    CALENDAR_ICS_URL: str = ""


settings = Settings()
