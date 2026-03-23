import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.agents.svg_generation.refinement import RefinementProcessor
from src.core.gemini_client import GeminiClient, GeminiResponse
from src.core.types import PreflightBlueprint, AuditCriterion

class TestRefinementProcessor(unittest.TestCase):
    def setUp(self):
        self.mock_gemini_client = MagicMock(spec=GeminiClient)
        self.processor = RefinementProcessor(self.mock_gemini_client)

    def test_refine_request_success(self):
        # Mock successful response
        mock_response = GeminiResponse(
            success=True,
            text='{"refined_task_directive": "Refined task", "specific_style_hints": "Style hints", "dynamic_audit_checkpoints": [{"name": "Crit 1", "weight": 30.0, "check": "Check 1"}, {"name": "Crit 2", "weight": 30.0, "check": "Check 2"}], "version": "2.0"}',
            json_data={
                "refined_task_directive": "Refined task",
                "specific_style_hints": "Style hints",
                "dynamic_audit_checkpoints": [
                    {"name": "Crit 1", "weight": 30.0, "check": "Check 1"},
                    {"name": "Crit 2", "weight": 30.0, "check": "Check 2"}
                ],
                "version": "2.0"
            }
        )
        self.mock_gemini_client.generate_async = AsyncMock(return_value=mock_response)
        
        blueprint = asyncio.run(self.processor.refine_request_async("Original prompt"))
        
        self.assertIsInstance(blueprint, PreflightBlueprint)
        self.assertEqual(blueprint.refined_task_directive, "Refined task")
        self.assertEqual(len(blueprint.dynamic_audit_checkpoints), 2)
        # Weight should be normalized to 30 each (total 60)
        self.assertEqual(blueprint.dynamic_audit_checkpoints[0].weight, 30.0)

    def test_refine_request_failure_invalid_json(self):
        # Mock response with invalid JSON
        mock_response = GeminiResponse(
            success=True,
            text='Invalid JSON',
            json_data=None
        )
        self.mock_gemini_client.generate_async = AsyncMock(return_value=mock_response)
        
        blueprint = asyncio.run(self.processor.refine_request_async("Original prompt"))
        
        # Should return fallback blueprint
        self.assertIsInstance(blueprint, PreflightBlueprint)
        self.assertIn("Original prompt", blueprint.refined_task_directive)
        self.assertTrue(len(blueprint.dynamic_audit_checkpoints) > 0)

    def test_refine_request_api_failure(self):
        # Mock API failure
        mock_response = GeminiResponse(
            success=False,
            error="API Error"
        )
        self.mock_gemini_client.generate_async = AsyncMock(return_value=mock_response)
        
        blueprint = asyncio.run(self.processor.refine_request_async("Original prompt"))
        
        # Should return fallback blueprint
        self.assertIsInstance(blueprint, PreflightBlueprint)
        self.assertIn("Original prompt", blueprint.refined_task_directive)

if __name__ == "__main__":
    unittest.main()
