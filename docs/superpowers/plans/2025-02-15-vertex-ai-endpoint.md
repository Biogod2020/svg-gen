# Vertex AI Endpoint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate a new direct endpoint for Vertex AI into the existing `GeminiClient` rotation logic, supporting the `gemini-2.5-flash-lite` model using the simplified `aiplatform.googleapis.com` URL.

**Architecture:** Integrated Provider Logic in `GeminiClient`. The client will branch based on the `vertex` provider string to build the specific Vertex AI URL and handle its authentication.

**Tech Stack:** Python, `httpx`, `asyncio`, Vertex AI API.

---

### Task 1: Update Configuration

**Files:**
- Modify: `src/core/config.py`

- [ ] **Step 1: Add Vertex API Key and update default providers**

```python
# In src/core/config.py

# ... existing code ...
DEFAULT_AUTH_PASSWORD = os.getenv("GEMINI_AUTH_PASSWORD", "pwd")

# Add this:
VERTEX_API_KEY = os.getenv("VERTEX_API_KEY", DEFAULT_AUTH_PASSWORD)

# Update this:
DEFAULT_PROVIDERS = ["gemini-antigravity", "gemini-cli-oauth", "vertex"]
# ... rest of code ...
```

- [ ] **Step 2: Commit changes**

```bash
git add src/core/config.py
git commit -m "feat: add Vertex AI configuration"
```

---

### Task 2: Implement Vertex Logic in GeminiClient

**Files:**
- Modify: `src/core/gemini_client.py`

- [ ] **Step 1: Import VERTEX_API_KEY**

```python
# In src/core/gemini_client.py
from .config import DEFAULT_MODEL, DEFAULT_BASE_URL, DEFAULT_AUTH_PASSWORD, DEFAULT_THINKING_LEVEL, DEFAULT_PROVIDERS, VERTEX_API_KEY
```

- [ ] **Step 2: Modify `generate_async` to handle Vertex URL**

```python
# In src/core/gemini_client.py, generate_async method

        target_model = model or self.model
        action = "streamGenerateContent" if stream else "generateContent"
        
        # Base URL logic
        if model_provider == "vertex":
            url = f"https://aiplatform.googleapis.com/v1/publishers/google/models/{target_model}:{action}?key={VERTEX_API_KEY}"
        else:
            url = f"{self.api_base_url}/v1beta/models/{target_model}:{action}"
            if stream:
                url += "?alt=sse"
```

- [ ] **Step 3: Modify `_get_headers` to handle Vertex auth**

```python
# In src/core/gemini_client.py, _get_headers method

    def _get_headers(self, model_provider: Optional[str] = None) -> dict:
        headers = {"Content-Type": "application/json"}
        
        if model_provider == "vertex":
            # Vertex uses ?key= in the URL, but we can still set Content-Type
            return headers
            
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        # ...
```

- [ ] **Step 4: Update `generate_async` retry loop to use the dynamic URL**

Actually, the `url` is built before the retry loop. If the `model_provider` changes during retries, the `url` needs to be re-built.

```python
# In src/core/gemini_client.py, generate_async method (inside the retry loop)

            for attempt in range(max_retries):
                try:
                    # Re-build URL inside the loop if provider changes
                    current_url = url
                    if current_provider == "vertex":
                         current_url = f"https://aiplatform.googleapis.com/v1/publishers/google/models/{target_model}:{action}?key={VERTEX_API_KEY}"
                    else:
                         current_url = f"{self.api_base_url}/v1beta/models/{target_model}:{action}"
                         if stream:
                             current_url += "?alt=sse"

                    client = await self._get_client()
                    if stream:
                        resp = await self._handle_native_stream(client, current_url, payload, model_provider=current_provider)
                    else:
                        http_resp = await client.post(current_url, json=payload, headers=self._get_headers(model_provider=current_provider))
                        # ...
```

- [ ] **Step 5: Commit changes**

```bash
git add src/core/gemini_client.py
git commit -m "feat: implement Vertex AI logic in GeminiClient"
```

---

### Task 3: Verification

**Files:**
- Create: `tests/verify_vertex.py`

- [ ] **Step 1: Write verification script**

```python
import asyncio
from src.core.gemini_client import GeminiClient

async def main():
    # Force vertex provider for testing
    client = GeminiClient(model_provider="vertex", model="gemini-2.5-flash-lite")
    print("Testing Vertex AI endpoint...")
    resp = await client.generate_async(prompt="Say 'Vertex OK'")
    if resp.success:
        print(f"Success! Response: {resp.text}")
    else:
        print(f"Failed! Error: {resp.error}")

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Run verification**

Run: `python3 tests/verify_vertex.py`
Expected: `Success! Response: Vertex OK` (or similar)

- [ ] **Step 3: Commit verification script**

```bash
git add tests/verify_vertex.py
git commit -m "test: add Vertex AI verification script"
```
