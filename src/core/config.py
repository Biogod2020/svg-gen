import os

# ============================================================================
# API & Provider Configuration (SOTA 3.0 Cloud Migration)
# ============================================================================

# --- AI Studio (Direct) ---
AISTUDIO_BASE_URL = "https://generativelanguage.googleapis.com"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Vertex AI (Google Cloud) ---
VERTEX_BASE_TEMPLATE = "https://{location}-aiplatform.googleapis.com/v1/projects/{project}/locations/{location}/publishers/google/models/{model}:{action}"
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# --- Legacy Proxy Support (Archived) ---
ENABLE_LEGACY_PROXY = os.getenv("ENABLE_LEGACY_PROXY", "false").lower() == "true"
LEGACY_GEMINI_API_URL = os.getenv(
    "LEGACY_GEMINI_API_URL", os.getenv("API_URL", "http://localhost:7861/antigravity")
)
LEGACY_GEMINI_AUTH_TOKEN = os.getenv(
    "LEGACY_GEMINI_AUTH_TOKEN", os.getenv("GEMINI_AUTH_PASSWORD", "pwd")
)

# Backward compatibility aliases
DEFAULT_BASE_URL = LEGACY_GEMINI_API_URL
DEFAULT_AUTH_PASSWORD = LEGACY_GEMINI_AUTH_TOKEN
VERTEX_API_KEY = os.getenv("VERTEX_API_KEY", "")

# Default API Version
DEFAULT_API_VERSION = os.getenv("GEMINI_API_VERSION", "v1")

# Default providers for polling (Ordered by preference)
_providers_env = os.getenv("DEFAULT_PROVIDERS", "aistudio,vertex,legacy-proxy")
DEFAULT_PROVIDERS = [p.strip() for p in _providers_env.split(",") if p.strip()]


# ============================================================================
# Model Selection (Centralized)
# ============================================================================

# The primary model used for SVG Generation and Audit
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-3-flash")

# Default thinking level for Gemini 3 series models
# Options: "HIGH", "MEDIUM", "LOW", "MINIMAL"
DEFAULT_THINKING_LEVEL = os.getenv("DEFAULT_THINKING_LEVEL", "HIGH")


# ============================================================================
# Workspace & System Settings
# ============================================================================

WORKSPACE_BASE = os.getenv("WORKSPACE_BASE", "./workspace")
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"
HEADLESS_MODE = os.getenv("HEADLESS_MODE", "true").lower() == "true"
