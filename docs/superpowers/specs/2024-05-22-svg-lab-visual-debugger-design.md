# Design Spec: SVG Optimization Lab Visual Debugger

**Status:** Draft (Approved by User)
**Author:** Gemini CLI
**Date:** 2024-05-22
**Topic:** Visual-First Debugging UI for SVG Generation Agent

## 1. Introduction
The SVG Optimization Lab is an AI-powered tool that generates, audits, and repairs SVG assets using a Vision Language Model (VLM). This document outlines the design for a modern, Google-styled (Material Design 3) web interface focused on **debugging** the agent's optimization loop. The UI prioritizes visual feedback while providing deep-dive logs and code diffs.

## 2. User Persona
*   **Primary User:** Developers and AI Researchers.
*   **Goal:** Understand why an SVG failed an audit, how the agent interpreted the visual issues, and what specific code changes were made during the repair cycle.

## 3. Core Requirements
*   **Visual-First:** The generated SVG must be the focal point of the UI.
*   **Debugging Transparency:** Real-time access to the "Generate-Audit-Repair" loop (up to 5 iterations).
*   **Multi-way Sync:** Clicking an image hotspot, a log entry, or a code line should highlight the corresponding data in other views.
*   **Modern Aesthetic:** Google/Material Design 3 aesthetic (clean, white/light-gray, Product Sans, rounded corners).

## 4. UI/UX Design

### 4.1 Layout (The Stage & Drawer)
The interface follows a "Google Cloud Console" pattern:
*   **Global Header:** Job ID, Status indicator (Optimizing/Success/Fail), and "Regenerate" controls.
*   **Central Visual Stage (70%):** A large, light-gray area for high-resolution SVG preview. Includes an "Audit Overlay" that marks visual issues with pulsing hotspots. **New: Supports "Pixel Diff" overlay mode to show rasterized changes between iterations.**
*   **Bottom Filmstrip:** A horizontal list of thumbnails representing each iteration (Initial -> Iteration 1... -> Final). Status icons (Pass/Fail) are shown on each thumbnail.
*   **Right Debug Drawer (30%):** A collapsible panel containing:
    *   **Audit Logs:** A list of agent thoughts and VQA findings. **New: Logs now include bounding box coordinates for mapping to the Stage.**
    *   **Code Diff:** A side-by-side or unified diff viewer showing changes from the previous version.

### 4.2 Key Interactions
1.  **Iteration Switching:** Clicking a thumbnail in the Filmstrip updates the Stage, Logs, and Diff views to that specific step.
2.  **Visual Hotspots:** Hovering over a pulsing red dot on the SVG highlights the specific "Issue" in the Log List.
3.  **Log-to-Code Mapping:** Clicking a log entry (e.g., "Line thickness is inconsistent") scrolls the Diff view to the relevant lines of SVG code.
4.  **Comparison Mode:** Holding `Shift` while selecting two thumbnails triggers a "Split Slider" mode in the Stage to compare two versions visually.
5.  **Element Picker:** Clicking an element in the Stage highlights its corresponding code in the Diff viewer.

## 5. Technical Architecture

### 5.1 Frontend Stack
*   **Framework:** React (TypeScript)
*   **State Management:** Zustand (for centralized management of active iteration, highlighted elements, and audit hotspots).
*   **Styling:** Vanilla CSS with CSS Modules (following MD3 variables).
*   **Components:** 
    *   `VisualStage`: Custom SVG renderer with pan/zoom, overlay logic, and pixel-diff capabilities.
    *   `Filmstrip`: Horizontal scroll container with thumbnail cards.
    *   `DebugDrawer`: Split-pane container for Logs and Diff.
    *   `DiffViewer`: Integration with `react-diff-viewer-continued` or similar, styled for Google aesthetic.

### 5.2 Backend Integration (Required Changes)
The current `main.py` only returns the final SVG result. To support debugging, the API must be extended:
*   **Spatial Auditing:** Update the VLM prompt in `src/agents/asset_management/processors/audit.py` to return JSON with `bounding_box: [ymin, xmin, ymax, xmax]` for each identified issue.
*   **New Endpoint/Response:** Include `history` in the response:
    ```json
    {
      "iteration": 0,
      "svg_code": "...",
      "vqa_results": { 
        "status": "fail", 
        "issues": [
          { "description": "...", "box": [0.1, 0.2, 0.3, 0.4], "severity": "high" }
        ], 
        "score": 45 
      },
      "agent_thoughts": "..."
    }
    ```
*   **Persistence:** Ensure intermediate files in the `workspace/` are tracked and accessible.
*   **Error Recovery:** Implement a "Malformed SVG Cleanup" utility to handle cases where the LLM returns invalid SVG syntax, ensuring the UI can still render a partial or fixed version for debugging.

## 6. Implementation Strategy
1.  **Scaffolding:** Initialize React + Vite project.
2.  **API Refactor:** Modify `src/agents/svg_generation/agent.py` and `main.py` to collect and return the full audit trail.
3.  **Core Layout:** Build the Stage, Filmstrip, and Drawer layout.
4.  **Interactive Logic:** Implement the state management for iteration switching and cross-component highlighting.
5.  **Polishing:** Apply Material Design 3 styling and animations.

## 7. Success Criteria
*   Users can identify the cause of an audit failure within 10 seconds of viewing the UI.
*   The UI remains performant even with large SVG files or multiple iterations.
*   The aesthetic matches the "Google Style" requested by the user.
