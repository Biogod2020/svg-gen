# SVG Optimization Lab (ASSA Evolution)

## 🎯 Purpose
This lab is a standalone sandbox dedicated to optimizing the **Generate-Audit-Repair** lifecycle of SVG visual assets. By decoupling these components from the main `long_md_writer` project, we can iterate on generation prompts, VLM audit dimensions, and Aider-style repair strategies without impacting the production environment.

## 📂 Origin
The logic and code in this directory are extracted and distilled from:
- **Project Root**: `/home/jiahao/code_workspace/long_md_writer`
- **Core Modules**:
    - `src/agents/svg_generation/`: SVG agent and processor.
    - `src/agents/asset_management/processors/audit.py`: VLM-based visual quality control.
    - `src/core/`: Infrastructure including GeminiClient, Patcher, and Persistence.
- **Reference Repository**: [long_md_writer](/home/jiahao/code_workspace/long_md_writer)

## 🏗️ Structure (SOTA 3.0 Evolution)
```text
lab_svg_optimization/
├── src/
│   ├── agents/
│   │   ├── svg_generation/     # [CORE] SVG Reflection Loop
│   │   │   ├── agent.py        # [SOTA 3.0] Pre-flight structure check -> Unified Audit -> Memory Repair
│   │   │   └── processor.py    # SOTA 3.0 design prompts & SEARCH/REPLACE logic
│   │   └── asset_management/   # [QC] Visual Quality Assurance
│   │       ├── processors/
│   │       │   └── audit.py    # [SOTA 3.0] Unified Auditor (0-100 score, Logic Red Lines)
│   │       └── utils.py        # Asset registration and HTML conversion
│   └── core/                   # [SUPPORT] Infrastructure & Utilities
│       ├── gemini_client.py    # Multi-provider Gemini interface with API version control
│       ├── patcher.py          # [SOTA 3.0] Aider-style RelativeIndenter & Tiered Matching
│       ├── json_utils.py       # [SOTA 3.0] Robust JSON parsing using json-repair
│       ├── types.py            # Global models (AuditResult, PreflightBlueprint)
│       └── path_utils.py       # CAS and path resolution
├── frontend/                   # [UI] Material Design 3 (Google Style) Interface
└── GEMINI.md                   # This file (Project Memory)
```

## 🛠️ Optimization Achievements (SOTA 3.0)
1. **Unified Auditor (audit.py)**: Combined Logic and Aesthetic checks into a single VLM call. Implemented 0-100 scoring with hard "Red Lines" for scientific accuracy and text readability.
2. **Robust Repair (patcher.py)**: Ported Aider's `RelativeIndenter` and tiered strategy matching. Matches code blocks regardless of indentation shifts or minor LLM typos.
3. **Robust JSON (json_utils.py)**: Switched to `json-repair` as the core parsing engine. Handles truncated JSON, control characters, and unescaped newlines reliably.
4. **Pre-flight Linting (agent.py)**: Added fast local `lxml` validation to catch XML syntax errors before expensive VLM audits.
5. **Memory-Augmented Repair**: Injected `Optimization History` into the repair prompt to prevent regressions across iterations.
6. **Premium UI (frontend)**: Complete Material 3 (Google style) redesign with multi-format high-res downloads (SVG, PNG, PDF).


## 🛡️ Stability & Bug Fixes
- **JSON Recovery**: Fixed `Invalid control character` errors by integrating `json-repair` and pre-cleansing non-printable ASCII.
- **Indentation Resilience**: Solved "Search block not found" failures by implementing relative indentation matching.
- **URL Pathing**: Corrected Gemini API versioning and proxy path duplication (`/antigravity/v1/`).
- **Robust Rendering**: Ensured final caption refinement always has image evidence by using a fallback Playwright-based robust renderer.
- **State Integrity**: Fixed SSE stream corruption where dictionary references were polluting agent history.
To run a standalone test, use the included `.env` and ensure dependencies are installed:
```bash
pip install -r requirements.txt
playwright install chromium
```
