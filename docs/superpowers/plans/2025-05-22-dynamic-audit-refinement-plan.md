# Dynamic Audit Standards & Prompt Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a "SOTA Pre-flight Refinement" system that dynamically optimizes SVG generation prompts and audit criteria based on user input, ensuring high-fidelity results and strict quality control.

**Architecture:** A new `RefinementProcessor` will perform a single LLM call to generate a `PreflightBlueprint`. This blueprint contains a refined task directive, style hints, and dynamic audit checkpoints with weights. These are then surgically injected into existing generation and audit prompts.

**Tech Stack:** Python 3.x, Pydantic v2, Gemini API.

---

### Task 1: Data Models & Types

**Files:**
- Modify: `src/core/types.py`

- [ ] **Step 1: Add `AuditCriterion` and `PreflightBlueprint` models**
Add these models to `src/core/types.py`. Include a `@model_validator` to normalize weights so the sum of `dynamic_audit_checkpoints` weights always equals 60.0.

```python
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional

class AuditCriterion(BaseModel):
    name: str
    weight: float = Field(..., description="Weight of this criterion (0-60)")
    check: str = Field(..., description="Specific validation check instruction")

class PreflightBlueprint(BaseModel):
    refined_task_directive: str
    specific_style_hints: str
    dynamic_audit_checkpoints: List[AuditCriterion]
    version: str = "2.0"

    @model_validator(mode='after')
    def normalize_weights(self) -> 'PreflightBlueprint':
        total = sum(c.weight for c in self.dynamic_audit_checkpoints)
        if total > 0:
            for c in self.dynamic_audit_checkpoints:
                c.weight = (c.weight / total) * 60.0
        return self
```

- [ ] **Step 2: Commit changes**
```bash
git add src/core/types.py
git commit -m "feat(core): add PreflightBlueprint and AuditCriterion models with normalization"
```

---

### Task 2: Implement Refinement Processor

**Files:**
- Create: `src/agents/svg_generation/refinement.py`
- Test: `tests/agents/svg_generation/test_refinement.py`

- [ ] **Step 1: Write the failing test for refinement logic**
Verify the refinement processor correctly parses a JSON response and handles API failures by returning a default/fallback blueprint.

- [ ] **Step 2: Implement `RefinementProcessor`**
Create `src/agents/svg_generation/refinement.py`. Implement `refine_request_async` which calls Gemini. If the call fails or returns invalid JSON, it MUST return a `get_fallback_blueprint()` (e.g., 50/50 split on generic criteria).

- [ ] **Step 3: Run tests and verify success**
Run `pytest tests/agents/svg_generation/test_refinement.py`.

- [ ] **Step 4: Commit changes**
```bash
git add src/agents/svg_generation/refinement.py tests/agents/svg_generation/test_refinement.py
git commit -m "feat(svg): implement RefinementProcessor with fallback logic"
```

---

### Task 3: Surgical Prompt Update - Generation

**Files:**
- Modify: `src/agents/svg_generation/processor.py`

- [ ] **Step 1: Update `SVG_GENERATION_PROMPT`**
Remove hardcoded specifics. Add placeholders for `{refined_task_directive}` and `{style_hints}`. Ensure "Scientific Rigor" and "Zero Overlap" are hardcoded.

- [ ] **Step 2: Update `generate_svg_async` signature**
Update `async def generate_svg_async(...)` to accept an optional `blueprint: Optional[PreflightBlueprint] = None`. Use blueprint fields if present, else fallback to the original description.

- [ ] **Step 3: Commit changes**
```bash
git add src/agents/svg_generation/processor.py
git commit -m "feat(svg): surgically update generation prompt and function signature"
```

---

### Task 4: Surgical Prompt Update - Audit

**Files:**
- Modify: `src/agents/asset_management/processors/audit.py`

- [ ] **Step 1: Update `SVG_AUDIT_PROMPT`**
Refactor the rubric to the 40/60 split. Hardcode the 40pt "Static Core". Add placeholders for `{dynamic_checkpoints}`.

- [ ] **Step 2: Update `audit_svg_visual_async` signature**
Update `async def audit_svg_visual_async(...)` to accept `blueprint: Optional[PreflightBlueprint] = None`. 

- [ ] **Step 3: Implement 40/60 scoring and Hard-Failure logic**
Update the scoring logic to use the blueprint's checkpoints for the 60% intent portion. Implement the "cap at 60" rule if any Static Core items fail.

- [ ] **Step 4: Commit changes**
```bash
git add src/agents/asset_management/processors/audit.py
git commit -m "feat(audit): implement 40/60 dynamic scoring and hard-failure cap"
```

---

### Task 5: Integration in SVGAgent Loop

**Files:**
- Modify: `src/agents/svg_generation/agent.py`

- [ ] **Step 1: Integrate `RefinementProcessor` into `run_optimization_loop`**
Call `refine_request_async` at the start of the loop. Store the `PreflightBlueprint` in the state. Pass it to generation and audit calls.

- [ ] **Step 2: Update Repair logic**
Ensure the repair prompt also receives the `dynamic_checkpoints` to focus the repair agent on the specific intent.

- [ ] **Step 3: Verify the whole loop**
Run a full Generate-Audit-Repair cycle with a complex prompt. Verify the `audit_log` reflects the dynamic criteria.

- [ ] **Step 4: Commit changes**
```bash
git add src/agents/svg_generation/agent.py
git commit -m "feat(svg): integrate pre-flight refinement into the main agent loop"
```

---

### Task 6: Final Verification & Documentation

- [ ] **Step 1: Run all tests**
Run `pytest` to ensure no regressions.

- [ ] **Step 2: Final commit**
```bash
git commit --allow-empty -m "chore(svg): complete dynamic audit standards and prompt refinement track"
```
