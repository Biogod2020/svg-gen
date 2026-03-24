# Streaming SVG Optimization & Enhanced Visualization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement real-time SVG generation streaming via SSE and enhance the frontend visual stage for large-scale SVG viewing.

**Architecture:** 
- Backend: Refactor `SVGAgent` to a generator and add a FastAPI `StreamingResponse` endpoint.
- Frontend: Update Zustand store to process SSE streams and enhance `VisualStage` with automatic scaling and zoom controls.

**Tech Stack:** FastAPI (SSE), React, Zustand, Lucide Icons, Vitest, Pytest.

---

### Task 1: Backend - Refactor SVGAgent to Async Generator

**Files:**
- Modify: `src/agents/svg_generation/agent.py`
- Test: `tests/agents/svg_generation/test_agent_generator.py`

- [ ] **Step 1: Write failing test for generator**
- [ ] **Step 2: Verify test fails**
- [ ] **Step 3: Refactor run_optimization_loop to yield iterations**
- [ ] **Step 4: Verify test passes**
- [ ] **Step 5: Commit**

### Task 2: Backend - Streaming API Endpoint

**Files:**
- Modify: `main.py`
- Test: `tests/backend/test_streaming_api.py`

- [ ] **Step 1: Write failing test for /generate-stream**
- [ ] **Step 2: Verify test fails**
- [ ] **Step 3: Implement /generate-stream using StreamingResponse**
- [ ] **Step 4: Verify test passes**
- [ ] **Step 5: Commit**

### Task 3: Frontend - Streaming Store Logic

**Files:**
- Modify: `frontend/src/store/useStore.ts`
- Modify: `frontend/src/types.ts`
- Test: `frontend/src/store/__tests__/useStore.streaming.test.ts`

- [ ] **Step 1: Update Iteration type if necessary**
- [ ] **Step 2: Write failing test for streaming data into history**
- [ ] **Step 3: Implement generateStream action in Zustand**
- [ ] **Step 4: Verify test passes**
- [ ] **Step 5: Commit**

### Task 4: Frontend - Visual Stage Scaling & Fit-to-Screen

**Files:**
- Modify: `frontend/src/components/VisualStage/VisualStage.tsx`
- Modify: `frontend/src/components/VisualStage/VisualStage.css`

- [ ] **Step 1: Remove max-height/max-width constraints in CSS**
- [ ] **Step 2: Implement fitToScreen calculation logic**
- [ ] **Step 3: Add "Fit to Screen" button to controls**
- [ ] **Step 4: Manually verify large SVG display**
- [ ] **Step 5: Commit**

### Task 5: Integration & UI Cleanup

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `run.sh`

- [ ] **Step 1: Connect App component to the new streaming action**
- [ ] **Step 2: Update run.sh if needed (e.g., adding host flags)**
- [ ] **Step 3: Perform end-to-end verification**
- [ ] **Step 4: Commit**
