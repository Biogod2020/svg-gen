# AGENTS.md - SVG Optimization Lab

This guide is for agentic coding agents operating in this repository. Adhere to these standards to maintain consistency and quality.

## 🚀 Development Commands

### Backend (Python 3.12+)
- **Start API Server:** `uvicorn main:app --reload --port 8000`
- **Run All Tests:** `pytest`
- **Run Single Test File:** `pytest tests/agents/svg_generation/test_refinement.py`
- **Run Specific Test:** `pytest tests/agents/svg_generation/test_refinement.py::test_refine_request_async`
- **Install Dependencies:** `pip install -r requirements.txt`
- **Check Types:** `mypy src` (if configured)

### Frontend (React + TypeScript + Vite)
- **Start Dev Server:** `cd frontend && npm run dev`
- **Run All Tests:** `cd frontend && npm run test`
- **Run Single Test File:** `cd frontend && npm run test -- App.test.tsx`
- **Lint Code:** `cd frontend && npm run lint`
- **Build Project:** `cd frontend && npm run build`

---

## 🎨 Code Style Guidelines

### General Principles
- **Readability:** Code must be easy to read. Avoid "clever" one-liners.
- **Consistency:** Match the surrounding code's style, naming, and structure.
- **Simplicity:** Prefer straightforward solutions over complex abstractions.
- **Documentation:** Document *why* something is done, especially in complex agent logic.

### Python Standards (Google Style Guide)
- **Imports:** Use `import x` for packages/modules. Use `from x import y` for submodules. Group imports: stdlib, third-party, local.
- **Naming:** `snake_case` for functions/variables, `PascalCase` for classes, `ALL_CAPS` for constants.
- **Types:** Use type annotations for all function signatures and public APIs.
- **Docstrings:** Use `"""triple double quotes"""` with `Args:`, `Returns:`, and `Raises:` sections.
- **Error Handling:** Use specific built-in exceptions. Avoid bare `except:`.
- **Async:** Use `asyncio` for I/O bound tasks. Prefer `Path` from `pathlib` for file operations.
- **Pydantic:** Use Pydantic `BaseModel` for data structures and API schemas.

### TypeScript & React Standards
- **Components:** Use functional components with `React.FC`.
- **State Management:** Use `useState` for local state and `zustand` for global store (`frontend/src/store/useStore.ts`).
- **Types:** Define interfaces for props and data structures in `types.ts` or near usage.
- **Imports:** Absolute imports are not configured; use relative paths.
- **Styling:** Use CSS files (e.g., `ComponentName.css`) imported into the component.
- **Testing:** Use Vitest and React Testing Library for frontend tests.

---

## 🛠️ Project Architecture & Rules

### SVG Optimization Loop
The core logic resides in `src/agents/svg_generation/agent.py`. It follows a **Generate -> Audit -> Repair** loop:
1. **Refinement:** `RefinementProcessor` optimizes the user prompt into a `PreflightBlueprint`.
2. **Generation:** `generate_svg_async` creates the initial SVG based on the blueprint.
3. **Audit:** `audit_svg_visual_async` uses a VLM to check both code and rendered PNG.
4. **Repair:** `repair_svg_async` applies surgical fixes based on audit feedback (max 5 attempts).

### Core Data Models (`src/core/types.py`)
- **`AgentState`:** Tracks the current job, workspace path, and telemetry.
- **`AssetEntry`:** Records metadata for a generated asset, including VQA status and audit results.
- **`AuditResult`:** Contains the score, issues, and suggestions from a VLM audit.
- **`UniversalAssetRegistry` (UAR):** Manages asset persistence and Content-Addressable Storage (CAS).

### Workspace Management
- All generated assets and logs must be stored in the `workspace/` directory, organized by `job_id`.
- Use `AgentState.get_uar()` to access the asset registry for the current job.
- Assets are stored atomically using SHA256 hashes in `workspace/<job_id>/assets/cas/`.

### VLM Audit Integration
- Audits are cross-modal. Always provide both the SVG source code and a base64-encoded PNG rendering to the VLM.
- Use `render_svg_to_png_base64` from `src/agents/asset_management/processors/audit.py` for rendering.
- Normalize audit weights to a total of 60.0 as defined in `PreflightBlueprint`.

### API Integration
- The backend is a FastAPI application (`main.py`).
- Use `StreamingResponse` with Server-Sent Events (SSE) for real-time generation feedback.
- Ensure all iteration data sent over SSE is JSON serializable (convert Pydantic models using `.model_dump()`).

---

## 📝 Documentation & Maintenance
- Update `GEMINI.md` if the high-level architecture or optimization targets change.
- Ensure `requirements.txt` is kept up-to-date with any new backend dependencies.
- Follow the `TODO(username): Fix this.` format for pending tasks.
