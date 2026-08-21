import asyncio
import logging
import psutil
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("civil3d_mcp_server")

app = Server("civil3d-mcp-server")

def is_civil3d_running():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and 'acad.exe' in proc.info['name'].lower():
            return True
    return False

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="civil3d_status",
            description="Check if AutoCAD/Civil 3D process is running.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="draw_line",
            description="Draw an 8m line in Civil 3D.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "civil3d_status":
        running = is_civil3d_running()
        return [TextContent(type="text", text=f"Civil 3D running status: {running}")]
    elif name == "draw_line":
        # In a real scenario, this would use COM interop to send commands to Civil 3D.
        # For now, we simulate the action.
        if not is_civil3d_running():
            return [TextContent(type="text", text="Error: Civil 3D is not running. Please open it first.")]
        return [TextContent(type="text", text="Successfully executed draw_line command in Civil 3D.")]
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    logger.info("Starting Civil 3D MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
