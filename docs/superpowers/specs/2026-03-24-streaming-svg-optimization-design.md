# Design Spec: Streaming SVG Optimization & Enhanced Visualization

## 1. Problem Statement
Current SVG Lab UI has two main limitations:
1.  **Delayed Feedback**: Users must wait for the entire Generate-Audit-Repair loop (up to 5 iterations) to finish before seeing any visual output.
2.  **Visualization Constraints**: Large or complex SVGs are constrained by CSS `max-height`/`max-width`, making detail inspection difficult even with zoom.

## 2. Proposed Solution

### 2.1 Backend: Server-Sent Events (SSE)
- Refactor `SVGAgent.run_optimization_loop` to be an asynchronous generator (`yield` each iteration).
- Add a new FastAPI endpoint `/generate-stream` using `StreamingResponse`.
- Data chunks will follow the SSE format: `data: <JSON_ITERATION_OBJECT>\n\n`.
- Yield iterations immediately after initial generation and after each successful repair step.

### 2.2 Frontend: Streaming Store & Dynamic History
- Update Zustand `useStore` to handle `ReadableStream` from the `/generate-stream` fetch call.
- Use `TextDecoder` and a parser for the SSE stream format.
- Append incoming iterations to the `history` array in real-time.
- Automatically switch `currentIterationIndex` to the latest iteration as it arrives.

### 2.3 Frontend: Enhanced Visual Stage
- Remove rigid CSS constraints on the SVG content (remove `max-height: 80vh`).
- Implement a `fitToScreen` utility that calculates the initial `scale` based on the SVG's `viewBox` (if present) or bounding client rect and the container's dimensions.
- Add a dedicated "Fit to Screen" button in the `VisualStage` controls.
- Optimize Pan/Zoom performance for high-resolution SVGs.

## 3. Data Flow
1.  User submits prompt.
2.  Frontend calls `/generate-stream`.
3.  Backend starts `SVGAgent`.
4.  Backend yields `Iteration 0` (Initial).
5.  Frontend receives `Iteration 0`, updates UI, shows SVG.
6.  Backend performs Audit.
7.  Backend yields `Iteration 1` (Repair 1).
8.  Frontend receives `Iteration 1`, switches view to it.
9.  Loop continues until Pass or Max Retries.
10. Backend sends `[DONE]` marker or closes connection.

## 4. Testing Strategy (TDD)
- **Backend**: `pytest` for the streaming generator and the FastAPI endpoint (using `httpx.AsyncClient` with stream support).
- **Frontend**: `vitest` for the store's stream processing logic and `VisualStage` scaling calculations.
