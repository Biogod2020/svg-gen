"""
SVGAgent: Optimized SVG Generation Loop
Streamlined for the SVG Optimization Lab.
"""

import asyncio
from pathlib import Path
from typing import Optional, Tuple, Any

from ...core.gemini_client import GeminiClient
from ...core.types import (
    AgentState,
    AssetEntry,
    AssetSource,
    AssetVQAStatus,
    PreflightBlueprint
)
from pydantic import BaseModel
from .processor import generate_svg_async, repair_svg_async
from .refinement import RefinementProcessor
from ..asset_management.processors.audit import (
    audit_svg_visual_async, 
    render_svg_to_png_base64,
    refine_caption_async
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

    async def run_optimization_loop(
        self, 
        asset_id: str,
        description: str,
        state: AgentState,
        style_hints: str = ""
    ) -> Tuple[bool, Optional[AssetEntry], str]:
        """
        Runs the Generate-Audit-Repair loop for a single SVG asset.
        
        Returns:
            (success, asset_entry, html_code)
        """
        ws_path = Path(state.workspace_path)
        out_path = ws_path / "agent_generated"
        out_path.mkdir(parents=True, exist_ok=True)
        
        print(f"    [SVGAgent] 🚀 Starting SVG optimization loop (ID: {asset_id})...")

        # 0. Pre-flight Refinement
        print(f"    [SVGAgent] 🔍 Refining prompt and generating dynamic standards...")
        refiner = RefinementProcessor(self.client)
        blueprint = await refiner.refine_request_async(description)
        
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
            return False, None, f"<!-- SVG Generation failed for {asset_id} -->"

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
            audit = await audit_svg_visual_async(
                self.client, 
                svg_code, 
                description, 
                state=state, 
                svg_path=file_path,
                blueprint=blueprint
            )

            if audit and audit.get("result") == "pass":
                is_valid = True
                print(f"    [SVGAgent] ✅ Audit PASSED (ID: {asset_id})")
                break
            
            issues = audit.get("issues", ["Audit failed or timed out"]) if audit else ["API Timeout/Error"]
            suggestions = audit.get("suggestions", []) if audit else []
            
            print(f"    [SVGAgent] ⚠️ Audit NOT PASSED: {issues[0][:100]}...")
            
            if attempt < self.MAX_REPAIR_ATTEMPTS:
                print(f"    [SVGAgent] 🛠️ Attempting precise repair via Reflection Loop...")
                png_b64 = render_svg_to_png_base64(svg_code)
                new_svg = await repair_svg_async(
                    self.client, 
                    description, 
                    svg_code, 
                    issues, 
                    suggestions, 
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
        
        return True, asset, html_code


class SVGResult(BaseModel):
    asset_id: str
    svg_code: str
    caption: str
    vqa_passed: bool
    local_path: Optional[str] = None
    audit_log: list[str] = []


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
        success, asset, html = await agent.run_optimization_loop(
            asset_id=asset_id,
            description=description,
            state=state,
            style_hints=style_hints
        )
        
        # Read final SVG code from disk (CAS or agent_generated)
        ws_p = Path(workspace_path)
        svg_file = ws_p / "agent_generated" / f"{asset_id}.svg"
        svg_code = svg_file.read_text(encoding="utf-8") if svg_file.exists() else ""
        
        return SVGResult(
            asset_id=asset_id,
            svg_code=svg_code,
            caption=asset.caption or description,
            vqa_passed=(asset.vqa_status == AssetVQAStatus.PASS),
            local_path=asset.local_path,
            audit_log=state.errors
        )
