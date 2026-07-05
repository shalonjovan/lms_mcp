"""Application configuration loaded from environment."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# LMS
LMS_URL = os.getenv("LMS_URL", "https://lms.ssn.edu.in")
LMS_USERNAME = os.getenv("LMS_USERNAME", "")
LMS_PASSWORD = os.getenv("LMS_PASSWORD", "")

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

# Ensure directories exist
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
