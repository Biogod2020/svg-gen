# AGENTS.md - SVG Optimization Lab (SOTA 3.0)

This guide is for agentic coding agents operating in this repository. Adhere to these standards to maintain consistency and quality.

## 🚀 Development Commands

### Backend (Python 3.12+)
- **Start API Server:** `uvicorn main:app --reload --port 8000`
- **Run All Tests:** `pytest`
- **Run Core Robustness Tests:** `pytest tests/core/`
- **Run Specific Test:** `pytest tests/core/test_patcher_robustness.py::test_apply_smart_patch_fuzzy`
- **Install Dependencies:** `pip install -r requirements.txt`

### Frontend (React + TypeScript + Vite)
- **Start Dev Server:** `cd frontend && npm run dev`
- **Run All Tests:** `cd frontend && npm run test`
- **Lint Code:** `cd frontend && npm run lint`

---

## 🎨 Code Style Guidelines

### General Principles
- **Robustness First:** Always use `src/core/json_utils.py` for parsing LLM JSON. Never use standard `json.loads` directly on raw LLM strings.
- **Precision Patching:** When applying code changes, use `src/core/patcher.py`. It uses Aider-style matching that handles indentation shifts.
- **Readability:** Maintain clean, documented code. Use `Absolute Imports` (e.g., `from src.core...`) for clarity across sub-agents.

### Python Standards
- **Parsing:** Use `parse_json_dict_robust` from `src.core.json_utils`.
- **Async:** Use `asyncio` for all I/O and LLM calls. 
- **Types:** Strictly use Pydantic `BaseModel` for data structures defined in `src/core/types.py`.

---

## 🛠️ Project Architecture (SOTA 3.0)

### SVG Optimization Loop
The core logic resides in `src/agents/svg_generation/agent.py`. The SOTA 3.0 loop is:
1. **Refinement:** Prompt optimization into a `PreflightBlueprint`.
2. **Generation:** Initial SVG creation with SOTA design principles (rounded corners, soft shadows).
3. **Pre-flight Lint:** Fast local XML/viewBox check using `lxml` to catch structural errors instantly.
4. **Unified Audit:** Single VLM call using `UNIFIED_SOTA_AUDIT_PROMPT` (0-100 score, Logic Red Lines).
5. **Memory-Augmented Repair:** Surgical fixes using `SEARCH/REPLACE` blocks, aware of previous iteration scores and issues.

### Robustness Components
- **`RelativeIndenter`**: Ported from Aider. Matches code based on relative indentation increments, ignoring absolute whitespace shifts.
- **`json-repair`**: Integrated via `json_utils`. Automatically fixes malformed JSON, truncated responses, and unescaped control characters.
- **`get_svg_render_base64_async`**: Robust dual-mode renderer (Playwright -> CairoSVG) to ensure VLM always has visual evidence.

### Core Data Models
- **`AuditResult`**: Standardized 0-100 scoring.
    - **Pass Threshold**: 80/100.
    - **Logic Red Line**: Scientific error caps score at 40 (Force Repair).
    - **Readability Red Line**: Text overlap caps score at 70 (Force Repair).

---

## 📝 Documentation & Maintenance
- **Project Memory**: Update `GEMINI.md` with major architectural milestones or bug-fix patterns.
- **Dependencies**: Keep `requirements.txt` synced, especially for SOTA tools like `json-repair` and `diff-match-patch`.
- **UI Consistency**: Follow **Material Design 3** (Google Style) for all frontend components.
