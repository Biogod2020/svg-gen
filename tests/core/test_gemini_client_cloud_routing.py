import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from src.core.gemini_client import GeminiClient


@pytest.mark.asyncio
async def test_generate_async_uses_aistudio_headers(monkeypatch):
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
        AsyncMock(
            return_value=MagicMock(
                provider="aistudio",
                url="https://generativelanguage.googleapis.com/v1/models/gemini-3-flash:generateContent",
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": "test-key",
                },
            )
        ),
    )

    response = await client.generate_async(prompt="hello")

    assert response.text == "ok"
    fake_http.post.assert_awaited_once()
    assert fake_http.post.await_args.kwargs["headers"]["x-goog-api-key"] == "test-key"


@pytest.mark.asyncio
async def test_generate_async_falls_back_to_vertex_after_transient_error(monkeypatch):
    client = GeminiClient(
        model_provider=["aistudio", "vertex"], prefer_first_provider=True
    )
    client.MAX_LOCAL_RETRIES = 0  # Force immediate fallback for this test
    fake_http = MagicMock()
    first = MagicMock(status_code=503, text="backend unavailable")
    second = MagicMock(status_code=200)
    second.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "vertex ok"}]}}]
    }
    fake_http.post = AsyncMock(side_effect=[first, second])

    monkeypatch.setattr(client, "_get_client", AsyncMock(return_value=fake_http))
    monkeypatch.setattr(client, "reset_client", AsyncMock())
    monkeypatch.setattr("src.core.gemini_client.asyncio.sleep", AsyncMock())

    async def fake_target(provider, model, action, stream, **kwargs):
        if provider == "aistudio":
            return MagicMock(
                provider=provider,
                url="https://aistudio",
                headers={"x-goog-api-key": "k", "Content-Type": "application/json"},
            )
        return MagicMock(
            provider=provider,
            url="https://vertex",
            headers={"Authorization": "Bearer t", "Content-Type": "application/json"},
        )

    monkeypatch.setattr("src.core.gemini_client.build_provider_target", fake_target)

    response = await client.generate_async(prompt="hello")

    assert response.text == "vertex ok"
    assert fake_http.post.await_count == 2

    # Assert call order and targets
    calls = fake_http.post.await_args_list
    assert calls[0].args[0] == "https://aistudio"
    assert calls[1].args[0] == "https://vertex"


@pytest.mark.asyncio
async def test_generate_async_honors_instance_overrides_for_legacy_proxy(monkeypatch):
    # Test that api_base_url and auth_token overrides on the instance are passed to build_provider_target
    client = GeminiClient(
        api_base_url="http://custom-proxy:8888",
        auth_token="custom-token",
        model_provider="legacy-proxy",
    )
    fake_http = MagicMock()
    fake_response = MagicMock(status_code=200)
    fake_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "ok"}]}}]
    }
    fake_http.post = AsyncMock(return_value=fake_response)

    monkeypatch.setattr(client, "_get_client", AsyncMock(return_value=fake_http))
    monkeypatch.setattr("src.core.gemini_client.asyncio.sleep", AsyncMock())

    # Mock build_provider_target to verify arguments
    mock_build = AsyncMock(
        return_value=MagicMock(
            provider="legacy-proxy",
            url="http://custom-proxy:8888/v1/models/m:generateContent",
            headers={},
        )
    )
    monkeypatch.setattr("src.core.gemini_client.build_provider_target", mock_build)

    await client.generate_async(prompt="hello")

    mock_build.assert_awaited_once()
    kwargs = mock_build.await_args.kwargs
    assert kwargs["api_base_url_override"] == "http://custom-proxy:8888"
    assert kwargs["auth_token_override"] == "custom-token"


@pytest.mark.asyncio
async def test_generate_async_does_not_retry_local_on_permanent_errors(monkeypatch):
    client = GeminiClient(
        model_provider=["aistudio", "vertex"], prefer_first_provider=True
    )
    fake_http = MagicMock()
    # 400 Bad Request is a permanent error
    bad_request = MagicMock(status_code=400, text="Invalid prompt", headers={})
    fake_http.post = AsyncMock(return_value=bad_request)

    monkeypatch.setattr(client, "_get_client", AsyncMock(return_value=fake_http))
    monkeypatch.setattr("src.core.gemini_client.asyncio.sleep", AsyncMock())

    async def fake_target(provider, model, action, stream, **kwargs):
        return MagicMock(provider=provider, url=f"https://{provider}", headers={})

    monkeypatch.setattr("src.core.gemini_client.build_provider_target", fake_target)

    response = await client.generate_async(prompt="hello")

    assert response.success is False
    assert "HTTP 400" in response.error
    # Should only have 1 call because 400 is permanent and it shouldn't switch provider either for 400 by default (it just fails)
    assert fake_http.post.await_count == 1


@pytest.mark.asyncio
async def test_generate_async_uses_robust_json_parsing(monkeypatch):
    client = GeminiClient(model_provider=["aistudio"])
    fake_http = MagicMock()
    # Return a response with messy JSON
    fake_response = MagicMock(status_code=200)
    fake_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": 'Here is the data: ```json\n{ "key": "value", } \n```'}
                    ]
                }
            }
        ]
    }
    fake_http.post = AsyncMock(return_value=fake_response)

    monkeypatch.setattr(client, "_get_client", AsyncMock(return_value=fake_http))
    monkeypatch.setattr("src.core.gemini_client.asyncio.sleep", AsyncMock())

    async def fake_target(provider, model, action, stream, **kwargs):
        return MagicMock(provider=provider, url=f"https://{provider}", headers={})

    monkeypatch.setattr("src.core.gemini_client.build_provider_target", fake_target)

    response = await client.generate_async(prompt="hello")

    assert response.success is True
    # parse_json_dict_robust should handle the trailing comma and code fences
    assert response.json_data == {"key": "value"}


@pytest.mark.asyncio
async def test_generate_async_parsing_handles_empty_text(monkeypatch):
    client = GeminiClient(model_provider=["aistudio"])
    fake_http = MagicMock()
    fake_response = MagicMock(status_code=200)
    # Empty content parts
    fake_response.json.return_value = {"candidates": [{"content": {"parts": []}}]}
    fake_http.post = AsyncMock(return_value=fake_response)

    monkeypatch.setattr(client, "_get_client", AsyncMock(return_value=fake_http))
    monkeypatch.setattr("src.core.gemini_client.asyncio.sleep", AsyncMock())

    async def fake_target(*args, **kwargs):
        return MagicMock(provider="aistudio", url="https://aistudio", headers={})

    monkeypatch.setattr("src.core.gemini_client.build_provider_target", fake_target)

    response = await client.generate_async(prompt="hello")

    assert response.success is True
    assert response.text == ""
    assert response.json_data is None


@pytest.mark.asyncio
async def test_generate_async_streaming_populates_json_data(monkeypatch):
    client = GeminiClient(model_provider=["aistudio"])
    fake_http = MagicMock()

    # Mock stream response
    def mock_stream(*args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        async def aiter_lines():
            # Send JSON in chunks
            yield 'data: {"candidates": [{"content": {"parts": [{"text": "```json\\n"}]}}]}'
            yield 'data: {"candidates": [{"content": {"parts": [{"text": "{\\"streamed\\": \\"ok\\"}"}]}}]}'
            yield 'data: {"candidates": [{"content": {"parts": [{"text": "\\n```"}]}}]}'
            yield "data: [DONE]"

        mock_resp.aiter_lines = aiter_lines
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=None)
        return mock_resp

    fake_http.stream = mock_stream

    monkeypatch.setattr(client, "_get_client", AsyncMock(return_value=fake_http))
    monkeypatch.setattr("src.core.gemini_client.asyncio.sleep", AsyncMock())

    async def fake_target(*args, **kwargs):
        return MagicMock(provider="aistudio", url="https://aistudio", headers={})

    monkeypatch.setattr("src.core.gemini_client.build_provider_target", fake_target)

    response = await client.generate_async(prompt="hello", stream=True)

    assert response.success is True
    assert response.json_data == {"streamed": "ok"}


@pytest.mark.asyncio
async def test_generate_async_honors_per_request_model_provider_override(monkeypatch):
    client = GeminiClient(model_provider=["aistudio"], prefer_first_provider=True)
    fake_http = MagicMock()

    fake_response = MagicMock(status_code=200)
    fake_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "vertex response"}]}}]
    }
    fake_http.post = AsyncMock(return_value=fake_response)

    monkeypatch.setattr(client, "_get_client", AsyncMock(return_value=fake_http))
    monkeypatch.setattr("src.core.gemini_client.asyncio.sleep", AsyncMock())

    async def fake_target(provider, model, action, stream, **kwargs):
        return MagicMock(provider=provider, url=f"https://{provider}", headers={})

    monkeypatch.setattr("src.core.gemini_client.build_provider_target", fake_target)

    # Override with string
    await client.generate_async(prompt="hello", model_provider="vertex")
    assert fake_http.post.await_args.args[0] == "https://vertex"
    assert client.model_providers == ["aistudio"]  # Original preserved

    # Override with list
    fake_http.post.reset_mock()
    await client.generate_async(
        prompt="hello", model_provider=["legacy-proxy", "vertex"]
    )
    assert fake_http.post.await_args.args[0] == "https://legacy-proxy"
    assert client.model_providers == ["aistudio"]  # Original preserved
