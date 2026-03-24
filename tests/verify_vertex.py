import asyncio
import os
from dotenv import load_dotenv

# Load environment variables (VERTEX_API_KEY) before project imports
load_dotenv()

from src.core.gemini_client import GeminiClient

async def main():
    # Force vertex provider for testing
    # Note: gemini-2.5-flash-lite is the model the user requested
    client = GeminiClient(model_provider="vertex", model="gemini-2.5-flash-lite")
    print("Testing Vertex AI endpoint...")
    
    # Simple prompt to verify connection
    resp = await client.generate_async(prompt="Say 'Vertex OK'")
    
    if resp.success:
        print(f"\n[SUCCESS] Vertex AI is working!")
        print(f"Response: {resp.text}")
        if resp.thoughts:
            print(f"Thoughts: {resp.thoughts}")
    else:
        print(f"\n[FAILED] Vertex AI call failed.")
        print(f"Error: {resp.error}")
        if resp.raw_response:
            print(f"Raw Response: {resp.raw_response}")

if __name__ == "__main__":
    asyncio.run(main())
