"""
Refinement Processor

Refines user prompts into structured PreflightBlueprints.
"""

import json
from typing import Optional, List
from src.core.gemini_client import GeminiClient
from src.core.types import PreflightBlueprint, AuditCriterion

SVG_REFINEMENT_PROMPT = """You are a Senior SVG Technical Architect. Your task is to analyze a user's request for an SVG illustration and refine it into a structured execution plan (PreflightBlueprint).

### 🎯 GOAL
Translate the user intent into a high-fidelity technical directive, style hints, and dynamic audit checkpoints. Your plan must ensure the output adheres to State-of-the-Art (SOTA) aesthetic standards: clean geometry, professional color theory, and clear visual hierarchy. Be extremely demanding in your quality standards.

### ⚖️ WEIGHTING RULES
- The `dynamic_audit_checkpoints` weights should ideally sum to 60.0.
- Use weights to prioritize the most important aspects of the illustration.
- Provide at least 3-4 specific, granular checkpoints.
- Include at least one checkpoint dedicated to "Aesthetic Professionalism and SOTA Polish".

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
                    check="Verify the SVG matches the core intent of the original request.",
                ),
                AuditCriterion(
                    name="Technical Soundness",
                    weight=30.0,
                    check="Ensure the SVG is responsive, valid, and uses a professional aesthetic.",
                ),
            ],
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
                temperature=0.2,
            )

            if not response.success or not response.json_data:
                return self.get_fallback_blueprint(user_prompt)

            # Validate and parse into model
            try:
                data = response.json_data
                if not isinstance(data, dict):
                    return self.get_fallback_blueprint(user_prompt)

                # SOTA Fix: Handle model wrapping in a root key
                if "preflight_blueprint" in data:
                    data = data["preflight_blueprint"]
                elif "blueprint" in data:
                    data = data["blueprint"]

                # SOTA Fix: Normalize field names for PreflightBlueprint
                if "title" in data and "refined_task_directive" not in data:
                    data["refined_task_directive"] = data["title"]
                if "style_hints" in data and "specific_style_hints" not in data:
                    data["specific_style_hints"] = data["style_hints"]
                if (
                    "audit_checkpoints" in data
                    and "dynamic_audit_checkpoints" not in data
                ):
                    data["dynamic_audit_checkpoints"] = data["audit_checkpoints"]

                # SOTA Fix: Normalize field names for AuditCriterion
                if "dynamic_audit_checkpoints" in data:
                    for cp in data["dynamic_audit_checkpoints"]:
                        if "criterion" in cp and "name" not in cp:
                            cp["name"] = cp["criterion"]
                        if "instruction" in cp and "check" not in cp:
                            cp["check"] = cp["instruction"]
                        elif "description" in cp and "check" not in cp:
                            cp["check"] = cp["description"]

                return PreflightBlueprint(**data)
            except Exception as e:
                print(f"[RefinementProcessor] Validation failed: {e}")
                return self.get_fallback_blueprint(user_prompt)

        except Exception as e:
            print(f"[RefinementProcessor] Refinement failed: {e}")
            return self.get_fallback_blueprint(user_prompt)
