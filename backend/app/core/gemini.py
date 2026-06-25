import logging

from google import genai

from app.core.config import settings

logger = logging.getLogger("clutch")

if not settings.GEMINI_API_KEY:
    logger.warning(
        "GEMINI_API_KEY is not set; the Gemini client is initialised with a "
        "placeholder key. AI calls will fail until a real key is configured."
    )

# Construct with a placeholder when unset so the app stays importable (CI smoke
# tests, `import app.main`). Real AI calls require a valid key.
client = genai.Client(api_key=settings.GEMINI_API_KEY or "missing-api-key")
