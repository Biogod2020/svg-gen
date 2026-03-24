import pytest
from httpx import ASGITransport, AsyncClient
from main import app
import json

@pytest.mark.asyncio
async def test_generate_stream_endpoint():
    """
    Test that the /generate-stream endpoint returns a stream of events.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "prompt": "A simple red circle",
            "style_hints": "minimalist"
        }
        
        # We use a long timeout because SVG generation and VLM audit can be slow
        async with ac.stream("POST", "/generate-stream", json=payload, timeout=60.0) as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            
            chunks = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[len("data: "):]
                    if data_str == "[DONE]":
                        chunks.append("[DONE]")
                        break
                    try:
                        data = json.loads(data_str)
                        chunks.append(data)
                    except json.JSONDecodeError:
                        pytest.fail(f"Failed to decode JSON: {data_str}")
            
            # We expect at least one iteration and a [DONE] message
            assert len(chunks) >= 2
            assert chunks[-1] == "[DONE]"
            
            # Verify the structure of the first iteration
            first_iteration = chunks[0]
            assert "iteration" in first_iteration
            assert "svg_code" in first_iteration
            assert "vqa_results" in first_iteration
            assert "png_b64" in first_iteration
