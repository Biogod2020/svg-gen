import asyncio
import sys
from dotenv import load_dotenv

# SOTA 3.0: Load environment before any project imports to ensure GeminiClient has credentials
load_dotenv()

from mcp.server import Server
from mcp.server.stdio import stdio_server

from src.mcp_shared import register_tools


async def main():
    server = Server("svg-gen-local")
    register_tools(server)

    async with stdio_server() as (read_stream, write_stream):
        original_stdout = sys.stdout
        sys.stdout = sys.stderr
        try:
            await server.run(
                read_stream, write_stream, server.create_initialization_options()
            )
        finally:
            sys.stdout = original_stdout


if __name__ == "__main__":
    asyncio.run(main())
