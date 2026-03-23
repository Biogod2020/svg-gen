"""
Refinement Processor

Refines user prompts into structured PreflightBlueprints.
"""

import json
from typing import Optional, List
from ...core.gemini_client import GeminiClient
from ...core.types import PreflightBlueprint, AuditCriterion

SVG_REFINEMENT_PROMPT = """You are a Senior SVG Technical Architect. Your task is to analyze a user's request for an SVG illustration and refine it into a structured execution plan (PreflightBlueprint).

### 🎯 GOAL
Translate the user intent into a high-fidelity technical directive, style hints, and dynamic audit checkpoints.

### 📋 JSON SCHEMA
Your output MUST be a valid JSON object matching this schema:
{{
  "refined_task_directive": "A detailed, technical expansion of the user's original request.",
  "specific_style_hints": "Specific aesthetic and technical guidelines (e.g., 'Use professional blue/gray palette', 'Avoid complex gradients').",
  "dynamic_audit_checkpoints": [
    {{
      "name": "Criterion Name",
      "weight": 30.0,
      "check": "Specific instruction for the auditor to verify this criterion."
    }}
  ],
  "version": "2.0"
}}

### ⚖️ WEIGHTING RULES
- The `dynamic_audit_checkpoints` weights should ideally sum to 60.0.
- Use weights to prioritize the most important aspects of the illustration.
- Provide at least 2-3 specific checkpoints.

### INPUT USER REQUEST:
{user_prompt}
"""

class RefinementProcessor:
    def __init__(self, client: GeminiClient):
        self.client = client

    def get_fallback_blueprint(self, user_prompt: str) -> PreflightBlueprint:
        """Returns a safe fallback blueprint when AI refinement fails."""
        return PreflightBlueprint(
            refined_task_directive=f"Create a professional SVG illustration based on: {user_prompt}",
            specific_style_hints="Maintain visual clarity, professional hierarchy, and responsive design.",
            dynamic_audit_checkpoints=[
                AuditCriterion(
                    name="Visual Alignment",
                    weight=30.0,
                    check="Verify the SVG matches the core intent of the original request."
                ),
                AuditCriterion(
                    name="Technical Soundness",
                    weight=30.0,
                    check="Ensure the SVG is responsive, valid, and uses a professional aesthetic."
                )
            ]
        )

    async def refine_request_async(self, user_prompt: str) -> PreflightBlueprint:
        """
        Calls Gemini to refine a user prompt into a PreflightBlueprint.
        Handles failures by returning a default/fallback blueprint.
        """
        prompt = SVG_REFINEMENT_PROMPT.format(user_prompt=user_prompt)
        
        try:
            response = await self.client.generate_async(
                prompt=prompt,
                system_instruction="You are a Senior SVG Technical Architect. Output ONLY valid JSON.",
                temperature=0.2
            )
            
            if not response.success or not response.json_data:
                return self.get_fallback_blueprint(user_prompt)
            
            # Validate and parse into model
            try:
                # json_data might be a dict already if GeminiClient parsed it
                data = response.json_data
                if isinstance(data, dict):
                    return PreflightBlueprint(**data)
                else:
                    return self.get_fallback_blueprint(user_prompt)
            except Exception as e:
                print(f"[RefinementProcessor] Validation failed: {e}")
                return self.get_fallback_blueprint(user_prompt)

        except Exception as e:
            print(f"[RefinementProcessor] Refinement failed: {e}")
            return self.get_fallback_blueprint(user_prompt)
