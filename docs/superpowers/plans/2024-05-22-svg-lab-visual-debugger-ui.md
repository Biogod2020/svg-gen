# SVG Lab Visual Debugger UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Google-style (Material Design 3) visual-first debugging UI for the SVG Optimization Lab, enabling developers to audit and repair SVG assets with full transparency into the AI's iterative process.

**Architecture:** A React frontend (Vite) communicating with the existing FastAPI backend. The backend is extended to provide full iteration history, including spatial audit data (bounding boxes). Frontend state is managed via Zustand for cross-component highlighting.

**Tech Stack:** React, TypeScript, Vite, Zustand, Material Design 3 (Vanilla CSS/CSS Modules), FastAPI.

---

### Task 1: Backend - Update Core Types & Audit Logic

**Files:**
- Modify: `src/core/types.py`
- Modify: `src/agents/asset_management/processors/audit.py`
- Create: `tests/backend/test_audit_parsing.py`

- [ ] **Step 1: Update `AssetEntry` and add `AuditIssue` model**
Add `box` (list of 4 floats: `[ymin, xmin, ymax, xmax]`) to `AuditIssue` and ensure it's part of the audit results.

- [ ] **Step 2: Implement `Malformed SVG Cleanup` utility**
Create a utility function to sanitize SVG code (e.g., removing leading/trailing text, fixing unclosed tags) before rendering/auditing.

- [ ] **Step 3: Update `SVG_VISUAL_AUDIT_PROMPT` in `audit.py`**
Modify the prompt to request JSON with bounding boxes: `[ymin, xmin, ymax, xmax]`.

- [ ] **Step 4: Update `audit_svg_visual_async` to parse new JSON structure**
Ensure it extracts bounding boxes and thoughts.

- [ ] **Step 5: Write unit tests for audit parsing**
Test with mock VLM responses containing bounding boxes and malformed SVG strings.
Run: `pytest tests/backend/test_audit_parsing.py`

- [ ] **Step 6: Commit**
`git add src/core/types.py src/agents/asset_management/processors/audit.py tests/backend/test_audit_parsing.py && git commit -m "feat(backend): add spatial audit and svg cleanup"`

### Task 2: Backend - Capture Iteration History in `SVGAgent`

**Files:**
- Modify: `src/agents/svg_generation/agent.py`
- Create: `tests/backend/test_agent_history.py`

- [ ] **Step 1: Modify `run_optimization_loop` to collect history**
Create a `history` list and append an entry for each iteration. Each entry MUST include: `svg_code`, `vqa_results` (with boxes), `thoughts`, and `png_b64` (rendered for that iteration).

- [ ] **Step 2: Update `SVGResult` and `optimize_svg_pipeline`**
Ensure the standard interface returns the full history.

- [ ] **Step 3: Write tests for iteration history**
Verify `history` length and content across mock generation/repair cycles.
Run: `pytest tests/backend/test_agent_history.py`

- [ ] **Step 4: Commit**
`git add src/agents/svg_generation/agent.py tests/backend/test_agent_history.py && git commit -m "feat(backend): capture full iteration history with images"`

### Task 3: Backend - Update API Response

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Update `/generate` endpoint response**
Ensure the FastAPI endpoint returns the `history` field.

- [ ] **Step 2: Test with `test_api.py`**
Verify the JSON response structure.
Run: `python test_api.py` (updated to check for history)

- [ ] **Step 3: Commit**
`git add main.py && git commit -m "feat(api): expose iteration history in /generate endpoint"`

### Task 4: Frontend - Scaffolding & Initial Setup

**Files:**
- Create: `frontend/` (using Vite)

- [ ] **Step 1: Scaffold Vite project**
Run: `npm create vite@latest frontend -- --template react-ts`

- [ ] **Step 2: Install dependencies**
Run: `npm install zustand lucide-react react-diff-viewer-continued @use-gesture/react @react-spring/web vitest @testing-library/react`

- [ ] **Step 3: Configure Proxy and Vitest**
Modify `vite.config.ts` for API proxy and test environment.

- [ ] **Step 4: Commit**
`git add frontend/ && git commit -m "chore(frontend): scaffold project and install dependencies"`

### Task 5: Frontend - State Management & Types

**Files:**
- Create: `frontend/src/store/useStore.ts`
- Create: `frontend/src/types.ts`
- Create: `frontend/src/store/__tests__/useStore.test.ts`

- [ ] **Step 1: Define TypeScript types**
Include `Iteration`, `AuditIssue`, and `AppState`.

- [ ] **Step 2: Implement Zustand store**
Manage `currentIterationIndex`, `history`, `highlightedIssueId`, `isDrawerOpen`, and `comparisonMode` (none|split|pixel-diff).

- [ ] **Step 3: Write store tests**
Verify state transitions for iteration switching and issue highlighting.
Run: `npx vitest run src/store/__tests__`

- [ ] **Step 4: Commit**
`git add frontend/src/store/ && git commit -m "feat(frontend): implement state management with tests"`

### Task 6: Frontend - Visual Stage (Rendering & Overlays)

**Files:**
- Create: `frontend/src/components/VisualStage/`
- Create: `frontend/src/components/VisualStage/VisualStage.tsx`
- Create: `frontend/src/components/VisualStage/HotspotOverlay.tsx`
- Create: `frontend/src/components/VisualStage/ComparisonLayer.tsx`

- [ ] **Step 1: Implement Base Renderer with Pan/Zoom**
Use `@use-gesture/react` for fluid interaction.

- [ ] **Step 2: Implement Hotspot Overlay**
Render pulsing dots using normalized `box` coordinates `[ymin, xmin, ymax, xmax]`.

- [ ] **Step 3: Implement Comparison Layer (Split Slider & Pixel Diff)**
Split Slider: Horizontal divider to compare two SVGs.
Pixel Diff: Overlay `png_b64` of two iterations using `mix-blend-mode: difference`.

- [ ] **Step 4: Commit**
`git add frontend/src/components/VisualStage/ && git commit -m "feat(frontend): build visual stage with overlays and comparison"`

### Task 7: Frontend - Filmstrip & Debug Drawer

**Files:**
- Create: `frontend/src/components/Filmstrip.tsx`
- Create: `frontend/src/components/DebugDrawer.tsx`
- Create: `frontend/src/components/__tests__/Filmstrip.test.tsx`

- [ ] **Step 1: Build `Filmstrip`**
Thumbnail list with iteration status icons. Add "Compare" toggle logic.

- [ ] **Step 2: Build `DebugDrawer`**
Split pane: Top for `AuditLogList` (with box mapping), bottom for `DiffViewer`.

- [ ] **Step 3: Implement Element Picker logic**
Clicking an SVG element in the Stage highlights the corresponding line in the Diff.

- [ ] **Step 4: Commit**
`git add frontend/src/components/ && git commit -m "feat(frontend): build filmstrip and debug drawer"`

### Task 8: Frontend - Final Integration & Styling

**Files:**
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/styles/md3.css`

- [ ] **Step 1: Apply Global MD3 Styles**
Implement Google colors, Product Sans typography, and 16px rounded corners.

- [ ] **Step 2: Connect `App.tsx` to API**
Fetch logic for `/generate` -> populate store.

- [ ] **Step 3: Final Polishing & E2E Test**
Add transitions. Verify full "Generate -> Audit -> Debug" flow.

- [ ] **Step 4: Commit**
`git add frontend/ && git commit -m "feat(frontend): final integration and md3 styling"`
