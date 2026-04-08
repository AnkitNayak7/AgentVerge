from __future__ import annotations

import os
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()


def _set_default_google_application_credentials() -> None:
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        return

    repo_root = Path(__file__).resolve().parents[2]
    candidate_paths = [
        repo_root / "key.json",
        repo_root / "agents" / "key.json",
    ]
    for candidate in candidate_paths:
        if candidate.exists():
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(candidate)
            return


_set_default_google_application_credentials()


def _patch_googleapiclient_discovery_when_adc_missing() -> None:
    """googleapiclient.discovery.build() loads ADC for APIs that declare OAuth scopes.

    ADK uses this to fetch Calendar/Tasks discovery into OpenAPI. Docker and some
    local setups have no ADC; Cloud Run provides it via the metadata server.

    On DefaultCredentialsError, retry with GOOGLE_API_KEY as developerKey (if
    set) or unauthenticated discovery via AnonymousCredentials.
    """
    from google.auth.credentials import AnonymousCredentials
    from google.auth.exceptions import DefaultCredentialsError
    from googleapiclient import discovery as discovery_mod

    _orig = discovery_mod.build

    def _build(serviceName, version, *args, **kwargs):
        try:
            return _orig(serviceName, version, *args, **kwargs)
        except DefaultCredentialsError:
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                kwargs = dict(kwargs)
                kwargs["developerKey"] = kwargs.get("developerKey") or api_key
                kwargs.pop("credentials", None)
                return _orig(serviceName, version, *args, **kwargs)
            kwargs = dict(kwargs)
            kwargs["credentials"] = AnonymousCredentials()
            return _orig(serviceName, version, *args, **kwargs)

    discovery_mod.build = _build


_patch_googleapiclient_discovery_when_adc_missing()

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
