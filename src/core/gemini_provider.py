import asyncio
import time
from dataclasses import dataclass
from typing import Dict, Union, Optional

import google.auth
import google.auth.transport.requests
from src.core import config


@dataclass
class ProviderTarget:
    """Standardized target for Gemini API requests."""

    provider: str
    url: str
    headers: Dict[str, str]


# Token cache for Vertex AI
_vertex_token_cache: Dict[str, Union[str, float]] = {}


async def get_vertex_bearer_token() -> str:
    """
    Get a bearer token for Vertex AI with simple caching.
    Uses asyncio.to_thread to avoid blocking the event loop during refresh.
    """
    global _vertex_token_cache

    now = time.time()
    if (
        _vertex_token_cache.get("token")
        and _vertex_token_cache.get("expiry", 0) > now + 60
    ):
        return str(_vertex_token_cache["token"])

    def refresh_credentials():
        try:
            credentials, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            request = google.auth.transport.requests.Request()
            credentials.refresh(request)
            return credentials
        except google.auth.exceptions.DefaultCredentialsError as e:
            # SOTA 3.0: Normalize ADC failures into descriptive ValueError for GeminiClient
            raise ValueError(f"Vertex ADC missing: {str(e)}") from e
        except Exception as e:
            raise ValueError(f"Vertex credential refresh failed: {str(e)}") from e

    credentials = await asyncio.to_thread(refresh_credentials)

    expiry_ts = now + 3600
    if credentials.expiry:
        if hasattr(credentials.expiry, "timestamp"):
            expiry_ts = credentials.expiry.timestamp()
        else:
            try:
                expiry_ts = float(credentials.expiry)
            except (ValueError, TypeError):
                pass

    _vertex_token_cache = {"token": credentials.token, "expiry": expiry_ts}
    return str(credentials.token)


async def build_provider_target(
    provider: str,
    model: str,
    action: str,
    stream: bool = False,
    api_base_url_override: Optional[str] = None,
    auth_token_override: Optional[str] = None,
) -> ProviderTarget:
    """
    Build a ProviderTarget for the specified provider, model, and action.
    This function is async to support non-blocking token retrieval for Vertex.
    """
    if provider == "aistudio":
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required for aistudio provider")

        url = f"{config.AISTUDIO_BASE_URL}/{config.DEFAULT_API_VERSION}/models/{model}:{action}"
        if stream:
            url += "?alt=sse"

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": config.GEMINI_API_KEY,
        }
        return ProviderTarget(provider=provider, url=url, headers=headers)

    elif provider == "vertex":
        if not config.GOOGLE_CLOUD_PROJECT:
            raise ValueError("GOOGLE_CLOUD_PROJECT is required for vertex provider")

        location = config.GOOGLE_CLOUD_LOCATION
        project = config.GOOGLE_CLOUD_PROJECT

        # https://{location}-aiplatform.googleapis.com/v1/projects/{project}/locations/{location}/publishers/google/models/{model}:{action}
        url = config.VERTEX_BASE_TEMPLATE.format(
            location=location, project=project, model=model, action=action
        )

        token = await get_vertex_bearer_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        return ProviderTarget(provider=provider, url=url, headers=headers)

    elif provider == "legacy-proxy":
        if not config.ENABLE_LEGACY_PROXY:
            raise ValueError(
                "legacy-proxy provider is disabled. Set ENABLE_LEGACY_PROXY=true to use it."
            )

        base_url = api_base_url_override or config.LEGACY_GEMINI_API_URL
        if not base_url:
            raise ValueError(
                "api_base_url or LEGACY_GEMINI_API_URL is required for legacy-proxy provider"
            )

        url = f"{base_url.rstrip('/')}/{config.DEFAULT_API_VERSION}/models/{model}:{action}"
        if stream:
            url += "?alt=sse"

        headers = {
            "Content-Type": "application/json",
        }
        auth_token = auth_token_override or config.LEGACY_GEMINI_AUTH_TOKEN
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        return ProviderTarget(provider=provider, url=url, headers=headers)

    else:
        raise ValueError(f"Unsupported provider: {provider}")
