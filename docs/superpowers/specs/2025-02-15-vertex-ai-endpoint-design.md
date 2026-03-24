# Design Spec: Vertex AI Endpoint Integration (Gemini 2.5 Flash Lite support)

## 🎯 Goal
Integrate a new direct endpoint for Vertex AI into the existing `GeminiClient` rotation logic. This allows the system to utilize Vertex AI models (like `gemini-2.5-flash-lite`) alongside existing providers.

## 🏗️ Architecture
The integration will follow the **Integrated Provider Logic** pattern within `src/core/gemini_client.py`.

### 1. Configuration Changes (`src/core/config.py`)
- Add `VERTEX_API_KEY` to environment variables (defaulting to the provided `AQ.` token or an `AIza` key).
- Add `vertex` to the `DEFAULT_PROVIDERS` list for automatic rotation.
- Set `DEFAULT_MODEL` or provide a way to target `gemini-2.5-flash-lite` (user called it `gemini3flash`).

### 2. Client Logic Changes (`src/core/gemini_client.py`)
- **URL Building**: In `generate_async`, if the selected provider is `"vertex"`, the client will build a specialized URL:
  `https://aiplatform.googleapis.com/v1/publishers/google/models/{model_id}:{action}?key={VERTEX_API_KEY}`
- **Authentication**: When using the Vertex endpoint, the API Key is passed as a URL parameter (`?key=`), bypassing the `Authorization: Bearer` header used for standard providers (or combining them if necessary, but the user's test showed `?key=` works).
- **Provider Rotation**: The `_get_next_provider()` logic remains unchanged, but the `generate_async` loop will now handle the different URL and auth requirements for the `vertex` provider.

## 🛠️ Implementation Plan
1. **Update `src/core/config.py`**:
   - Define `VERTEX_API_KEY = os.getenv("VERTEX_API_KEY", DEFAULT_AUTH_PASSWORD)`.
   - Update `DEFAULT_PROVIDERS = ["gemini-antigravity", "gemini-cli-oauth", "vertex"]`.
2. **Update `src/core/gemini_client.py`**:
   - Modify `generate_async` to branch based on `current_provider == "vertex"`.
   - Implement the simplified Vertex AI URL construction.
   - Ensure `max_tokens` and other `generationConfig` parameters are compatible with the Vertex AI endpoint.
3. **Validation**:
   - Run a test script to verify that the rotation eventually picks the `vertex` provider and successfully calls the `gemini-2.5-flash-lite` model.

## ✅ Success Criteria
- The system can successfully generate SVGs using the Vertex AI endpoint.
- Errors on the Vertex endpoint trigger the standard `GeminiClient` retry/rotation logic.
- No regression in existing provider functionality.
