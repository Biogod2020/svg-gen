import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.agents.svg_generation.agent import SVGAgent, optimize_svg_pipeline
from src.core.types import AgentState, AssetVQAStatus, AssetEntry, AssetSource, AuditResult
import os
from pathlib import Path

@pytest.fixture
def mock_gemini_client():
    return MagicMock()

@pytest.fixture
def agent_state(tmp_path):
    state = AgentState(
        job_id="test-job",
        workspace_path=str(tmp_path)
    )
    return state

@pytest.mark.asyncio
async def test_run_optimization_loop_captures_history(mock_gemini_client, agent_state, tmp_path):
    agent = SVGAgent(client=mock_gemini_client)
    
    # Mock RefinementProcessor
    with patch("src.agents.svg_generation.agent.RefinementProcessor") as mock_refiner_cls:
        mock_refiner = mock_refiner_cls.return_value
        mock_refiner.refine_request_async = AsyncMock(return_value=MagicMock())
        
        # Mock generate_svg_async
        with patch("src.agents.svg_generation.agent.generate_svg_async", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "<svg>Initial</svg>"
            
            # Mock audit_svg_visual_async
            with patch("src.agents.svg_generation.agent.audit_svg_visual_async", new_callable=AsyncMock) as mock_audit:
                # First audit fails, second succeeds
                mock_audit.side_effect = [
                    {
                        "result": "fail",
                        "overall_score": 45,
                        "issues": [{"description": "Issue 1", "box": [0, 0, 100, 100], "severity": "high"}],
                        "suggestions": ["Fix it"],
                        "quality_assessment": "Needs improvement",
                        "thought": "Thinking..."
                    },
                    {
                        "result": "pass",
                        "overall_score": 95,
                        "issues": [],
                        "suggestions": [],
                        "quality_assessment": "Perfect",
                        "thought": "Done."
                    }
                ]
                
                # Mock repair_svg_async
                with patch("src.agents.svg_generation.agent.repair_svg_async", new_callable=AsyncMock) as mock_repair:
                    mock_repair.return_value = "<svg>Repaired</svg>"
                    
                    # Mock render_svg_to_png_base64
                    with patch("src.agents.svg_generation.agent.render_svg_to_png_base64") as mock_render:
                        mock_render.return_value = "fake_b64_image"
                        
                        # Mock refine_caption_async
                        with patch("src.agents.svg_generation.agent.refine_caption_async", new_callable=AsyncMock) as mock_refine_cap:
                            mock_refine_cap.return_value = "Refined Caption"
                            
                            # Mock state.get_uar().add_asset_atomic
                            mock_uar = MagicMock()
                            mock_asset = AssetEntry(
                                id="test_asset",
                                source=AssetSource.AI,
                                local_path="agent_generated/test_asset.svg",
                                semantic_label="test",
                                caption="Refined Caption",
                                vqa_status=AssetVQAStatus.PASS
                            )
                            mock_uar.add_asset_atomic.return_value = mock_asset
                            
                            with patch.object(AgentState, "get_uar", return_value=mock_uar):
                                all_iterations = []
                                async for iteration in agent.run_optimization_loop(
                                    asset_id="test_asset",
                                    description="A test SVG",
                                    state=agent_state
                                ):
                                    all_iterations.append(iteration)

                                # Filter out placeholder iterations (iteration 0)
                                iterations = [i for i in all_iterations if i["iteration"] > 0]

                                assert len(iterations) == 2
                                assert len(agent.history) == 2                                
                                # Check first entry
                                assert iterations[0]["svg_code"] == "<svg>Initial</svg>"
                                assert iterations[0]["vqa_results"].status == AssetVQAStatus.FAIL
                                assert iterations[0]["png_b64"] == "fake_b64_image"
                                assert iterations[0]["thoughts"] == "Thinking..."
                                
                                # Check second entry
                                assert iterations[1]["svg_code"] == "<svg>Repaired</svg>"
                                assert iterations[1]["vqa_results"].status == AssetVQAStatus.PASS

@pytest.mark.asyncio
async def test_optimize_svg_pipeline_returns_history(mock_gemini_client, tmp_path):
    mock_asset = MagicMock(spec=AssetEntry)
    mock_asset.caption = "Test Caption"
    mock_asset.vqa_status = AssetVQAStatus.PASS
    mock_asset.local_path = "path/to/svg"

    async def mock_gen(*args, **kwargs):
        yield {"svg_code": "<svg></svg>", "vqa_results": MagicMock(spec=AuditResult), "png_b64": "...", "thoughts": "...", "iteration": 1}

    with patch("src.agents.svg_generation.agent.SVGAgent") as MockAgent:
        mock_agent_instance = MockAgent.return_value
        mock_agent_instance.run_optimization_loop = mock_gen
        mock_agent_instance.history = [{"svg_code": "<svg></svg>", "vqa_results": MagicMock(spec=AuditResult), "png_b64": "...", "thoughts": "...", "iteration": 1}]
        
        # Mock file reading
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value="<svg></svg>"):
                # Mock state.get_uar()
                mock_uar = MagicMock()
                mock_uar.assets = {"test": mock_asset}
                with patch.object(AgentState, "get_uar", return_value=mock_uar): 
                    result = await optimize_svg_pipeline(
                        asset_id="test",
                        description="test",
                        workspace_path=str(tmp_path),
                        client=mock_gemini_client
                    )
                    
                    assert hasattr(result, "history")
                    assert len(result.history) == 1
                    assert result.history[0]["svg_code"] == "<svg></svg>"
