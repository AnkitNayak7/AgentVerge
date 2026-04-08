from __future__ import annotations

import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.getenv("AGENTVERGE_MODEL", "gemini-2.5-flash")
APP_NAME = "agentverge"
ROOT_AGENT_NAME = "AgentVerge"
APP_TZ = os.getenv("APP_TIMEZONE", "Asia/Kolkata")
LOCAL_TZ = ZoneInfo(APP_TZ)

OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")

if not OAUTH_CLIENT_ID or not OAUTH_CLIENT_SECRET:
    raise ValueError(
        "Missing OAUTH_CLIENT_ID / OAUTH_CLIENT_SECRET. "
        "Set them in local .env or inject them as environment variables/secrets in Cloud Run."
    )
