import sys
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from starlette.responses import Response

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import mcp_sse
import mcp_stdio


@pytest.mark.asyncio
async def test_mcp_stdio_redirects_stdout_during_server_run(monkeypatch):
    original_stdout = sys.stdout
    calls = []

    class FakeServer:
        def create_initialization_options(self):
            return "init-options"

        async def run(self, read_stream, write_stream, init_options):
            calls.append(
                (read_stream, write_stream, init_options, sys.stdout, sys.stderr)
            )

    @asynccontextmanager
    async def fake_stdio_server():
        yield "read-stream", "write-stream"

    monkeypatch.setattr(mcp_stdio, "Server", lambda name: FakeServer())
    monkeypatch.setattr(mcp_stdio, "register_tools", lambda server: None)
    monkeypatch.setattr(mcp_stdio, "stdio_server", fake_stdio_server)

    await mcp_stdio.main()

    assert calls == [
        ("read-stream", "write-stream", "init-options", sys.stderr, sys.stderr)
    ]
    assert sys.stdout is original_stdout


@pytest.mark.asyncio
async def test_mcp_sse_uses_transport_context_manager(monkeypatch):
    calls = []

    class FakeTransport:
        def __init__(self, endpoint):
            self.endpoint = endpoint

        @asynccontextmanager
        async def connect_sse(self, scope, receive, send):
            calls.append(("connect_sse", scope, receive, send))
            yield "read-stream", "write-stream"

    async def fake_run(read_stream, write_stream, init_options):
        calls.append(("run", read_stream, write_stream, init_options))

    monkeypatch.setattr(mcp_sse, "SseServerTransport", FakeTransport)
    monkeypatch.setattr(mcp_sse, "sse_transport", FakeTransport("/mcp/messages"))
    monkeypatch.setattr(mcp_sse.server, "run", fake_run)
    monkeypatch.setattr(
        mcp_sse.server, "create_initialization_options", lambda: "init-options"
    )

    async def fake_receive():
        return {"type": "http.disconnect"}

    sent_messages = []

    async def fake_send(message):
        sent_messages.append(message)

    request = type(
        "RequestStub",
        (),
        {
            "scope": {"type": "http", "method": "GET", "path": "/mcp/sse"},
            "receive": fake_receive,
            "_send": fake_send,
        },
    )()

    response = await mcp_sse.handle_sse(request)

    assert isinstance(response, Response)
    assert calls == [
        ("connect_sse", request.scope, request.receive, request._send),
        ("run", "read-stream", "write-stream", "init-options"),
    ]


@pytest.mark.asyncio
async def test_mcp_sse_posts_messages_via_asgi_transport(monkeypatch):
    calls = []

    class FakeTransport:
        async def handle_post_message(self, scope, receive, send):
            calls.append((scope, receive, send))

    monkeypatch.setattr(mcp_sse, "sse_transport", FakeTransport())

    async def fake_receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def fake_send(message):
        return None

    request = type(
        "RequestStub",
        (),
        {
            "scope": {"type": "http", "method": "POST", "path": "/mcp/messages"},
            "receive": fake_receive,
            "_send": fake_send,
        },
    )()

    await mcp_sse.handle_messages(request)

    assert calls == [(request.scope, request.receive, request._send)]


@pytest.mark.asyncio
async def test_generate_svg_tool_integration(monkeypatch, tmp_path):
    """
    Test the generate_svg tool logic in mcp_shared.py using mocks for SVGAgent.
    """
    import mcp.types as types
    from mcp.server import Server
    from src.mcp_shared import register_tools
    from src.core.types import AssetEntry, AssetSource, AssetVQAStatus

    # Mock the SVGAgent and its run_optimization_loop
    class FakeAgent:
        def __init__(self, **kwargs):
            pass

        async def run_optimization_loop(
            self, asset_id, description, state, style_hints=""
        ):
            # Simulate asset generation by adding an entry to the registry
            uar = state.get_uar()
            # Create a dummy SVG file
            (Path(state.workspace_path) / "test.svg").write_text("<svg></svg>")

            uar.assets[asset_id] = AssetEntry(
                id=asset_id,
                source=AssetSource.AI,
                local_path="test.svg",
                semantic_label="test",
                caption="Generated SVG",
                vqa_status=AssetVQAStatus.PASS,
            )
            yield {"iteration": 1}

    monkeypatch.setattr("src.mcp_shared.SVGAgent", FakeAgent)
    monkeypatch.setattr("src.mcp_shared.GeminiClient", lambda: None)

    # Use tmp_path as CWD to avoid polluting the workspace
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    # Capture the handler
    captured_handler = None

    class MockServer:
        def __init__(self, name):
            pass

        def list_tools(self):
            def decorator(f):
                return f

            return decorator

        def call_tool(self):
            def decorator(f):
                nonlocal captured_handler
                captured_handler = f
                return f

            return decorator

    server = MockServer("test-server")
    register_tools(server)

    # Directly call the handler
    result = await captured_handler("generate_svg", {"prompt": "a red circle"})

    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)
    assert "SVG Generation Successful" in result[0].text
    assert "<svg></svg>" in result[0].text
    assert f"VQA Status: {AssetVQAStatus.PASS}" in result[0].text


@pytest.mark.asyncio
async def test_generate_svg_tool_includes_audit_details(monkeypatch, tmp_path):
    """
    Test that the generate_svg tool includes score and issues if available.
    """
    import mcp.types as types
    from src.mcp_shared import register_tools
    from src.core.types import (
        AssetEntry,
        AssetSource,
        AssetVQAStatus,
        AuditResult,
        AuditIssue,
    )

    class FakeAgent:
        def __init__(self, **kwargs):
            pass

        async def run_optimization_loop(
            self, asset_id, description, state, style_hints=""
        ):
            uar = state.get_uar()
            (Path(state.workspace_path) / "audit.svg").write_text("<svg>audit</svg>")

            uar.assets[asset_id] = AssetEntry(
                id=asset_id,
                source=AssetSource.AI,
                local_path="audit.svg",
                semantic_label="test",
                caption="Audited SVG",
                vqa_status=AssetVQAStatus.FAIL,
                latest_audit=AuditResult(
                    status=AssetVQAStatus.FAIL,
                    score=45.5,
                    summary="Poor contrast and overlapping text.",
                    issues=[
                        AuditIssue(description="Low contrast", severity="high"),
                        AuditIssue(description="Text overlap", severity="medium"),
                    ],
                ),
            )
            yield {"iteration": 1}

    monkeypatch.setattr("src.mcp_shared.SVGAgent", FakeAgent)
    monkeypatch.setattr("src.mcp_shared.GeminiClient", lambda: None)
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    captured_handler = None

    class MockServer:
        def list_tools(self):
            return lambda f: f

        def call_tool(self):
            def decorator(f):
                nonlocal captured_handler
                captured_handler = f
                return f

            return decorator

    register_tools(MockServer())
    result = await captured_handler("generate_svg", {"prompt": "audit me"})

    text = result[0].text
    assert "SVG Generation Failed Audit" in text
    assert "Score: 45.5/100" in text
    assert "Summary: Poor contrast and overlapping text." in text
    assert "- Low contrast (high)" in text
    assert "- Text overlap (medium)" in text


@pytest.mark.asyncio
async def test_generate_svg_tool_descriptive_header_for_pending(monkeypatch, tmp_path):
    """
    Test that the generate_svg tool uses a descriptive header for PENDING status.
    """
    import mcp.types as types
    from src.mcp_shared import register_tools
    from src.core.types import AssetEntry, AssetSource, AssetVQAStatus

    class FakeAgent:
        def __init__(self, **kwargs):
            pass

        async def run_optimization_loop(
            self, asset_id, description, state, style_hints=""
        ):
            uar = state.get_uar()
            (Path(state.workspace_path) / "pending.svg").write_text(
                "<svg>pending</svg>"
            )

            uar.assets[asset_id] = AssetEntry(
                id=asset_id,
                source=AssetSource.AI,
                local_path="pending.svg",
                semantic_label="test",
                caption="Pending SVG",
                vqa_status=AssetVQAStatus.PENDING,
            )
            yield {"iteration": 1}

    monkeypatch.setattr("src.mcp_shared.SVGAgent", FakeAgent)
    monkeypatch.setattr("src.mcp_shared.GeminiClient", lambda: None)
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    captured_handler = None

    class MockServer:
        def list_tools(self):
            return lambda f: f

        def call_tool(self):
            def decorator(f):
                nonlocal captured_handler
                captured_handler = f
                return f

            return decorator

    register_tools(MockServer())
    result = await captured_handler("generate_svg", {"prompt": "pending"})

    assert "SVG Generation Pending" in result[0].text
    assert f"VQA Status: {AssetVQAStatus.PENDING}" in result[0].text


@pytest.mark.asyncio
async def test_generate_svg_tool_reports_failure_on_vqa_fail(monkeypatch, tmp_path):
    """
    Test that the generate_svg tool reports failure if vqa_status is FAIL.
    """
    import mcp.types as types
    from src.mcp_shared import register_tools
    from src.core.types import AssetEntry, AssetSource, AssetVQAStatus

    # Mock the SVGAgent and its run_optimization_loop
    class FakeAgent:
        def __init__(self, **kwargs):
            pass

        async def run_optimization_loop(
            self, asset_id, description, state, style_hints=""
        ):
            # Simulate asset generation with FAIL status
            uar = state.get_uar()
            (Path(state.workspace_path) / "failed.svg").write_text("<svg>failed</svg>")

            uar.assets[asset_id] = AssetEntry(
                id=asset_id,
                source=AssetSource.AI,
                local_path="failed.svg",
                semantic_label="test",
                caption="Failed SVG audit",
                vqa_status=AssetVQAStatus.FAIL,
            )
            yield {"iteration": 1}

    monkeypatch.setattr("src.mcp_shared.SVGAgent", FakeAgent)
    monkeypatch.setattr("src.mcp_shared.GeminiClient", lambda: None)
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    # Capture the handler
    captured_handler = None

    class MockServer:
        def list_tools(self):
            def decorator(f):
                return f

            return decorator

        def call_tool(self):
            def decorator(f):
                nonlocal captured_handler
                captured_handler = f
                return f

            return decorator

    server = MockServer()
    register_tools(server)

    # Directly call the handler
    result = await captured_handler("generate_svg", {"prompt": "a failed shape"})

    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)
    # The response should NOT claim unqualified success
    assert "SVG Generation Failed Audit" in result[0].text
    assert f"VQA Status: {AssetVQAStatus.FAIL}" in result[0].text
    assert "<svg>failed</svg>" in result[0].text


@pytest.mark.asyncio
async def test_generate_svg_anchors_workspace_to_project_root(monkeypatch, tmp_path):
    import mcp.types as types
    from src.mcp_shared import register_tools
    from src.core.types import AssetEntry, AssetSource, AssetVQAStatus

    external_cwd = tmp_path / "external-cwd"
    expected_project_root = tmp_path / "project-root"
    external_cwd.mkdir()
    expected_project_root.mkdir()

    observed_workspace_path = None
    captured_handler = None

    class FakeAgent:
        def __init__(self, **kwargs):
            pass

        async def run_optimization_loop(
            self, asset_id, description, state, style_hints=""
        ):
            nonlocal observed_workspace_path
            observed_workspace_path = Path(state.workspace_path)
            observed_workspace_path.mkdir(parents=True, exist_ok=True)
            (observed_workspace_path / "test.svg").write_text("<svg></svg>")

            uar = state.get_uar()
            uar.assets[asset_id] = AssetEntry(
                id=asset_id,
                source=AssetSource.AI,
                local_path="test.svg",
                semantic_label="test",
                caption="Generated SVG",
                vqa_status=AssetVQAStatus.PASS,
            )
            yield {"iteration": 1}

    class MockServer:
        def list_tools(self):
            def decorator(f):
                return f

            return decorator

        def call_tool(self):
            def decorator(f):
                nonlocal captured_handler
                captured_handler = f
                return f

            return decorator

    monkeypatch.setattr("src.mcp_shared.SVGAgent", FakeAgent)
    monkeypatch.setattr("src.mcp_shared.GeminiClient", lambda: None)
    monkeypatch.setattr(Path, "cwd", lambda: external_cwd)
    monkeypatch.setattr(
        "src.mcp_shared.get_project_root",
        lambda start_path=None: expected_project_root,
        raising=False,
    )

    register_tools(MockServer())

    result = await captured_handler("generate_svg", {"prompt": "a blue square"})

    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)
    assert observed_workspace_path is not None
    assert observed_workspace_path.parent == expected_project_root / "workspace"
