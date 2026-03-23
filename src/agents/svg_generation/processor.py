"""
SVG Processor

Handles SVG generation and extraction.
"""

import re
from typing import Optional, List, Dict, Any, Union

from ...core.gemini_client import GeminiClient
from ...core.types import AgentState
from ...core.patcher import apply_smart_patch, parse_aider_blocks

SVG_GENERATION_PROMPT = """You are a Senior Information Architect and Technical Illustrator. Your goal is to create State-of-the-Art (SOTA) vector graphics that translate complex concepts into intuitive visual metaphors.

## 🎯 YOUR TASK
Create a professional SVG illustration based on the following specific requirements and chapter context:

{description}

{style_hints}

## 🎨 DESIGN PHILOSOPHY (The SOTA Standard)
1. **Visual Hierarchy**: Use line weight, color saturation, and scale to guide the reader's eye. The most critical information must be immediately prominent.
2. **Cognitive Load Management**: Avoid clutter. Use negative space (whitespace) as a functional element to separate concepts.
3. **Professional Finish**: Aim for a modern, precise, and high-quality aesthetic (e.g., subtle gradients, rounded geometric shapes, balanced composition).
4. **Contextual Awareness**: Ensure the diagram feels like an organic part of the overall document.

## 🛠️ TECHNICAL EXECUTION
- Generate strictly valid, self-contained SVG code.
- Use `viewBox` for fluid responsiveness. Set `width="100%"` and `height="auto"`.
- **Avoid Overlapping**: Prevent labels or lines from crossing each other messily.
- **Labeling Strategy**: Place labels where they are most readable. Use leader lines (arrows/paths) to pull text away from high-density areas if needed. 
- **Font Support**: Use system-standard font stacks.

Your output should not just be a 'drawing', but a high-fidelity 'Knowledge Interface'.
"""

SVG_CAPTION_REFINEMENT_PROMPT = """You are a Senior Technical Editor. Your task is to write a precise, factual, and professional caption for the provided SVG illustration.

### Instructions:
1. **Analyze the Image**: Look at what is ACTUALLY rendered in the image (labels, arrows, colors, structures).
2. **Consult Context**: Read the [ARTICLE CONTEXT] to understand the intended narrative and terminology.
3. **Synthesize**: Write a caption that:
   - Describes the core mechanism or concept shown.
   - Specifically mentions key labels visible in the diagram to anchor the text to the visual.
   - Is concise (1-2 sentences) but high-value.
   - Avoids "Here is a diagram showing..." or "This image illustrates...". Start directly with the factual description.
   - **LANGUAGE ALIGNMENT (CRITICAL)**: Always write the caption in the **SAME LANGUAGE** as the [ARTICLE CONTEXT] (e.g., Chinese if the section is Chinese).

### Input Data:
- **Original Directive**: {original_directive}
- **Article Context**: {article_context}

### Final Caption Output:
(Output only the caption text, no JSON or quotes)
"""


def extract_svg(text: str) -> Optional[str]:
    """从文本中提取 SVG 代码"""
    # 尝试匹配 ```svg ... ``` 块
    match = re.search(r'```svg\s*([\s\S]*?)```', text)
    if match:
        return match.group(1).strip()

    # 尝试直接匹配 <svg ...> ... </svg>
    match = re.search(r'<svg[^>]*>[\s\S]*?</svg>', text, re.IGNORECASE)
    if match:
        return match.group(0)

    return None


async def generate_svg_async(
    client: GeminiClient,
    description: str,
    state: Optional[AgentState] = None,
    style_hints: str = ""
) -> Optional[str]:
    """异步生成 SVG 图形"""
    hints_section = f"## Additional Style\n{style_hints}" if style_hints else ""
    prompt = SVG_GENERATION_PROMPT.format(
        description=description,
        style_hints=hints_section
    )

    try:
        response = await client.generate_async(
            prompt=prompt,
            system_instruction="You are a professional SVG designer. Create accurate, readable, and aesthetically pleasing vector graphics.",
            temperature=0.5,
            stream=True
        )

        if not response.success:
            print(f"[SVG Processor] API error: {response.error}")
            return None

        # Capture thoughts
        if state and response.thoughts:
            state.thoughts += f"\n[SVG Generation] {response.thoughts}"

        return extract_svg(response.text)

    except Exception as e:
        print(f"[SVG Processor] Generation failed: {e}")
        return None


def generate_svg(
    client: GeminiClient,
    description: str,
    style_hints: str = ""
) -> Optional[str]:
    """同步生成 SVG 图形"""
    hints_section = f"## Additional Style\n{style_hints}" if style_hints else ""
    prompt = SVG_GENERATION_PROMPT.format(
        description=description,
        style_hints=hints_section
    )

    try:
        response = client.generate(
            prompt=prompt,
            system_instruction="You are a professional SVG designer. Create accurate, readable, and aesthetically pleasing vector graphics."
        )
        return extract_svg(response.text)

    except Exception as e:
        print(f"[SVG Processor] Generation failed: {e}")
        return None


# ============================================================================
# SVG Repair (Aider-Style SEARCH/REPLACE with Visual Context)
# ============================================================================

SVG_REPAIR_PROMPT = """You are a senior SVG technical specialist. Your task is to fix issues in an SVG file using *SEARCH/REPLACE blocks*.

### Critical Rules for SEARCH/REPLACE:
1. **Verbatim Search**: The `SEARCH` section must EXACTLY match the existing code, including all whitespace and punctuation.
2. **Minimal Changes**: Only modify what is necessary to fix the reported issues.
3. **No JSON**: Do NOT return JSON. Output only the blocks.
4. **No Escaping**: Output raw SVG code. Do NOT escape quotes or backslashes.

### Format:
```markdown
<<<<<<< SEARCH
[Existing code to be fixed]
=======
[New code to replace it with]
>>>>>>> REPLACE
```

### Input Data:
1. **Original Intent**: {original_intent}
2. **Audit Feedback**: 
   - Issues: {issues}
   - Suggestions: {suggestions}
3. **Previous Attempt Feedback**: {feedback}

## CURRENT SVG CODE
```svg
{failed_svg_code}
```
"""

async def repair_svg_async(
    client: GeminiClient,
    original_intent: str,
    failed_svg_code: str,
    issues: list[str],
    suggestions: list[str],
    state: Optional[AgentState] = None,
    rendered_image_b64: Optional[str] = None,
    max_retries: int = 2
) -> Optional[str]:
    """
    Repair an SVG using Aider-style blocks.
    Implements an escalation loop with rich feedback.
    """
    issues_text = "\n".join(f"- {issue}" for issue in issues) if issues else "- None"
    suggestions_text = "\n".join(f"- {s}" for s in suggestions) if suggestions else "- None"
    
    current_svg_code = failed_svg_code
    last_feedback = "This is the first repair attempt."

    for attempt in range(max_retries + 1):
        prompt = SVG_REPAIR_PROMPT.format(
            original_intent=original_intent,
            failed_svg_code=current_svg_code,
            issues=issues_text,
            suggestions=suggestions_text,
            feedback=last_feedback
        )
        
        # Multi-modal parts (study the image in every retry)
        parts = []
        if rendered_image_b64:
            parts.append({"text": "## Visual Reference\nStudy this current rendering to locate issues:"})
            parts.append({"inline_data": {"mime_type": "image/jpeg", "data": rendered_image_b64}})
        parts.append({"text": prompt})

        try:
            print(f"    [SVG Repair] 🛠️ Attempt {attempt + 1}/{max_retries + 1}...")
            response = await client.generate_async(
                parts=parts,
                system_instruction="You are a SOTA SVG Patching Agent. Fix issues using Aider-style SEARCH/REPLACE blocks.",
                temperature=0.0,
                stream=True
            )

            if not response.success:
                last_feedback = f"API Error: {response.error}"
                continue

            if state and response.thoughts:
                state.thoughts += f"\n[SVG Repair Attempt {attempt+1}] {response.thoughts}"

            # Extract Aider blocks using global standardized parser
            blocks = parse_aider_blocks(response.text)
            if not blocks:
                # SOTA: If no blocks but we see the markers, it might be malformed
                if "<<<<<<< SEARCH" in response.text:
                    last_feedback = "Your response contained malformed SEARCH/REPLACE blocks. Ensure you follow the exact format."
                else:
                    last_feedback = "No SEARCH/REPLACE blocks found in your response. Please provide a fix."
                continue

            # Apply blocks sequentially
            applied_content = current_svg_code
            any_success = False
            
            for b in blocks:
                new_content, success = apply_smart_patch(applied_content, b["search"], b["replace"])
                if success:
                    applied_content = new_content
                    any_success = True
                else:
                    print(f"    [SVG Repair] ❌ Block match failed: {b['search'][:30]}...")
            
            if any_success:
                print(f"    [SVG Repair] ✅ Patch applied (Attempt {attempt+1})")
                return applied_content
            else:
                last_feedback = "All your SEARCH/REPLACE blocks failed to match the current content. Please double-check for verbatim accuracy."

        except Exception as e:
            print(f"    [SVG Repair] Exception: {e}")
            last_feedback = f"System Exception: {str(e)}"
            
    return None


async def refine_svg_caption_async(
    client: GeminiClient,
    original_directive: str,
    article_context: str,
    rendered_image_b64: str,
    state: Optional[AgentState] = None
) -> str:
    """
    Refine the SVG description (caption) based on the actual rendered image.
    Ensures high alignment between text and visual evidence.
    """
    prompt = SVG_CAPTION_REFINEMENT_PROMPT.format(
        original_directive=original_directive,
        article_context=article_context
    )
    
    parts = [
        {"text": "Analyze this final rendered SVG illustration:"},
        {
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": rendered_image_b64
            }
        },
        {"text": prompt}
    ]
    
    try:
        response = await client.generate_async(
            parts=parts,
            system_instruction="You are a Technical Copywriter. Write factual captions based on visual evidence.",
            temperature=0.0
        )
        
        if response.success:
            return response.text.strip()
        return original_directive # Fallback to original
    except Exception as e:
        print(f"    [SVGAgent] Caption refinement failed: {e}")
        return original_directive
