"""
SVGAgent: Optimized SVG Generation Loop
Streamlined for the SVG Optimization Lab.
"""

import asyncio
from pathlib import Path
from typing import Optional, Tuple, Any, List, Dict, AsyncGenerator

from src.core.gemini_client import GeminiClient
from src.core.types import (
    AgentState,
    AssetEntry,
    AssetSource,
    AssetVQAStatus,
    PreflightBlueprint,
    AuditResult,
    AuditIssue,
)
from pydantic import BaseModel
from .processor import generate_svg_async, repair_svg_async
from .refinement import RefinementProcessor
from ..asset_management.processors.audit import (
    audit_svg_visual_async,
    render_svg_to_png_base64,
    get_svg_render_base64_async,
    refine_caption_async,
    sanitize_svg,
)
from ..asset_management.utils import generate_figure_html


class SVGAgent:
    """
    Sub-Agent dedicated to SVG generation.
    Implements a formal Reflection Loop to improve SVG quality based on audit feedback.
    """

    @staticmethod
    def validate_svg_structure(svg_code: str) -> Tuple[bool, str]:
        """[SOTA 3.0] Fast local SVG structure check (Linter)"""
        if not svg_code:
            return False, "Empty SVG code"

        # 1. XML Parsing check
        try:
            from lxml import etree

            parser = etree.XMLParser(recover=False)
            etree.fromstring(svg_code.encode("utf-8"), parser=parser)
        except Exception as e:
            return False, f"Invalid XML structure: {str(e)}"

        # 2. ViewBox check
        import re

        if not re.search(r'viewBox=["\']', svg_code):
            return (
                False,
                "Missing 'viewBox' attribute. SOTA SVGs require fluid viewBox.",
            )

        return True, "Structure OK"

    MAX_REPAIR_ATTEMPTS = 5

    def __init__(self, client: Optional[GeminiClient] = None, debug: bool = False):
        self.client = client or GeminiClient()
        self.debug = debug
        self.history: List[Dict[str, Any]] = []

    def _make_iteration(
        self, index: int, thought: str, status: str, score: float = 0
    ) -> Dict[str, Any]:
        return {
            "iteration": index,
            "svg_code": "",
            "vqa_results": AuditResult(
                status=AssetVQAStatus(status),
                score=score,
                issues=[],
                suggestions=[],
                summary=thought,
                thought=thought,
            ),
            "thoughts": thought,
            "png_b64": "",
        }

    async def run_optimization_loop(
        self, asset_id: str, description: str, state: AgentState, style_hints: str = ""
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """[SOTA 3.0] 闭环优化逻辑：预检 -> 统一审计 -> 鲁棒修复"""
        self.history = []
        ws_path = Path(state.workspace_path)
        out_path = ws_path / "agent_generated"
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / f"{asset_id}.svg"

        print(f"    [SVGAgent] 🚀 Starting SOTA 3.0 loop (ID: {asset_id})...")

        # 0. Refinement
        yield self._make_iteration(0, "Refining prompt...", "PENDING")
        refiner = RefinementProcessor(self.client)
        blueprint = await refiner.refine_request_async(description)

        # 1. Initial Generation
        yield self._make_iteration(0, "Generating initial SVG...", "PENDING")
        svg_code = await generate_svg_async(
            self.client,
            description,
            state=state,
            style_hints=style_hints,
            blueprint=blueprint,
        )

        if not svg_code:
            print(f"    [SVGAgent] ❌ Initial generation failed (ID: {asset_id})")
            return

        attempt = 0
        is_valid = False

        # 2. Reflection Loop: Audit & Repair
        while attempt < self.MAX_REPAIR_ATTEMPTS:
            attempt += 1

            # Step A: Pre-flight Structure Check (Fast & Local)
            valid_struct, msg = self.validate_svg_structure(svg_code)
            if not valid_struct:
                print(f"    [SVGAgent] ❌ Pre-flight failed: {msg}")
                audit_obj = AuditResult(
                    status=AssetVQAStatus.FAIL,
                    score=20.0,
                    summary=msg,
                    issues=[AuditIssue(description=msg, severity="high")],
                )
            else:
                # Step B: Unified SOTA Audit (VLM)
                print(f"    [SVGAgent] 📋 Unified SOTA Audit (Attempt {attempt})...")
                # Persist to disk for possible debugging
                file_path.write_text(svg_code, encoding="utf-8")

                audit_dict = await audit_svg_visual_async(
                    self.client,
                    svg_code,
                    description,
                    state=state,
                    blueprint=blueprint,
                )

                if audit_dict:
                    status = (
                        AssetVQAStatus.PASS
                        if audit_dict.get("result") == "pass"
                        else AssetVQAStatus.FAIL
                    )
                    audit_obj = AuditResult(
                        status=status,
                        score=float(audit_dict.get("overall_score", 0)),
                        issues=[AuditIssue(**i) for i in audit_dict.get("issues", [])],
                        suggestions=audit_dict.get("suggestions", []),
                        summary=f"Logic: {audit_dict.get('logic_score')}, Visual: {audit_dict.get('visual_score')}, Aesthetic: {audit_dict.get('aesthetic_score')}",
                        thought=audit_dict.get("thought", ""),
                    )
                else:
                    audit_obj = AuditResult(
                        status=AssetVQAStatus.FAIL,
                        score=0.0,
                        summary="Audit failed or returned invalid JSON",
                        thought="No structured response from VLM",
                    )

            # Step C: Capture Iteration History
            png_b64 = await get_svg_render_base64_async(svg_code)
            iteration = {
                "iteration": attempt,
                "svg_code": sanitize_svg(svg_code),
                "vqa_results": audit_obj,
                "thoughts": audit_obj.thought or state.thoughts,
                "png_b64": png_b64,
            }
            self.history.append(iteration)
            yield iteration

            if audit_obj.status == AssetVQAStatus.PASS:
                is_valid = True
                print(f"    [SVGAgent] ✅ Audit PASSED (ID: {asset_id})")
                break

            print(
                f"    [SVGAgent] ⚠️ Audit NOT PASSED: {audit_obj.issues[0].description[:100] if audit_obj.issues else 'No specific issues'}..."
            )

            # Step D: Repair
            if attempt < self.MAX_REPAIR_ATTEMPTS:
                print(
                    f"    [SVGAgent] 🛠️ Attempting precise repair via Reflection Loop..."
                )

                # Build concise history
                history_summary_parts = []
                for h in self.history[-1:]:  # Only last iteration for focus
                    vqa = h["vqa_results"]
                    history_summary_parts.append(
                        f"- Iteration {h['iteration']}: Score {vqa.score}/100. Top issue: {vqa.issues[0].description[:100] if vqa.issues else 'Unknown'}"
                    )
                history_summary = "\n".join(history_summary_parts)

                new_svg = await repair_svg_async(
                    self.client,
                    description,
                    svg_code,
                    [i.description for i in audit_obj.issues],
                    audit_obj.suggestions,
                    state=state,
                    rendered_image_b64=png_b64,
                    blueprint=blueprint,
                    history_summary=history_summary,
                )

                if not new_svg:
                    print(f"    [SVGAgent] ⚠️ Repair Agent failed to return code.")
                else:
                    svg_code = new_svg
                    print(
                        f"    [SVGAgent] 🛠️ Repair complete (new len: {len(svg_code)})"
                    )
            else:
                print(f"\n⚠️ [SVGAgent] Exhausted {self.MAX_REPAIR_ATTEMPTS} attempts.")

        # 3. Finalization
        print(f"    [SVGAgent] ✍️ Refining caption based on visual evidence...")
        png_b64 = await get_svg_render_base64_async(svg_code)
        if png_b64:
            final_caption = await refine_caption_async(
                self.client, png_b64, description, state=state
            )
        else:
            final_caption = description

        uar = state.get_uar()
        asset = uar.add_asset_atomic(
            asset_id=asset_id,
            content=svg_code.encode("utf-8"),
            source=AssetSource.AI,
            semantic_label=description[:100],
            alt_text=description,
            caption=final_caption,
            vqa_status=AssetVQAStatus.PASS if is_valid else AssetVQAStatus.FAIL,
        )

        html_code = generate_figure_html(asset, final_caption, workspace_path=ws_path)

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
    client: Optional[GeminiClient] = None,
) -> SVGResult:
    """
    [Standard Interface] Generates, audits, and repairs an SVG asset.
    Returns a single SVGResult object containing the final code and caption.
    """
    client = client or GeminiClient()
    state = AgentState(job_id=f"job-{asset_id}", workspace_path=workspace_path)

    agent = SVGAgent(client=client)
    async for iteration in agent.run_optimization_loop(
        asset_id=asset_id, description=description, state=state, style_hints=style_hints
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
        history=agent.history,
    )
