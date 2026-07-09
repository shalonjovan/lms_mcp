"""Application configuration loaded from environment."""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Fix: re-read password from .env directly to handle $ escaping that dotenv mangles
def _fix_password():
    try:
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line.startswith("LMS_PASSWORD=") and not line.startswith("#"):
                    raw_val = line.split("=", 1)[1]
                    if len(raw_val) >= 2 and raw_val[0] == raw_val[-1] and raw_val[0] in ('"', "'"):
                        raw_val = raw_val[1:-1]
                    raw_val = raw_val.replace("$$", "$").replace("\\$", "$")
                    current = os.environ.get("LMS_PASSWORD", "")
                    if "$" in raw_val and "$" not in current:
                        os.environ["LMS_PASSWORD"] = raw_val
                    return raw_val
    except FileNotFoundError:
        pass
    return os.environ.get("LMS_PASSWORD", "")


def setup_logging():
    """Configure centralized logging."""
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        stream=sys.stderr,
    )


def validate_config():
    """Check required configuration and warn about missing values."""
    missing = []
    if not LMS_USERNAME:
        missing.append("LMS_USERNAME")
    if not LMS_PASSWORD:
        missing.append("LMS_PASSWORD")
    if AI_PROVIDER == "google" and not GOOGLE_API_KEY:
        missing.append("GOOGLE_API_KEY (current AI_PROVIDER)")
    elif AI_PROVIDER == "anthropic" and not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY (current AI_PROVIDER)")
    elif AI_PROVIDER == "openai" and not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY (current AI_PROVIDER)")
    if AI_PROVIDER not in ("google", "anthropic", "openai"):
        logger = logging.getLogger(__name__)
        logger.warning("Unknown AI_PROVIDER '%s', defaulting to 'google'", AI_PROVIDER)

    if missing:
        logger = logging.getLogger(__name__)
        logger.warning("Missing recommended config: %s", ", ".join(missing))


BASE_DIR = Path(__file__).resolve().parent.parent

# LMS
LMS_URL = os.getenv("LMS_URL", "https://lms.ssn.edu.in")
LMS_USERNAME = os.getenv("LMS_USERNAME", "")
LMS_PASSWORD = _fix_password()

# AI Provider
AI_PROVIDER = os.getenv("AI_PROVIDER", "google")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Student Info
STUDENT_NAME = os.getenv("STUDENT_NAME", "")
STUDENT_REG_NO = os.getenv("STUDENT_REG_NO", "")
STUDENT_DEPT = os.getenv("STUDENT_DEPT", "")
STUDENT_YEAR = os.getenv("STUDENT_YEAR", "")

# App
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "127.0.0.1")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8080"))
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "lms_mcp.db")))
GENERATED_DIR = Path(os.getenv("GENERATED_DIR", str(BASE_DIR / "generated")))
POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "30"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Ensure directories exist
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
