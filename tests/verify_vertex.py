import asyncio
from dotenv import load_dotenv

# Load environment variables (GEMINI_API_KEY, GOOGLE_CLOUD_PROJECT, etc.)
load_dotenv()

from src.core.gemini_client import GeminiClient


async def verify(provider: str, prompt: str):
    # Note: gemini-3-flash is the standard model for SOTA 3.0
    # Using model_provider as a list [provider] to force a specific provider for verification
    client = GeminiClient(model_provider=[provider], model="gemini-3-flash")
    print(f"Testing {provider} endpoint...")
    resp = await client.generate_async(prompt=prompt)
    return provider, resp


async def main():
    import os

    results = []

    # Placeholder value check
    placeholders = {
        "GEMINI_API_KEY": "your_aistudio_api_key_here",
        "GOOGLE_CLOUD_PROJECT": "your_gcp_project_id_here",
    }

    skipped = 0
    for provider in ["aistudio", "vertex"]:
        try:
            # SOTA 3.0: Standardized pre-flight placeholder check
            if provider == "aistudio":
                key = os.getenv("GEMINI_API_KEY")
                if not key or key == placeholders["GEMINI_API_KEY"]:
                    print(
                        f"[SKIP] {provider} has placeholder or missing GEMINI_API_KEY. Update .env."
                    )
                    skipped += 1
                    continue
            elif provider == "vertex":
                project = os.getenv("GOOGLE_CLOUD_PROJECT")
                if not project or project == placeholders["GOOGLE_CLOUD_PROJECT"]:
                    print(
                        f"[SKIP] {provider} has placeholder or missing GOOGLE_CLOUD_PROJECT. Update .env."
                    )
                    skipped += 1
                    continue

            name, response = await verify(provider, f"Say '{provider} OK'")
            results.append((name, response))
            if response.success:
                print(f"[SUCCESS] {name} is working: {response.text}")
            else:
                print(f"[FAILED] {name} call failed: {response.error}")
        except Exception as e:
            print(f"[ERROR] {provider} raised exception: {str(e)}")

    print("\n--- Summary ---")
    all_ok = True
    for name, resp in results:
        status = "OK" if resp.success else "FAILED"
        print(f"{name}: {status}")
        if not resp.success:
            all_ok = False

    if not all_ok:
        print("\nVerification failed for one or more providers.")
    elif skipped == 2:
        print("\nAll cloud providers skipped (placeholders in .env).")
    else:
        print("\nAll providers working correctly.")


if __name__ == "__main__":
    asyncio.run(main())
