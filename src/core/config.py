import os

# ============================================================================
# API & Provider Configuration
# ============================================================================

# Default proxy URL (gcli2api defaults to 7861)
DEFAULT_BASE_URL = os.getenv("API_URL", "http://localhost:7861")

# Default authentication password/token
DEFAULT_AUTH_PASSWORD = os.getenv("GEMINI_AUTH_PASSWORD", "pwd")

# SOTA 2.1: Default providers for polling
DEFAULT_PROVIDERS = ["gemini-antigravity", "gemini-cli-oauth"]


# ============================================================================
# Model Selection (Centralized)
# ============================================================================

# The primary model used for SVG Generation and Audit
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-3-flash-preview")

# Default thinking level for Gemini 3 series models
# Options: "HIGH", "MEDIUM", "LOW", "MINIMAL"
DEFAULT_THINKING_LEVEL = "HIGH"


# ============================================================================
# Workspace & System Settings
# ============================================================================

WORKSPACE_BASE = os.getenv("WORKSPACE_BASE", "./workspace")
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"
HEADLESS_MODE = os.getenv("HEADLESS_MODE", "true").lower() == "true"
