"""
Audit Processor

Handles visual and code-based auditing of assets.
"""

import re
import json
import base64
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

from ....core.gemini_client import GeminiClient
from ....core.types import AgentState, PreflightBlueprint


VISUAL_AUDIT_PROMPT = """You are a senior visual editor and content auditor. Your task is to evaluate this image against its intended purpose with high precision.

## Intent Description
{intent_description}

## Standardized Scoring Rubric (0-100)

1. **Information Accuracy (40%)**:
   - Does the image correctly represent the intended information?
   - Deduct for factual errors, misleading elements, or missed requirements.

2. **Visual Clarity & Composition (30%)**:
   - Is the content clear and easy to understand at a glance?
   - Check contrast, balance, and focus. Deduct for clutter or poor legibility.

3. **Professional Quality (30%)**:
   - Check for professional aesthetics, consistent styling, and high-fidelity output.
   - Deduct for low resolution, artifacts, or an unprofessional "primitive" feel.

## Performance Mapping
- 90-100: pass | Exceptional, ready for premium publication.
- 80-89: pass | High quality, meets all core requirements.
- 65-79: needs_revision | Functional but requires specific refinements.
- <65: fail | Significant quality or accuracy issues.

## Output (JSON only)
```json
{{
  "accuracy_score": 0,
  "clarity_score": 0,
  "quality_score": 0,
  "overall_score": 0,
  "result": "pass|fail|needs_revision",
  "issues": [],
  "suggestions": [],
  "quality_assessment": "Summary of pros and cons."
}}
```
"""

SVG_AUDIT_PROMPT = """You are a senior SVG technical auditor. Evaluate the provided code against technical and visual standards.

## Intent Description
{intent_description}

## SVG Code
```svg
{svg_code}
```

## Standardized Scoring Rubric (0-100)

1. **Information Integrity (40%)**:
   - Does the SVG accurately convey the intended information?
2. **Code Quality & Technicality (30%)**:
   - Check for efficient path usage, semantic grouping (<g>), responsiveness (viewBox), and valid XML.
3. **Visual Clarity (30%)**:
   - Evaluate layout, text legibility, and appropriate use of strokes and colors.

## Performance Mapping
- 90-100: pass | Textbook quality, efficient code.
- 80-89: pass | Meets professional standards.
- 65-79: needs_revision | Functional but lacks polish or technical optimization.
- <65: fail | Inaccurate or technically broken.

## Output (JSON only)
```json
{{
  "integrity_score": 0,
  "code_score": 0,
  "visual_score": 0,
  "overall_score": 0,
  "result": "pass|fail|needs_revision",
  "issues": [],
  "suggestions": [],
  "quality_assessment": "Summary of findings."
}}
```
"""


def check_svg_syntax(svg_code: str) -> list[str]:
    """检查 SVG 基本语法"""
    issues = []
    if not re.search(r'<svg[^>]*>', svg_code, re.IGNORECASE):
        issues.append("Missing <svg> open tag")
    if not re.search(r'</svg>', svg_code, re.IGNORECASE):
        issues.append("Missing </svg> close tag")
    if '<svg' in svg_code and 'xmlns' not in svg_code:
        issues.append("Missing xmlns declaration")
    return issues


def sanitize_svg(svg_code: str) -> str:
    """
    Sanitize SVG code by removing leading/trailing non-SVG text and fixing basic issues.
    """
    # Remove markdown code blocks if present
    svg_code = re.sub(r'```svg\s*', '', svg_code)
    svg_code = re.sub(r'```', '', svg_code)
    
    # Find the first <svg and last </svg>
    start_match = re.search(r'<svg', svg_code, re.IGNORECASE)
    end_match = re.search(r'</svg>', svg_code, re.IGNORECASE)
    
    if start_match and end_match:
        svg_code = svg_code[start_match.start():end_match.end()]
    elif start_match:
        # If no closing tag, append it
        svg_code = svg_code[start_match.start():] + "\n</svg>"
    
    return svg_code.strip()


def extract_json_payload(text: str) -> Optional[str]:
    """提取 JSON 响应内容"""
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        return json_match.group(0)
    return None


async def audit_image_async(
    client: GeminiClient,
    image_path: Path,
    intent_description: str,
    state: Optional[AgentState] = None
) -> Optional[Dict[str, Any]]:
    """异步审计图片资产"""
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    ext = image_path.suffix.lower()
    mime_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp"
    }.get(ext, "image/png")

    prompt = VISUAL_AUDIT_PROMPT.format(intent_description=intent_description)
    parts = [
        {"text": prompt},
        {"inlineData": {"mimeType": mime_type, "data": image_data}}
    ]

    try:
        response = await client.generate_async(
            parts=parts,
            system_instruction="You are a visual content auditor. Output JSON only.",
            stream=True
        )
        if not response.success:
            return None

        # Capture thoughts
        if state and response.thoughts:
            state.thoughts += f"\n[Image Audit] {response.thoughts}"

        payload = extract_json_payload(response.text)
        return json.loads(payload) if payload else None
    except Exception:
        return None


async def audit_svg_async(
    client: GeminiClient,
    svg_code: str,
    intent_description: str,
    state: Optional[AgentState] = None
) -> Optional[Dict[str, Any]]:
    """异步审计 SVG 资产 (纯代码分析，回退模式)"""
    svg_code = sanitize_svg(svg_code)
    prompt = SVG_AUDIT_PROMPT.format(
        intent_description=intent_description,
        svg_code=svg_code
    )
    try:
        response = await client.generate_async(
            prompt=prompt,
            system_instruction="You are an SVG auditor. Output JSON only.",
            stream=True
        )
        if not response.success:
            return None

        # Capture thoughts
        if state and response.thoughts:
            state.thoughts += f"\n[SVG Code Audit] {response.thoughts}"

        payload = extract_json_payload(response.text)
        return json.loads(payload) if payload else None
    except Exception:
        return None


# ============================================================================
# 语义图注优化 (SOTA 2.0 Post-Fulfillment Alignment)
# ============================================================================

CAPTION_REFINEMENT_PROMPT = """You are a Senior Editor. Your task is to write a high-fidelity, structured, and context-aware caption for the provided visual asset.

### 🎯 Core Mission: Argumentative Support
The caption MUST serve as a bridge between the visual evidence and the narrative logic. Do not just describe the image in isolation; explain how it validates, illustrates, or extends the specific argument being made.

### 🎨 SOTA 2.0 Styling Rules:
- **Structure**: Use a "Title: Description" format.
- **Emphasis**: **Bold** the core subject and key visual labels (e.g., **RA**, **Vector V**).
- **Conciseness**: Every word must add analytical value to the reader's understanding.

### Instructions:
1. **Analyze the Visual Evidence**: Identify specific labels, colors, and spatial arrangements.
2. **Outcome**: Create a caption that makes the image an indispensable part of the narrative proof.

### Input Data:
- **Original Intent**: {original_intent}

### Output Format:
**[Refined Title]**: [Professional description that integrates visual evidence].
(Output ONLY the final caption text)
"""

async def refine_caption_async(
    client: GeminiClient,
    image_b64: str,
    original_intent: str,
    state: Optional[AgentState] = None
) -> str:
    """
    根据视觉证据优化资产描述（图注）。
    """
    prompt = CAPTION_REFINEMENT_PROMPT.format(original_intent=original_intent)
    
    parts = [
        {"text": "Analyze this final visual asset (Image Evidence):"},
        {
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": image_b64
            }
        },
        {"text": prompt}
    ]
    
    try:
        response = await client.generate_async(
            parts=parts,
            system_instruction="You are a Technical Copywriter. Write structured, beautiful captions based on visual evidence.",
            temperature=0.0
        )
        
        if response.success:
            return response.text.strip().replace("Refined Title:", "").replace("[", "").replace("]", "")
        return original_intent
    except Exception as e:
        print(f"    [Audit] Caption refinement failed: {e}")
        return original_intent


# ============================================================================
# SVG 渲染与视觉审计 (SOTA 2.0 双路交叉验证)
# ============================================================================

SVG_VISUAL_AUDIT_PROMPT = """You are a Senior Executive Editor and Visual Quality Lead. Your mission is to evaluate if this SVG asset achieves the SOTA standard for professional documentation.

## 🔬 SOTA CORE QUALITY (40% Weight)
Your primary responsibility is to ensure the technical and logical foundation is flawless.
1. **Scientific & Logical Integrity (20%)**: Does the diagram correctly represent the concepts? Are factual relationships (hierarchy, flow) accurate?
2. **Typography & Readability (15%)**: **STRICT CHECK: Zero Overlap.** Are fonts legible, properly sized, and high-contrast?
3. **Engineering Standard (5%)**: Valid `viewBox`, efficient code, responsive design.

## 🎯 DYNAMIC INTENT ALIGNMENT (60% Weight)
Evaluate the SVG against these specific criteria generated for this task:
{dynamic_checkpoints}

## ⚖️ SCORING & HARD-FAILURE RULES
- **TOTAL SCORE**: (Core Quality Score out of 40) + (Intent Alignment Score out of 60).
- **HARD FAILURE**: If there is ANY **font overlap** or **scientific inaccuracy**, the `overall_score` MUST NOT exceed 60, regardless of how well it matches the intent.

## 📍 SPATIAL AUDIT (NEW)
For each issue identified, you MUST provide a bounding box `[ymin, xmin, ymax, xmax]` in normalized coordinates (0-1000) where:
- [0, 0] is top-left, [1000, 1000] is bottom-right.
- The box should tightly enclose the visual problem (e.g., overlapping text, broken path).

## Output (JSON only)
```json
{{
  "thought": "Expert reasoning on Core Quality and Intent Alignment.",
  "accuracy_score": 0, // Out of 20
  "typography_score": 0, // Out of 15
  "engineering_score": 0, // Out of 5
  "intent_score": 0, // Out of 60
  "overall_score": 0, // Sum of above, or capped at 60 if hard failure
  "result": "pass|fail|needs_revision",
  "issues": [
    {{
      "description": "Short, precise description of the issue.",
      "box": [ymin, xmin, ymax, xmax],
      "severity": "low|medium|high"
    }}
  ],
  "suggestions": []
}}
```
"""



def render_svg_to_png_base64(svg_code: str, width: int = 1200) -> Optional[str]:
    """使用 cairosvg 将 SVG 渲染为 PNG (base64)"""
    try:
        import cairosvg
        png_data = cairosvg.svg2png(
            bytestring=svg_code.encode("utf-8"),
            output_width=width
        )
        return base64.b64encode(png_data).decode("utf-8")
    except ImportError:
        print("    [Audit] cairosvg not installed, trying browser render...")
        return None
    except Exception as e:
        print(f"    [Audit] cairosvg render failed: {e}")
        return None


async def render_svg_with_playwright(svg_code: str, output_path: Path) -> bool:
    """使用 Playwright 渲染 SVG 为 PNG (高保真，支持中文字体)"""
    # SOTA 2.1: Proxy Armor for Playwright
    import os
    os.environ['no_proxy'] = '*'
    os.environ['NO_PROXY'] = '*'
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            html, body {{ margin: 0; padding: 0; background: white; }}
            body {{ display: flex; justify-content: center; align-items: flex-start; min-height: 100vh; }}
            svg {{ 
                display: block; 
                max-width: 100vw; 
                max-height: 100vh; 
                width: auto; 
                height: auto; 
                min-width: 200px; 
                min-height: 200px;
            }}
        </style>
    </head>
    <body>
        {svg_code}
    </body>
    </html>
    """
    temp_html = output_path.with_suffix(".html")
    temp_html.write_text(html_template, encoding="utf-8")
    
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            # Use a more reasonable viewport
            context = await browser.new_context(viewport={"width": 1000, "height": 800})
            page = await context.new_page()
            
            # SOTA: Hard timeout for navigation
            await page.goto(f"file://{temp_html.absolute()}", wait_until="networkidle", timeout=15000)
            await asyncio.sleep(0.5)
            
            # Take screenshot
            await page.screenshot(path=str(output_path), full_page=False)
            
            # Post-process: Resize and compress using PIL to reduce payload
            from PIL import Image
            with Image.open(output_path) as img:
                # SOTA Fix: Convert to RGB immediately to avoid Palette transparency warnings
                if img.mode != "RGB":
                    img = img.convert("RGB")
                
                # If width > 1024, resize
                if img.width > 1024:
                    ratio = 1024 / img.width
                    img = img.resize((1024, int(img.height * ratio)), Image.Resampling.LANCZOS)
                # Save back with compression
                img.save(output_path, format="JPEG", quality=80, optimize=True)
                
            return True
    except Exception as e:
        print(f"    [Audit] Playwright render failed: {e}")
        return False
    finally:
        if temp_html.exists():
            temp_html.unlink()


async def audit_svg_visual_async(
    client: GeminiClient,
    svg_code: str,
    intent_description: str,
    state: Optional[AgentState] = None,
    svg_path: Optional[Path] = None,
    blueprint: Optional[PreflightBlueprint] = None
) -> Optional[Dict[str, Any]]:
    """双路交叉 SVG 审计：代码分析 + 渲染图视觉分析 (优先使用浏览器渲染以支持中文字体)"""
    import tempfile
    
    # Step 0: Sanitize SVG
    svg_code = sanitize_svg(svg_code)
    
    # Step 1: 优先尝试浏览器渲染 (Playwright) 以解决 CJK 字体问题
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    
    png_b64 = None
    if await render_svg_with_playwright(svg_code, tmp_path):
        try:
            with open(tmp_path, "rb") as f:
                png_b64 = base64.b64encode(f.read()).decode("utf-8")
        finally:
            tmp_path.unlink(missing_ok=True)
    
    # Step 2: 如果浏览器渲染失败，尝试 cairosvg
    if not png_b64:
        print("    [Audit] Browser render failed, trying cairosvg...")
        png_b64 = render_svg_to_png_base64(svg_code)
    
    # Step 3: 如果渲染均失败，回退到纯代码审计
    if not png_b64:
        print("    [Audit] All render methods failed, falling back to code-only audit")
        return await audit_svg_async(client, svg_code, intent_description, state=state)
    
    # Step 4: 多模态审计请求
    if blueprint:
        checkpoints_text = "\n".join([
            f"{i+1}. {c.name} ({c.weight:.1f}%): {c.check}" 
            for i, c in enumerate(blueprint.dynamic_audit_checkpoints)
        ])
    else:
        checkpoints_text = f"1. Match core intent: {intent_description} (60.0%)"

    prompt = SVG_VISUAL_AUDIT_PROMPT.format(dynamic_checkpoints=checkpoints_text)
    parts = [
        {"text": prompt},
        {"text": f"## SVG Source Code\n```svg\n{svg_code}\n```"},
        {
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": png_b64
            }
        }
    ]
    
    try:
        # SOTA 2.1: Add explicit timeout for VLM audit to avoid hangs
        response = await asyncio.wait_for(
            client.generate_async(
                parts=parts,
                system_instruction="You are an SVG auditor. Analyze both code and rendered image. Output JSON only.",
                stream=True
            ),
            timeout=60.0
        )
        if not response.success:
            return None

        # Capture thoughts
        if state and response.thoughts:
            state.thoughts += f"\n[SVG Visual Audit] {response.thoughts}"

        payload = extract_json_payload(response.text)
        if not payload:
            return None
            
        data = json.loads(payload)
        
        # Merge model-generated thoughts if present in JSON
        if data.get("thought") and state:
            state.thoughts += f"\n[Audit Deep Dive] {data['thought']}"
            
        return data
    except Exception as e:
        print(f"    [Audit] Multi-modal audit failed: {e}")
        return None
