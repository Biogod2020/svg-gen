# Design Spec: Dynamic Audit Standards & Prompt Refinement (SOTA 2.0)

**Date**: 2025-05-22
**Status**: Draft (Approved by User)
**Topic**: Implementing a "Surgical" Pre-flight Refinement Node to dynamically optimize SVG generation prompts and audit criteria while maintaining the SOTA core.

---

## 1. Executive Summary
The goal is to transition from static SVG generation and auditing to a dynamic, intent-aligned system. By introducing a "Pre-flight Refinement" node, we simultaneously generate an optimized generation prompt and a task-specific audit checklist. This approach preserves the core "SOTA" philosophies (Scientificity, Typography, Technical Standards) while ensuring the final output is strictly tailored to the user's specific request.

---

## 2. Architecture & Data Flow

### 2.1 The Refinement Processor
A single LLM call orchestrated before the SVG generation begins. It takes the `user_intent` and produces a structured `PreflightBlueprint`.

**PreflightBlueprint (JSON Schema):**
- `refined_task_directive`: A high-fidelity, technical expansion of the user's prompt.
- `specific_style_hints`: Task-specific aesthetic constraints (palette, layout type).
- `dynamic_audit_checkpoints`: An array of 3-5 checkpoints, each with a `name`, `weight` (totaling 60), and `validation_check`.

### 2.2 Orchestration (LangGraph)
- **Node: `refinement_node`**: Executes the Pre-flight call and updates the `AgentState`.
- **Node: `generation_node`**: Injects `refined_task_directive` into the static core generator prompt.
- **Node: `audit_node`**: Injects `dynamic_audit_checkpoints` into the 40/60 scoring rubric.

---

## 3. Surgical Prompt Design

### 3.1 SVG_GENERATION_PROMPT (The Core)
We will maintain the following **Static Core** principles as immutable rules:
- **Scientific Rigor**: Visual elements must be logically consistent; arrows/flows must represent valid data/factual relationships.
- **Typography & Layout (Redlines)**: 
    - **Zero Overlap**: Absolutely no overlapping fonts, lines, or background elements.
    - **Readability**: SOTA-standard font sizes and high-contrast colors (WCAG compliant).
    - **Technical Standard**: Mandatory `viewBox`, `width="100%"`, and clean XML structure.

**Dynamic Injections**:
- `{{refined_task_directive}}`: Replaces the basic user description.
- `{{specific_style_hints}}`: Injects task-aligned aesthetic guidance.

### 3.2 SVG_AUDIT_PROMPT (The Rubric)
The scoring system remains a **0-100 total**, split into two sections:

#### **Section A: Static Core Quality (40 points)**
- **Scientific & Logical Integrity (20pts)**: Evaluates if the image conveys correct factual/logical relationships.
- **Typography & Technicality (15pts)**: Strictly checks for font overlap, text clarity, and appropriate font sizing.
- **Engineering Standards (5pts)**: Verifies `viewBox` usage and code efficiency.

#### **Section B: Dynamic Intent Alignment (60 points)**
- **Dynamic Checkpoints (60pts)**: Iteratively evaluates the SVG against the `dynamic_audit_checkpoints` generated during Pre-flight.
- *Calculation*: `Sum(checkpoint_n_score * (checkpoint_n_weight / 60))`.

---

## 4. Error Handling & Quality Control
- **"Hard-Failure" Logic**: If any "Static Core" item (e.g., font overlap) receives a critical deduction, the `audit_node` will cap the maximum total score at 60 (Fail), regardless of Intent Alignment.
- **Repair Escalation**: The `SVG_REPAIR_PROMPT` will receive the dynamic checkpoints as part of the "Audit Feedback" to ensure the repair agent is as focused as the auditor.

---

## 5. Success Criteria
- **Intent Accuracy**: Visual assets must contain all specific elements requested by the user.
- **Zero Regression**: No "Primitive" or "Broken" SVGs (overlapping text, missing `viewBox`) should pass the audit.
- **Loop Efficiency**: The refined prompt should lead to a >80% first-pass audit success rate.
