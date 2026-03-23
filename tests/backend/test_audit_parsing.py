import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pathlib import Path
from src.agents.asset_management.processors.audit import sanitize_svg, extract_json_payload, audit_svg_visual_async

def test_sanitize_svg():
    # Markdown code blocks
    malformed_markdown = "Here is an SVG: ```svg\n<svg>Content</svg>\n```"
    assert sanitize_svg(malformed_markdown) == "<svg>Content</svg>"
    
    # Extra text before and after
    extra_text = "Before <svg>Main Content</svg> After"
    assert sanitize_svg(extra_text) == "<svg>Main Content</svg>"
    
    # Missing closing tag
    missing_close = "<svg>Incomplete content"
    assert sanitize_svg(missing_close) == "<svg>Incomplete content\n</svg>"
    
    # Case insensitive
    case_insensitive = "<SVG>UPPER CASE</SVG>"
    assert sanitize_svg(case_insensitive) == "<SVG>UPPER CASE</SVG>"

def test_extract_json_payload():
    # Clean JSON
    clean_json = '{"key": "value"}'
    assert extract_json_payload(clean_json) == clean_json
    
    # JSON surrounded by text
    surrounded_json = 'Text before {"key": "value"} and text after'
    assert extract_json_payload(surrounded_json) == '{"key": "value"}'
    
    # Multi-line JSON
    multi_line_json = """
    Here is the result:
    {
        "score": 85,
        "issues": [
            {"description": "Too small", "box": [10, 10, 50, 50]}
        ]
    }
    Hope this helps.
    """
    extracted = extract_json_payload(multi_line_json)
    assert json.loads(extracted)["score"] == 85
    
    # No JSON
    no_json = "Just some text with no braces"
    assert extract_json_payload(no_json) is None

@pytest.mark.asyncio
async def test_audit_svg_visual_async_parsing_success():
    # Mock GeminiClient
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.text = """
    ```json
    {
      "thought": "The SVG looks good but has one overlap.",
      "accuracy_score": 18,
      "typography_score": 10,
      "engineering_score": 5,
      "intent_score": 55,
      "overall_score": 88,
      "result": "pass",
      "issues": [
        {
          "description": "Text overlap at bottom",
          "box": [800, 100, 900, 400],
          "severity": "medium"
        }
      ],
      "suggestions": ["Increase bottom margin"]
    }
    ```
    """
    mock_response.thoughts = "Analyzing visual layout..."
    mock_client.generate_async.return_value = mock_response
    
    # Mock State
    mock_state = MagicMock()
    mock_state.thoughts = ""
    
    svg_code = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='90'>Overlap</text></svg>"
    intent = "A simple SVG with text"
    
    import src.agents.asset_management.processors.audit as audit_module
    
    with patch("src.agents.asset_management.processors.audit.render_svg_with_playwright", AsyncMock(return_value=True)):
        with patch("builtins.open", mock_open(read_data=b"fake_png_data")):
             result = await audit_svg_visual_async(
                client=mock_client,
                svg_code=svg_code,
                intent_description=intent,
                state=mock_state
            )
            
    assert result is not None
    assert result["overall_score"] == 88
    assert len(result["issues"]) == 1
    assert result["issues"][0]["box"] == [800, 100, 900, 400]
    # In audit_svg_visual_async:
    # state.thoughts += f"\n[SVG Visual Audit] {response.thoughts}"
    # and then if data.get("thought"):
    # state.thoughts += f"\n[Audit Deep Dive] {data['thought']}"
    
    # Since mock_state.thoughts is a MagicMock, we need to check how it was called
    # Actually, if I initialize it as an empty string it might not work as expected with += if it's a MagicMock
    # Let's use a real object for state
    
@pytest.mark.asyncio
async def test_audit_svg_visual_async_fallback():
    # Mock GeminiClient
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.text = '{"overall_score": 70, "issues": []}'
    mock_response.thoughts = "Fallback analysis..."
    mock_client.generate_async.return_value = mock_response
    
    class FakeState:
        def __init__(self):
            self.thoughts = ""
    
    state = FakeState()
    svg_code = "<svg>...</svg>"
    intent = "Test fallback"
    
    import src.agents.asset_management.processors.audit as audit_module
    
    with patch("src.agents.asset_management.processors.audit.render_svg_with_playwright", AsyncMock(return_value=False)):
        with patch("src.agents.asset_management.processors.audit.render_svg_to_png_base64", MagicMock(return_value=None)):
            result = await audit_svg_visual_async(
                client=mock_client,
                svg_code=svg_code,
                intent_description=intent,
                state=state
            )
            
    assert result is not None
    assert result["overall_score"] == 70
    assert "[SVG Code Audit] Fallback analysis..." in state.thoughts

@pytest.mark.asyncio
async def test_audit_svg_visual_async_with_state_capture():
    # Mock GeminiClient
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.text = '{"thought": "Deep thought", "overall_score": 90, "issues": []}'
    mock_response.thoughts = "Surface thought"
    mock_client.generate_async.return_value = mock_response
    
    class FakeState:
        def __init__(self):
            self.thoughts = ""
    
    state = FakeState()
    svg_code = "<svg>...</svg>"
    
    with patch("src.agents.asset_management.processors.audit.render_svg_with_playwright", AsyncMock(return_value=True)):
        with patch("builtins.open", mock_open(read_data=b"fake_png_data")):
            await audit_svg_visual_async(
                client=mock_client,
                svg_code=svg_code,
                intent_description="test",
                state=state
            )
            
    assert "[SVG Visual Audit] Surface thought" in state.thoughts
    assert "[Audit Deep Dive] Deep thought" in state.thoughts
