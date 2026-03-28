import sys
import pytest


def reload_config(monkeypatch, **env):
    for key in [
        "DEFAULT_PROVIDERS",
        "GEMINI_API_KEY",
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_CLOUD_LOCATION",
        "LEGACY_GEMINI_API_URL",
        "ENABLE_LEGACY_PROXY",
        "LEGACY_GEMINI_AUTH_TOKEN",
        "API_URL",
    ]:
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    # Force reload of the config module
    if "src.core.config" in sys.modules:
        del sys.modules["src.core.config"]

    import src.core.config

    return src.core.config


def reload_provider(monkeypatch, **env):
    reload_config(monkeypatch, **env)
    if "src.core.gemini_provider" in sys.modules:
        del sys.modules["src.core.gemini_provider"]
    import src.core.gemini_provider

    return src.core.gemini_provider


def test_default_providers_prefer_aistudio_then_vertex_then_legacy(monkeypatch):
    config = reload_config(monkeypatch)
    assert config.DEFAULT_PROVIDERS == ["aistudio", "vertex", "legacy-proxy"]


@pytest.mark.asyncio
async def test_build_provider_target_for_aistudio(monkeypatch):
    provider_mod = reload_provider(monkeypatch, GEMINI_API_KEY="test-key")
    target = await provider_mod.build_provider_target(
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


@pytest.mark.asyncio
async def test_build_provider_target_for_vertex(monkeypatch):
    provider_mod = reload_provider(
        monkeypatch,
        GOOGLE_CLOUD_PROJECT="demo-project",
        GOOGLE_CLOUD_LOCATION="us-central1",
    )

    async def mock_get_token():
        return "vertex-token"

    monkeypatch.setattr(
        "src.core.gemini_provider.get_vertex_bearer_token",
        mock_get_token,
    )
    target = await provider_mod.build_provider_target(
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


@pytest.mark.asyncio
async def test_legacy_proxy_requires_base_url(monkeypatch):
    # Overriding the config module directly because reload_provider/config might still see defaults
    provider_mod = reload_provider(monkeypatch, ENABLE_LEGACY_PROXY="true")
    provider_mod.config.LEGACY_GEMINI_API_URL = ""
    with pytest.raises(ValueError, match="api_base_url or LEGACY_GEMINI_API_URL"):
        await provider_mod.build_provider_target(
            provider="legacy-proxy",
            model="gemini-3-flash",
            action="generateContent",
            stream=False,
        )


@pytest.mark.asyncio
async def test_legacy_proxy_can_be_used_when_explicitly_enabled(monkeypatch):
    provider_mod = reload_provider(
        monkeypatch,
        ENABLE_LEGACY_PROXY="true",
        LEGACY_GEMINI_API_URL="http://localhost:7861/antigravity",
        LEGACY_GEMINI_AUTH_TOKEN="pwd",
    )
    target = await provider_mod.build_provider_target(
        provider="legacy-proxy",
        model="gemini-3-flash",
        action="generateContent",
        stream=False,
    )
    assert (
        target.url
        == "http://localhost:7861/antigravity/v1/models/gemini-3-flash:generateContent"
    )
    assert target.headers["Authorization"] == "Bearer pwd"


@pytest.mark.asyncio
async def test_legacy_proxy_is_rejected_unless_explicitly_enabled(monkeypatch):
    provider_mod = reload_provider(monkeypatch, ENABLE_LEGACY_PROXY="false")
    with pytest.raises(ValueError, match="legacy-proxy provider is disabled"):
        await provider_mod.build_provider_target(
            provider="legacy-proxy",
            model="gemini-3-flash",
            action="generateContent",
            stream=False,
        )


@pytest.mark.asyncio
async def test_build_provider_target_for_aistudio_streaming(monkeypatch):
    provider_mod = reload_provider(monkeypatch, GEMINI_API_KEY="test-key")
    target = await provider_mod.build_provider_target(
        provider="aistudio",
        model="gemini-3-flash",
        action="generateContent",
        stream=True,
    )
    assert target.url == (
        "https://generativelanguage.googleapis.com/v1/"
        "models/gemini-3-flash:generateContent?alt=sse"
    )


@pytest.mark.asyncio
async def test_build_provider_target_for_legacy_proxy_full(monkeypatch):
    provider_mod = reload_provider(
        monkeypatch,
        ENABLE_LEGACY_PROXY="true",
        LEGACY_GEMINI_API_URL="https://proxy.example.com",
        LEGACY_GEMINI_AUTH_TOKEN="proxy-token",
    )
    target = await provider_mod.build_provider_target(
        provider="legacy-proxy",
        model="gemini-3-flash",
        action="generateContent",
        stream=False,
    )
    assert target.url == (
        "https://proxy.example.com/v1/models/gemini-3-flash:generateContent"
    )
    assert target.headers["Authorization"] == "Bearer proxy-token"


@pytest.mark.asyncio
async def test_build_provider_target_for_aistudio_missing_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    provider_mod = reload_provider(monkeypatch)
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        await provider_mod.build_provider_target(
            provider="aistudio",
            model="gemini-3-flash",
            action="generateContent",
            stream=False,
        )
