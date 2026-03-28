import uuid
import sys
from pathlib import Path

import mcp.types as types
from mcp.server import Server

from src.agents.svg_generation.agent import SVGAgent
from src.core.path_utils import get_project_root
from src.core.types import AgentState, AssetVQAStatus
from src.core.gemini_client import GeminiClient


def _log(message: str) -> None:
    sys.stderr.write(f"[MCP] {message}\n")
    sys.stderr.flush()


def register_tools(server: Server):
    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="generate_svg",
                description="Generate a high-quality SVG based on a prompt using the SVG Optimization Lab.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The description of the SVG to generate.",
                        },
                        "style_hints": {
                            "type": "string",
                            "description": "Optional style hints (e.g., 'flat design, vibrant colors').",
                        },
                    },
                    "required": ["prompt"],
                },
            )
        ]

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if name != "generate_svg":
            raise ValueError(f"Unknown tool: {name}")

        if not arguments or "prompt" not in arguments:
            raise ValueError("Missing required argument: prompt")

        client = GeminiClient()
        prompt = arguments["prompt"]
        style_hints = arguments.get("style_hints", "")

        job_id = f"mcp_{uuid.uuid4().hex[:8]}"
        root_dir = get_project_root(Path(__file__).resolve())
        workspace_path = root_dir / "workspace" / job_id
        workspace_path.mkdir(parents=True, exist_ok=True)

        state = AgentState(job_id=job_id, workspace_path=str(workspace_path))
        agent = SVGAgent(client=client)

        try:
            _log(f"Received generation request: {prompt[:50]}...")
            async for _ in agent.run_optimization_loop(
                asset_id=f"svg_{job_id}",
                description=prompt,
                state=state,
                style_hints=style_hints,
            ):
                pass

            uar = state.get_uar()
            asset = uar.assets.get(f"svg_{job_id}")

            if not asset:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: SVG Generation or Optimization failed.",
                    )
                ]

            svg_path = Path(state.workspace_path) / asset.local_path
            if not svg_path.exists():
                return [
                    types.TextContent(
                        type="text", text="Error: Generated SVG file not found on disk."
                    )
                ]

            svg_code = svg_path.read_text(encoding="utf-8")

            if asset.vqa_status == AssetVQAStatus.PASS:
                status_header = "SVG Generation Successful"
            elif asset.vqa_status == AssetVQAStatus.FAIL:
                status_header = "SVG Generation Failed Audit"
            else:
                status_header = f"SVG Generation {asset.vqa_status.title()}"

            audit_details = ""
            if asset.latest_audit:
                audit = asset.latest_audit
                audit_details = f"\nScore: {audit.score}/100\nSummary: {audit.summary}"
                if audit.issues:
                    issues_str = "\n".join(
                        [f"- {i.description} ({i.severity})" for i in audit.issues]
                    )
                    audit_details += f"\nIssues Found:\n{issues_str}"

            result_text = f"{status_header}.\nVQA Status: {asset.vqa_status}\nCaption: {asset.caption}{audit_details}\n\n```xml\n{svg_code}\n```"
            return [types.TextContent(type="text", text=result_text)]

        except Exception as e:
            _log(f"Error: {e}")
            return [
                types.TextContent(
                    type="text", text=f"Error during generation: {str(e)}"
                )
            ]
