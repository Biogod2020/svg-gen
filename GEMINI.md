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

## 🏗️ Structure
```text
lab_svg_optimization/
├── src/
│   ├── agents/
│   │   ├── svg_generation/     # [CORE] SVG Reflection Loop
│   │   │   ├── agent.py        # Orchestrates Generate -> Audit -> Repair (up to 5 attempts)
│   │   │   └── processor.py    # Generative prompts and SEARCH/REPLACE repair logic
│   │   └── asset_management/   # [QC] Visual Quality Assurance
│   │       ├── processors/
│   │       │   └── audit.py    # VLM-based dual-mode audit (Source Code + PNG Rendering)
│   │       └── utils.py        # Asset registration and HTML conversion
│   └── core/                   # [SUPPORT] Infrastructure & Utilities
│       ├── gemini_client.py    # Unified interface for LLM/VLM calls
│       ├── patcher.py          # Aider-style code patching engine
│       ├── persistence.py      # Asset registry state management
│       ├── types.py            # Global type definitions (AgentState, AssetVQAStatus)
│       └── validators.py       # Data integrity checks
├── .env                        # API keys and environment secrets
├── requirements.txt            # Lab dependencies (Playwright, CairoSVG, etc.)
└── GEMINI.md                   # This file
```

## 🛠️ Optimization Targets
1. **SVG Prompt (processor.py)**: Refine `SVG_GENERATION_PROMPT` to enforce better responsive design and color palettes.
2. **Audit Dimension (audit.py)**: Adjust `SVG_VISUAL_AUDIT_PROMPT` to improve the detection of overlapping text or illogical layouts.
3. **Repair Precision (processor.py)**: Optimize `SVG_REPAIR_PROMPT` to provide more surgical feedback to the repair agent.

## 🚀 Usage
To run a standalone test, use the included `.env` and ensure dependencies are installed:
```bash
pip install -r requirements.txt
playwright install chromium
```
