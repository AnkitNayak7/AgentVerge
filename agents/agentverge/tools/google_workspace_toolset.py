from __future__ import annotations

from typing import List, Optional, Union

from google.adk.auth.auth_credential import AuthCredential
from google.adk.auth.auth_credential import AuthCredentialTypes
from google.adk.auth.auth_credential import OAuth2Auth
from google.adk.auth.auth_schemes import OpenIdConnectWithConfig
from google.adk.auth.auth_tool import AuthConfig
from google.adk.tools.base_toolset import ToolPredicate
from google.adk.tools.google_api_tool import GoogleApiToolset

from ..config import OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET

GOOGLE_WORKSPACE_SHARED_CREDENTIAL_KEY = "agentverge_google_workspace_shared_oauth"
GOOGLE_WORKSPACE_SHARED_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/tasks",
]


def _build_shared_google_auth_scheme() -> OpenIdConnectWithConfig:
    return OpenIdConnectWithConfig(
        authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
        token_endpoint="https://oauth2.googleapis.com/token",
        userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
        revocation_endpoint="https://oauth2.googleapis.com/revoke",
        token_endpoint_auth_methods_supported=[
            "client_secret_post",
            "client_secret_basic",
        ],
        grant_types_supported=["authorization_code"],
        scopes=GOOGLE_WORKSPACE_SHARED_SCOPES,
    )


def _build_shared_google_auth_credential() -> AuthCredential:
    return AuthCredential(
        auth_type=AuthCredentialTypes.OPEN_ID_CONNECT,
        oauth2=OAuth2Auth(
            client_id=OAUTH_CLIENT_ID,
            client_secret=OAUTH_CLIENT_SECRET,
            token_endpoint_auth_method="client_secret_post",
        ),
    )


def _apply_shared_auth(toolset: GoogleApiToolset) -> GoogleApiToolset:
    shared_auth_scheme = _build_shared_google_auth_scheme()
    shared_auth_credential = _build_shared_google_auth_credential()
    openapi_toolset = toolset._openapi_toolset
    openapi_toolset._auth_scheme = shared_auth_scheme
    openapi_toolset._auth_credential = shared_auth_credential
    openapi_toolset._auth_config = AuthConfig(
        auth_scheme=shared_auth_scheme,
        raw_auth_credential=shared_auth_credential,
        credential_key=GOOGLE_WORKSPACE_SHARED_CREDENTIAL_KEY,
    )
    openapi_toolset._configure_auth_all(shared_auth_scheme, shared_auth_credential)
    openapi_toolset._configure_credential_key_all(GOOGLE_WORKSPACE_SHARED_CREDENTIAL_KEY)
    return toolset


def build_google_workspace_toolset(
    api_name: str,
    api_version: str,
    *,
    tool_filter: Optional[Union[ToolPredicate, List[str]]] = None,
    tool_name_prefix: Optional[str] = None,
) -> GoogleApiToolset:
    toolset = GoogleApiToolset(
        api_name=api_name,
        api_version=api_version,
        client_id=OAUTH_CLIENT_ID,
        client_secret=OAUTH_CLIENT_SECRET,
        tool_filter=tool_filter,
        tool_name_prefix=tool_name_prefix,
    )
    return _apply_shared_auth(toolset)
