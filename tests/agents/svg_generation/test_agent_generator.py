import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.agents.svg_generation.agent import SVGAgent
from src.core.types import (
    AgentState,
    AssetVQAStatus,
    PreflightBlueprint,
    AuditResult,
    AuditIssue,
    AssetEntry,
    AssetSource,
)


@pytest.mark.asyncio
async def test_run_optimization_loop_generator(tmp_path):
    # Setup
    workspace_path = str(tmp_path)
    state = AgentState(job_id="test-job", workspace_path=workspace_path)
    agent = SVGAgent(debug=True)

    # Mock dependencies
    with (
        patch(
            "src.agents.svg_generation.agent.RefinementProcessor"
        ) as mock_refiner_cls,
        patch("src.agents.svg_generation.agent.generate_svg_async") as mock_generate,
        patch("src.agents.svg_generation.agent.audit_svg_visual_async") as mock_audit,
        patch("src.agents.svg_generation.agent.repair_svg_async") as mock_repair,
        patch(
            "src.agents.svg_generation.agent.refine_caption_async"
        ) as mock_refine_caption,
        patch(
            "src.agents.svg_generation.agent.get_svg_render_base64_async"
        ) as mock_render,
    ):
        # Setup mocks
        mock_refiner = mock_refiner_cls.return_value
        mock_refiner.refine_request_async = AsyncMock(
            return_value=PreflightBlueprint(
                refined_task_directive="Refined",
                specific_style_hints="Style",
                dynamic_audit_checkpoints=[],
            )
        )

        mock_generate.return_value = "<svg viewBox='0 0 100 100'>initial</svg>"

        # First audit fails, second passes
        mock_audit.side_effect = [
            {
                "result": "fail",
                "overall_score": 0.5,
                "issues": [{"description": "Missing circle", "severity": "medium"}],
                "suggestions": ["Add a circle"],
                "quality_assessment": "Bad",
                "thought": "I think it's bad",
            },
            {
                "result": "pass",
                "overall_score": 1.0,
                "issues": [],
                "suggestions": [],
                "quality_assessment": "Good",
                "thought": "I think it's good",
            },
        ]

        mock_repair.return_value = "<svg viewBox='0 0 100 100'>repaired</svg>"
        mock_refine_caption.return_value = "Final caption"
        mock_render.return_value = "base64_png"

        # Run the loop
        all_iterations = []
        try:
            async for iteration in agent.run_optimization_loop(
                asset_id="test_svg", description="A test SVG", state=state
            ):
                all_iterations.append(iteration)
        except TypeError as e:
            pytest.fail(f"run_optimization_loop is not an async generator: {e}")

        # Skip the two initial status updates (iteration 0)
        iterations = [i for i in all_iterations if i["iteration"] > 0]

        # Assertions
        assert len(iterations) >= 2
        assert iterations[0]["svg_code"] == "<svg viewBox='0 0 100 100'>initial</svg>"
        assert iterations[0]["vqa_results"].status == AssetVQAStatus.FAIL
        assert iterations[0]["iteration"] == 1

        assert iterations[1]["svg_code"] == "<svg viewBox='0 0 100 100'>repaired</svg>"
        assert iterations[1]["vqa_results"].status == AssetVQAStatus.PASS
        assert iterations[1]["iteration"] == 2

        # Verify last iteration has the final result marker if we decide to include it
        # Or check if we can get the final asset another way
        assert state.get_uar().assets["test_svg"].vqa_status == AssetVQAStatus.PASS
