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


settings = Settings()
