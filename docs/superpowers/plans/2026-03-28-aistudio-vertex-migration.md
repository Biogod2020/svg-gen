# AI Studio + Vertex Provider Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current localhost proxy-first Gemini routing with first-class Google AI Studio and Vertex AI providers, while archiving the local port option as an explicit legacy fallback.

**Architecture:** Keep the existing `httpx`-based `GeminiClient` and factor provider routing into a small cloud-provider helper instead of rewriting the whole stack to a new SDK in one shot. Make `aistudio` and `vertex` the only default providers, keep the old proxy path behind an explicit legacy flag, and cover provider resolution with focused unit tests so the rest of the SVG pipeline can keep using `GeminiClient` unchanged.

**Tech Stack:** Python, `httpx`, `google-auth`, FastAPI/MCP callers through `GeminiClient`, `pytest`, `python-dotenv`.

**Pre-requisites:** AI Studio requires `GEMINI_API_KEY`. Vertex AI requires Application Default Credentials plus `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`.

---

## File Structure

- Modify: `requirements.txt`
  - Add the minimum auth dependency needed for Vertex AI bearer-token flow.
- Modify: `src/core/config.py`
  - Replace proxy-centric defaults with cloud-centric env parsing.
  - Parse `DEFAULT_PROVIDERS` from env instead of hardcoding proxy names.
  - Keep a clearly named legacy proxy escape hatch.
- Create: `src/core/gemini_provider.py`
  - One responsibility: convert a provider name plus model/action into a concrete URL and headers.
  - Handle `aistudio`, `vertex`, and optional `legacy-proxy` only.
- Modify: `src/core/gemini_client.py`
  - Reuse existing request / retry / parse logic, but delegate provider-specific URL and header building.
  - Remove `Model-Provider` proxy header assumptions and localhost-specific special cases.
- Create: `tests/core/test_gemini_provider.py`
  - Unit tests for endpoint construction, auth headers, default provider order, and legacy guardrails.
- Create: `tests/core/test_gemini_client_cloud_routing.py`
  - Unit tests for `GeminiClient.generate_async()` routing and retry behavior with mocked HTTP.
- Create: `.env.example`
  - Non-secret example config for AI Studio, Vertex AI, and archived legacy proxy settings.
- Modify: `tests/verify_vertex.py`
  - Replace with a cloud verification script that can target both `aistudio` and `vertex`.
- Modify: `GEMINI.md`
  - Record the provider migration and new env model so future agents stop assuming `localhost:7861`.

---

### Task 1: Replace Proxy-Centric Configuration Defaults

**Files:**
- Modify: `requirements.txt`
- Modify: `src/core/config.py`
- Create: `.env.example`
- Test: `tests/core/test_gemini_provider.py`

- [ ] **Step 1: Write the failing configuration test**

```python
# tests/core/test_gemini_provider.py
import importlib
import sys


def reload_config(monkeypatch, **env):
    for key in [
        "DEFAULT_PROVIDERS",
        "GEMINI_API_KEY",
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_CLOUD_LOCATION",
        "LEGACY_GEMINI_API_URL",
        "ENABLE_LEGACY_PROXY",
    ]:
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    sys.modules.pop("src.core.config", None)
    import src.core.config
    return importlib.reload(src.core.config)


def test_default_providers_prefer_aistudio_then_vertex(monkeypatch):
    config = reload_config(monkeypatch)
    assert config.DEFAULT_PROVIDERS == ["aistudio", "vertex"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_gemini_provider.py::test_default_providers_prefer_aistudio_then_vertex -v`
Expected: FAIL because `src/core/config.py` still returns `['antigravity', 'gemini-cli-oauth', 'vertex']`

- [ ] **Step 3: Write minimal configuration implementation**

```python
# src/core/config.py
import os

AISTUDIO_BASE_URL = "https://generativelanguage.googleapis.com"
VERTEX_BASE_TEMPLATE = (
    "https://{location}-aiplatform.googleapis.com/v1/"
    "projects/{project}/locations/{location}/publishers/google/models/{model}:{action}"
)

DEFAULT_API_VERSION = os.getenv("GEMINI_API_VERSION", "v1")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-3-flash")
DEFAULT_THINKING_LEVEL = "HIGH"

DEFAULT_PROVIDERS = [
    provider.strip()
    for provider in os.getenv("DEFAULT_PROVIDERS", "aistudio,vertex").split(",")
    if provider.strip()
]

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
ENABLE_LEGACY_PROXY = os.getenv("ENABLE_LEGACY_PROXY", "false").lower() == "true"
LEGACY_GEMINI_API_URL = os.getenv("LEGACY_GEMINI_API_URL", os.getenv("API_URL", "")).rstrip("/")
LEGACY_GEMINI_AUTH_TOKEN = os.getenv("LEGACY_GEMINI_AUTH_TOKEN", os.getenv("GEMINI_AUTH_PASSWORD", ""))

WORKSPACE_BASE = os.getenv("WORKSPACE_BASE", "./workspace")
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"
HEADLESS_MODE = os.getenv("HEADLESS_MODE", "true").lower() == "true"
```

```text
# .env.example
DEFAULT_PROVIDERS=aistudio,vertex
DEFAULT_MODEL=gemini-3-flash
GEMINI_API_VERSION=v1

# AI Studio
GEMINI_API_KEY=replace-me

# Vertex AI
GOOGLE_CLOUD_PROJECT=replace-me
GOOGLE_CLOUD_LOCATION=global
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json

# Archived legacy proxy (disabled by default)
ENABLE_LEGACY_PROXY=false
LEGACY_GEMINI_API_URL=http://localhost:7861/antigravity
LEGACY_GEMINI_AUTH_TOKEN=pwd
```

```text
# requirements.txt
google-auth>=2.38.0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/core/test_gemini_provider.py::test_default_providers_prefer_aistudio_then_vertex -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add requirements.txt src/core/config.py .env.example tests/core/test_gemini_provider.py
git commit -m "feat(config): default Gemini providers to AI Studio and Vertex"
```

---

### Task 2: Add a Provider Endpoint Resolver

**Files:**
- Create: `src/core/gemini_provider.py`
- Test: `tests/core/test_gemini_provider.py`

- [ ] **Step 1: Write the failing resolver tests**

```python
# tests/core/test_gemini_provider.py
from types import SimpleNamespace

from src.core.gemini_provider import ProviderTarget, build_provider_target


def test_build_provider_target_for_aistudio(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    target = build_provider_target(
        provider="aistudio",
        model="gemini-3-flash",
        action="generateContent",
        stream=False,
    )
    assert target.url == (
        "https://generativelanguage.googleapis.com/v1/"
        "models/gemini-3-flash:generateContent"
    )
    assert target.headers["x-goog-api-key"] == "test-key"


def test_build_provider_target_for_vertex(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "demo-project")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    monkeypatch.setattr(
        "src.core.gemini_provider.get_vertex_bearer_token",
        lambda: "vertex-token",
    )
    target = build_provider_target(
        provider="vertex",
        model="gemini-3-flash",
        action="generateContent",
        stream=False,
    )
    assert target.url == (
        "https://us-central1-aiplatform.googleapis.com/v1/projects/demo-project/"
        "locations/us-central1/publishers/google/models/gemini-3-flash:generateContent"
    )
    assert target.headers["Authorization"] == "Bearer vertex-token"


def test_legacy_proxy_requires_explicit_opt_in(monkeypatch):
    monkeypatch.delenv("ENABLE_LEGACY_PROXY", raising=False)
    try:
        build_provider_target(
            provider="legacy-proxy",
            model="gemini-3-flash",
            action="generateContent",
            stream=False,
        )
    except ValueError as exc:
        assert "ENABLE_LEGACY_PROXY" in str(exc)
    else:
        raise AssertionError("expected ValueError")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_gemini_provider.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.core.gemini_provider'`

- [ ] **Step 3: Write minimal provider resolver implementation**

```python
# src/core/gemini_provider.py
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import google.auth
from google.auth.transport.requests import Request

from src.core.config import (
    AISTUDIO_BASE_URL,
    DEFAULT_API_VERSION,
    ENABLE_LEGACY_PROXY,
    GEMINI_API_KEY,
    GOOGLE_CLOUD_LOCATION,
    GOOGLE_CLOUD_PROJECT,
    LEGACY_GEMINI_API_URL,
    LEGACY_GEMINI_AUTH_TOKEN,
)


@dataclass(frozen=True)
class ProviderTarget:
    provider: str
    url: str
    headers: dict[str, str]


_VERTEX_TOKEN: str | None = None
_VERTEX_TOKEN_EXPIRY: datetime | None = None


def get_vertex_bearer_token() -> str:
    global _VERTEX_TOKEN, _VERTEX_TOKEN_EXPIRY

    if (
        _VERTEX_TOKEN
        and _VERTEX_TOKEN_EXPIRY
        and datetime.now(timezone.utc) < _VERTEX_TOKEN_EXPIRY - timedelta(minutes=5)
    ):
        return _VERTEX_TOKEN

    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(Request())
    _VERTEX_TOKEN = credentials.token
    _VERTEX_TOKEN_EXPIRY = credentials.expiry
    return _VERTEX_TOKEN


def build_provider_target(provider: str, model: str, action: str, stream: bool) -> ProviderTarget:
    if provider == "aistudio":
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required for provider 'aistudio'")
        url = f"{AISTUDIO_BASE_URL}/{DEFAULT_API_VERSION}/models/{model}:{action}"
        if stream:
            url += "?alt=sse"
        return ProviderTarget(
            provider=provider,
            url=url,
            headers={"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY},
        )

    if provider == "vertex":
        if not GOOGLE_CLOUD_PROJECT:
            raise ValueError("GOOGLE_CLOUD_PROJECT is required for provider 'vertex'")
        token = get_vertex_bearer_token()
        url = (
            f"https://{GOOGLE_CLOUD_LOCATION}-aiplatform.googleapis.com/v1/projects/"
            f"{GOOGLE_CLOUD_PROJECT}/locations/{GOOGLE_CLOUD_LOCATION}/publishers/google/models/"
            f"{model}:{action}"
        )
        # Vertex streaming uses the streamGenerateContent action itself; do not add ?alt=sse.
        return ProviderTarget(
            provider=provider,
            url=url,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        )

    if provider == "legacy-proxy":
        if not ENABLE_LEGACY_PROXY or not LEGACY_GEMINI_API_URL:
            raise ValueError("ENABLE_LEGACY_PROXY=true and LEGACY_GEMINI_API_URL are required for provider 'legacy-proxy'")
        url = f"{LEGACY_GEMINI_API_URL}/{DEFAULT_API_VERSION}/models/{model}:{action}"
        if stream:
            url += "?alt=sse"
        headers = {"Content-Type": "application/json"}
        if LEGACY_GEMINI_AUTH_TOKEN:
            headers["Authorization"] = f"Bearer {LEGACY_GEMINI_AUTH_TOKEN}"
        return ProviderTarget(provider=provider, url=url, headers=headers)

    raise ValueError(f"Unsupported Gemini provider: {provider}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/core/test_gemini_provider.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/gemini_provider.py tests/core/test_gemini_provider.py
git commit -m "feat(core): add Gemini cloud provider resolver"
```

---

### Task 3: Refactor GeminiClient to Use AI Studio + Vertex Routing

**Files:**
- Modify: `src/core/gemini_client.py`
- Test: `tests/core/test_gemini_client_cloud_routing.py`

- [ ] **Step 1: Write the failing GeminiClient routing tests**

```python
# tests/core/test_gemini_client_cloud_routing.py
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.core.gemini_client import GeminiClient, GeminiResponse


@pytest.mark.asyncio
async def test_generate_async_uses_aistudio_headers(monkeypatch):
    # Create the client after monkeypatches so no stale config is captured.
    client = GeminiClient(model_provider=["aistudio"], prefer_first_provider=True)
    fake_http = MagicMock()
    fake_response = MagicMock(status_code=200)
    fake_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "ok"}]}}]
    }
    fake_http.post = AsyncMock(return_value=fake_response)

    monkeypatch.setattr(client, "_get_client", AsyncMock(return_value=fake_http))
    monkeypatch.setattr(
        "src.core.gemini_client.build_provider_target",
        lambda provider, model, action, stream: MagicMock(
            provider="aistudio",
            url="https://generativelanguage.googleapis.com/v1/models/gemini-3-flash:generateContent",
            headers={"Content-Type": "application/json", "x-goog-api-key": "test-key"},
        ),
    )

    response = await client.generate_async(prompt="hello")

    assert response.text == "ok"
    fake_http.post.assert_awaited_once()
    assert fake_http.post.await_args.kwargs["headers"]["x-goog-api-key"] == "test-key"


@pytest.mark.asyncio
async def test_generate_async_falls_back_to_vertex_after_transient_error(monkeypatch):
    # Create the client after monkeypatches so provider order comes from this test only.
    client = GeminiClient(model_provider=["aistudio", "vertex"], prefer_first_provider=True)
    fake_http = MagicMock()
    timeout_exc = Exception("503 backend unavailable")
    ok_response = MagicMock(status_code=200)
    ok_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "vertex ok"}]}}]
    }
    fake_http.post = AsyncMock(side_effect=[timeout_exc, ok_response])

    monkeypatch.setattr(client, "_get_client", AsyncMock(return_value=fake_http))
    monkeypatch.setattr(client, "reset_client", AsyncMock())
    monkeypatch.setattr("src.core.gemini_client.asyncio.sleep", AsyncMock())

    def fake_target(provider, model, action, stream):
        if provider == "aistudio":
            return MagicMock(provider=provider, url="https://aistudio", headers={"x-goog-api-key": "k"})
        return MagicMock(provider=provider, url="https://vertex", headers={"Authorization": "Bearer t"})

    monkeypatch.setattr("src.core.gemini_client.build_provider_target", fake_target)

    response = await client.generate_async(prompt="hello")

    assert response.text == "vertex ok"
    assert fake_http.post.await_count == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_gemini_client_cloud_routing.py -v`
Expected: FAIL because `GeminiClient` still builds URLs and headers inline and still assumes proxy-specific behavior

- [ ] **Step 3: Write minimal client refactor**

```python
# src/core/gemini_client.py
from src.core.gemini_provider import build_provider_target


class GeminiClient:
    def __init__(self, model_provider=None, ...):
        # keep most existing constructor behavior
        if model_provider is None:
            model_provider = DEFAULT_PROVIDERS
        ...

    async def generate_async(...):
        target_model = model or self.model
        action = "streamGenerateContent" if stream else "generateContent"
        ...
        current_provider = self._get_next_provider()
        ...
        target = build_provider_target(
            provider=current_provider,
            model=target_model,
            action=action,
            stream=stream,
        )

        if stream:
            resp = await self._handle_native_stream(
                client,
                target.url,
                payload,
                headers=target.headers,
            )
        else:
            http_resp = await client.post(
                target.url,
                json=payload,
                headers=target.headers,
            )
```

```python
# also in src/core/gemini_client.py
async def _handle_native_stream(self, client, url, payload, headers) -> GeminiResponse:
    async with client.stream(
        "POST",
        url,
        json=payload,
        headers=headers,
        timeout=httpx.Timeout(self.timeout, read=300.0),
    ) as resp:
        ...
```

```python
# remove these proxy-only assumptions from src/core/gemini_client.py
# - DEFAULT_BASE_URL / DEFAULT_AUTH_PASSWORD imports
# - _get_headers()
# - Model-Provider header usage
# - localhost proxy special-casing in _get_client()
# - localhost-only stream parse logging branch
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_gemini_provider.py tests/core/test_gemini_client_cloud_routing.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/gemini_client.py tests/core/test_gemini_client_cloud_routing.py
git commit -m "refactor(core): route Gemini calls through AI Studio and Vertex providers"
```

---

### Task 4: Archive the Local Port Option Without Breaking Emergency Fallback

**Files:**
- Modify: `src/core/gemini_client.py`
- Modify: `tests/verify_vertex.py`
- Test: `tests/core/test_gemini_provider.py`

- [ ] **Step 1: Write the failing legacy fallback test**

```python
# tests/core/test_gemini_provider.py
from src.core.gemini_provider import build_provider_target


def test_legacy_proxy_can_be_used_when_explicitly_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_LEGACY_PROXY", "true")
    monkeypatch.setenv("LEGACY_GEMINI_API_URL", "http://localhost:7861/antigravity")
    monkeypatch.setenv("LEGACY_GEMINI_AUTH_TOKEN", "pwd")
    target = build_provider_target(
        provider="legacy-proxy",
        model="gemini-3-flash",
        action="generateContent",
        stream=False,
    )
    assert target.url == "http://localhost:7861/antigravity/v1/models/gemini-3-flash:generateContent"
    assert target.headers["Authorization"] == "Bearer pwd"
```

- [ ] **Step 2: Run test to verify it fails for the right reason**

Run: `pytest tests/core/test_gemini_provider.py::test_legacy_proxy_can_be_used_when_explicitly_enabled -v`
Expected: FAIL until the env parsing and legacy branch are fully wired through reload-safe config access

- [ ] **Step 3: Implement the archived legacy path and verification script update**

```python
# tests/verify_vertex.py
import asyncio
from dotenv import load_dotenv

load_dotenv()

from src.core.gemini_client import GeminiClient


async def verify(provider: str, prompt: str):
    client = GeminiClient(model_provider=[provider], model="gemini-3-flash")
    resp = await client.generate_async(prompt=prompt)
    return provider, resp


async def main():
    for provider in ["aistudio", "vertex"]:
        name, response = await verify(provider, f"Say '{provider} OK'")
        print(name, response.success, response.text)


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_gemini_provider.py tests/core/test_gemini_client_cloud_routing.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/gemini_client.py tests/core/test_gemini_provider.py tests/verify_vertex.py
git commit -m "chore(core): archive localhost proxy as explicit legacy provider"
```

---

### Task 5: Documentation, Memory, and End-to-End Verification

**Files:**
- Modify: `GEMINI.md`
- Modify: `.env.example`
- Test: `tests/verify_vertex.py`

- [ ] **Step 1: Write the failing documentation check**

Create a short checklist and verify the repo still documents `localhost:7861/antigravity` as the default. The plan is not done until that statement is removed from project memory.

```text
Checklist:
- G E M I N I . m d mentions AI Studio / Vertex as defaults
- .env.example documents both cloud providers
- legacy proxy is marked archived / opt-in
```

- [ ] **Step 2: Run the manual documentation check and confirm it fails**

Run: `grep -n "localhost:7861\|antigravity" GEMINI.md .env.example`
Expected: FAIL the checklist because old proxy wording is still present or cloud defaults are undocumented

- [ ] **Step 3: Write minimal documentation updates**

```markdown
# GEMINI.md
## Provider Routing (2026-03-28)
- Default Gemini providers are now `aistudio` then `vertex`.
- The old localhost proxy is archived behind `ENABLE_LEGACY_PROXY=true`.
- `GeminiClient` still exposes the same public API to the SVG agent stack.
```

```text
# .env.example
# Default cloud route order
DEFAULT_PROVIDERS=aistudio,vertex
```

- [ ] **Step 4: Run full verification**

Run: `pytest tests/core/test_gemini_provider.py tests/core/test_gemini_client_cloud_routing.py tests/backend/test_mcp_servers.py -v`
Expected: PASS

Run: `python3 tests/verify_vertex.py`
Expected: prints success for any cloud provider that has valid credentials configured; if one credential set is absent, the script must fail with a provider-specific configuration error instead of silently falling back to localhost

- [ ] **Step 5: Commit**

```bash
git add GEMINI.md .env.example tests/verify_vertex.py tests/core/test_gemini_provider.py tests/core/test_gemini_client_cloud_routing.py
git commit -m "docs(core): document AI Studio and Vertex provider migration"
```
