from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    GEMINI_API_KEY: str = ""
    DATABASE_URL: str = ""
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # --- Auth (Phase: multi-tenancy) ---
    # HMAC signing secret for access tokens. MUST be set to a long random string
    # in production (e.g. `python -c "import secrets; print(secrets.token_urlsafe(48))"`).
    # The default is intentionally unusable in prod and only keeps local/import working.
    AUTH_SECRET: str = "dev-insecure-change-me"
    # Access-token lifetime in hours (default 7 days).
    ACCESS_TOKEN_TTL_HOURS: int = 168

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

    # --- Voice Crisis Mode (Phase 8) ---
    # LiveKit (Cloud or self-hosted) is the WebRTC transport between the browser
    # and the voice agent worker. Leave any of these empty to disable voice:
    # the /voice/token endpoint then returns 503 instead of minting a token, and
    # the rest of the app is unaffected.
    LIVEKIT_URL: str = ""          # e.g. wss://<your-project>.livekit.cloud
    LIVEKIT_API_KEY: str = ""
    LIVEKIT_API_SECRET: str = ""

    # The Gemini Live (native-audio) model the voice agent speaks through, and
    # the prebuilt voice it uses. "Charon" is a calm, low register that suits a
    # crisis chief-of-staff. Both are overridable via env.
    GEMINI_LIVE_MODEL: str = "gemini-live-2.5-flash-native-audio"
    GEMINI_LIVE_VOICE: str = "Charon"

    # Default LiveKit room the browser and the agent meet in. This is a
    # single-user app, so one stable room is fine; the token endpoint can still
    # override it per request.
    VOICE_ROOM_NAME: str = "clutch-war-room"

    @property
    def voice_enabled(self) -> bool:
        """True only when LiveKit transport is fully configured."""
        return bool(self.LIVEKIT_URL and self.LIVEKIT_API_KEY and self.LIVEKIT_API_SECRET)

settings = Settings()
