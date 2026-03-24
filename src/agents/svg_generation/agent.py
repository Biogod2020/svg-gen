"""
SVGAgent: Optimized SVG Generation Loop
Streamlined for the SVG Optimization Lab.
"""

import asyncio
from pathlib import Path
from typing import Optional, Tuple, Any, List, Dict, AsyncGenerator

from ...core.gemini_client import GeminiClient
from ...core.types import (
    AgentState,
    AssetEntry,
    AssetSource,
    AssetVQAStatus,
    PreflightBlueprint,
    AuditResult,
    AuditIssue
)
from pydantic import BaseModel
from .processor import generate_svg_async, repair_svg_async
from .refinement import RefinementProcessor
from ..asset_management.processors.audit import (
    audit_svg_visual_async, 
    render_svg_to_png_base64,
    refine_caption_async,
    sanitize_svg
)
from ..asset_management.utils import generate_figure_html


class SVGAgent:
    """
    Sub-Agent dedicated to SVG generation.
    Implements a formal Reflection Loop to improve SVG quality based on audit feedback.
    """

    MAX_REPAIR_ATTEMPTS = 5

    def __init__(self, client: Optional[GeminiClient] = None, debug: bool = False):
        self.client = client or GeminiClient()
        self.debug = debug
        self.history: List[Dict[str, Any]] = []

    async def run_optimization_loop(
        self, 
        asset_id: str,
        description: str,
        state: AgentState,
        style_hints: str = ""
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Runs the Generate-Audit-Repair loop for a single SVG asset.
        
        Yields:
            Iteration dictionary objects.
        """
        self.history = []
        ws_path = Path(state.workspace_path)
        out_path = ws_path / "agent_generated"
        out_path.mkdir(parents=True, exist_ok=True)
        
        print(f"    [SVGAgent] 🚀 Starting SVG optimization loop (ID: {asset_id})...")

        # Yield a placeholder to indicate the agent is starting work
        yield {
            "iteration": 0,
            "svg_code": "",
            "vqa_results": {
                "status": "PENDING",
                "score": 0,
                "issues": [],
                "suggestions": [],
                "summary": "Agent is refining the prompt and analyzing requirements...",
                "thought": "Starting refinement step."
            },
            "thoughts": "Starting refinement step.",
            "png_b64": ""
        }

        # 0. Pre-flight Refinement
        print(f"    [SVGAgent] 🔍 Refining prompt and generating dynamic standards...")
        refiner = RefinementProcessor(self.client)
        blueprint = await refiner.refine_request_async(description)
        
        yield {
            "iteration": 0,
            "svg_code": "",
            "vqa_results": {
                "status": "PENDING",
                "score": 0,
                "issues": [],
                "suggestions": [],
                "summary": "Prompt refined. Starting initial SVG generation...",
                "thought": "Refinement complete. Moving to generation."
            },
            "thoughts": "Refinement complete. Moving to generation.",
            "png_b64": ""
        }

        # 1. Initial Generation
        svg_code = await generate_svg_async(
            self.client, 
            description, 
            state=state, 
            style_hints=style_hints,
            blueprint=blueprint
        )
        
        if not svg_code:
            print(f"    [SVGAgent] ❌ Initial generation failed (ID: {asset_id})")
            return

        print(f"    [SVGAgent] ✨ Initial generation successful (len: {len(svg_code)})")
        
        attempt = 0
        is_valid = False
        file_path = out_path / f"{asset_id}.svg"
        
        # 2. Reflection Loop: Audit & Repair
        while attempt < self.MAX_REPAIR_ATTEMPTS:
            attempt += 1
            print(f"    [SVGAgent] 📋 VLM Audit (Attempt {attempt}/{self.MAX_REPAIR_ATTEMPTS})...")
            
            # Persist to disk for auditing
            file_path.write_text(svg_code, encoding="utf-8")
            
            # Cross-modal audit (Code + Visual)
            audit_dict = await audit_svg_visual_async(
                self.client, 
                svg_code, 
                description, 
                state=state, 
                svg_path=file_path,
                blueprint=blueprint
            )

            # Map dict to AuditResult
            if audit_dict:
                status = AssetVQAStatus.PASS if audit_dict.get("result") == "pass" else AssetVQAStatus.FAIL
                audit_obj = AuditResult(
                    status=status,
                    score=float(audit_dict.get("overall_score", 0)),
                    issues=[AuditIssue(**i) for i in audit_dict.get("issues", [])],
                    suggestions=audit_dict.get("suggestions", []),
                    summary=audit_dict.get("quality_assessment", ""),
                    thought=audit_dict.get("thought", "")
                )
            else:
                audit_obj = AuditResult(
                    status=AssetVQAStatus.FAIL,
                    score=0,
                    summary="Audit failed or timed out",
                    thought="No response from VLM"
                )

            # Capture Iteration History
            png_b64 = render_svg_to_png_base64(svg_code)
            iteration = {
                "iteration": attempt,
                "svg_code": sanitize_svg(svg_code),
                "vqa_results": audit_obj,
                "thoughts": audit_obj.thought or state.thoughts,
                "png_b64": png_b64
            }
            self.history.append(iteration)
            yield iteration

            if audit_obj.status == AssetVQAStatus.PASS:
                is_valid = True
                print(f"    [SVGAgent] ✅ Audit PASSED (ID: {asset_id})")
                break
            
            print(f"    [SVGAgent] ⚠️ Audit NOT PASSED: {audit_obj.issues[0].description[:100] if audit_obj.issues else 'No specific issues'}...")
            
            if attempt < self.MAX_REPAIR_ATTEMPTS:
                print(f"    [SVGAgent] 🛠️ Attempting precise repair via Reflection Loop...")
                new_svg = await repair_svg_async(
                    self.client, 
                    description, 
                    svg_code, 
                    [i.description for i in audit_obj.issues], 
                    audit_obj.suggestions, 
                    state=state, 
                    rendered_image_b64=png_b64,
                    blueprint=blueprint
                )
                
                if not new_svg:
                    print(f"    [SVGAgent] ⚠️ Repair Agent failed to return code.")
                else:
                    svg_code = new_svg
                    print(f"    [SVGAgent] 🛠️ Repair complete (new len: {len(svg_code)})")
            else:
                print(f"\n⚠️ [SVGAgent] Exhausted {self.MAX_REPAIR_ATTEMPTS} attempts.")

        # 3. Finalization: Caption Refinement & Atomic Registration
        print(f"    [SVGAgent] ✍️ Refining caption based on visual evidence...")
        png_b64 = render_svg_to_png_base64(svg_code)
        final_caption = await refine_caption_async(self.client, png_b64, description, state=state)
        
        uar = state.get_uar()
        asset = uar.add_asset_atomic(
            asset_id=asset_id,
            content=svg_code.encode("utf-8"),
            source=AssetSource.AI,
            semantic_label=description[:100],
            alt_text=description,
            caption=final_caption,
            vqa_status=AssetVQAStatus.PASS if is_valid else AssetVQAStatus.FAIL
        )
        
        html_code = generate_figure_html(
            asset, final_caption, workspace_path=ws_path
        )
        
        return


class SVGResult(BaseModel):
    asset_id: str
    svg_code: str
    caption: str
    vqa_passed: bool
    local_path: Optional[str] = None
    audit_log: list[str] = []
    history: List[Dict[str, Any]] = []


async def optimize_svg_pipeline(
        asset_id: str,
        description: str,
        workspace_path: str,
        style_hints: str = "",
        client: Optional[GeminiClient] = None
    ) -> SVGResult:
        """
        [Standard Interface] Generates, audits, and repairs an SVG asset.
        Returns a single SVGResult object containing the final code and caption.
        """
        client = client or GeminiClient()
        state = AgentState(job_id=f"job-{asset_id}", workspace_path=workspace_path)
        
        agent = SVGAgent(client=client)
        async for iteration in agent.run_optimization_loop(
            asset_id=asset_id,
            description=description,
            state=state,
            style_hints=style_hints
        ):
            pass
        
        # Read final SVG code from disk (CAS or agent_generated)
        ws_p = Path(workspace_path)
        svg_file = ws_p / "agent_generated" / f"{asset_id}.svg"
        svg_code = svg_file.read_text(encoding="utf-8") if svg_file.exists() else ""
        
        uar = state.get_uar()
        asset = uar.assets.get(asset_id)
        
        return SVGResult(
            asset_id=asset_id,
            svg_code=svg_code,
            caption=asset.caption if asset else description,
            vqa_passed=(asset.vqa_status == AssetVQAStatus.PASS) if asset else False,
            local_path=asset.local_path if asset else None,
            audit_log=state.errors,
            history=agent.history
        )
