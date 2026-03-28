import asyncio
import json
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_apple_generation():
    print("🚀 Starting MCP Test: Generating 'an apple'...")

    # Server parameters
    server_params = StdioServerParameters(
        command="python3", args=["mcp_stdio.py"], env={**os.environ, "PYTHONPATH": "."}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()

            # List tools to verify
            tools = await session.list_tools()
            print(f"📦 Available tools: {[t.name for t in tools.tools]}")

            # Call generate_svg
            print(
                "🎨 Calling generate_svg tool (this may take a minute due to audit loop)..."
            )
            result = await session.call_tool(
                "generate_svg",
                arguments={
                    "prompt": "一个红苹果，写实风格，带一点高光",
                    "style_hints": "vibrant colors, soft shadows",
                },
            )

            # Print result summary
            for content in result.content:
                if content.type == "text":
                    print("\n--- MCP Response ---")
                    # Show first 500 chars to avoid flooding the console
                    text = content.text
                    if len(text) > 1000:
                        print(text[:1000] + "... [truncated]")
                    else:
                        print(text)

                    # Save the SVG to a file for verification
                    if "```xml" in text:
                        svg_code = text.split("```xml")[1].split("```")[0].strip()
                        with open("mcp_test_apple.svg", "w", encoding="utf-8") as f:
                            f.write(svg_code)
                        print(f"\n💾 SVG saved to mcp_test_apple.svg")


if __name__ == "__main__":
    asyncio.run(test_mcp_apple_generation())
