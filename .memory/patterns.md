# PATTERNS

---
id: P-20260323-SESSION
category: Logic
confidence: 8
status: Active
hit_count: 1
---

# Session-First Context Synchronization
**Rationale**: When an agent starts a task without explicitly searching for the current session's metadata (e.g., Session ID) within the `.memory/` or `conductor/` directories, it often relies on "code archaeology" which lacks the intent and progress state of the current session. This leads to redundant work or attempts to access unauthorized global session paths (e.g., `~/.gemini/sessions`).

**Rule**: Before initiating any ASSA-related diagnostic or implementation tasks, you MUST perform a `grep_search` for the current Session ID within the workspace (specifically targeting `.memory/` and `conductor/`) to locate the physical conversation records or related evolution signals. This ensures the agent is synchronized with the latest human intent and "evolutionary progress" documented in the ledger.
