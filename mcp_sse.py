import asyncio
from dotenv import load_dotenv

# SOTA 3.0: Load environment before any project imports
load_dotenv()

import uvicorn
from fastapi import FastAPI
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.responses import Response

from src.mcp_shared import register_tools

app = FastAPI(title="SVG Gen MCP Server (SSE)")
server = Server("svg-gen-remote")
register_tools(server)

sse_transport = SseServerTransport("/mcp/messages")


@app.get("/mcp/sse")
async def handle_sse(request: Request):
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )

    return Response()


@app.post("/mcp/messages")
async def handle_messages(request: Request):
    await sse_transport.handle_post_message(
        request.scope, request.receive, request._send
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
