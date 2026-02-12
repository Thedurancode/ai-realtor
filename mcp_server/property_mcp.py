#!/usr/bin/env python3
"""
Property Management MCP Server for AI Realtor
Exposes property database operations as MCP tools

Supports two transports:
  - stdio (default): For local Claude Desktop usage
  - sse: For remote HTTP access (deployed on Fly.io)

Usage:
  python property_mcp.py                  # stdio mode
  python property_mcp.py --transport sse  # SSE mode on port 8001
  python property_mcp.py --transport sse --port 9000
"""
import argparse
import asyncio
import os
import sys

# Add parent directory to path for app.database imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import mcp.server.stdio

# Import server instance (registers @app.list_tools / @app.call_tool)
from mcp_server.server import app  # noqa: E402

# Import all tool modules (triggers register_tool() calls at import time)
import mcp_server.tools  # noqa: F401, E402


async def main_stdio():
    """Run the MCP server over stdio (for Claude Desktop)"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def main_sse(port: int = 8001):
    """Run the MCP server over SSE (for remote HTTP access)"""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import JSONResponse
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware
    import uvicorn

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        from starlette.responses import Response
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
        return Response()

    async def handle_messages(request):
        from starlette.responses import Response
        await sse.handle_post_message(
            request.scope, request.receive, request._send
        )
        return Response(status_code=202)

    async def health(request):
        return JSONResponse({"status": "ok", "server": "property-management-mcp", "transport": "sse"})

    starlette_app = Starlette(
        routes=[
            Route("/health", health),
            Route("/sse", handle_sse),
            Route("/messages/", handle_messages, methods=["POST"]),
        ],
        middleware=[
            Middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_methods=["*"],
                allow_headers=["*"],
            ),
        ],
    )

    print(f"MCP SSE server running on http://0.0.0.0:{port}")
    print(f"  SSE endpoint: http://0.0.0.0:{port}/sse")
    print(f"  Health check: http://0.0.0.0:{port}/health")
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Property Management MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport to use (default: stdio)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_SSE_PORT", "8001")),
        help="Port for SSE transport (default: 8001)"
    )
    args = parser.parse_args()

    if args.transport == "sse":
        main_sse(args.port)
    else:
        asyncio.run(main_stdio())
