import asyncio
import os
import sys
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Ensure API key is set
# You can set it in your environment: $env:ANTHROPIC_API_KEY = "your-key"
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("WARNING: ANTHROPIC_API_KEY environment variable is not set.")
    # For testing, you can hardcode here or prompt user

async def main():
    # 1. Initialize MCP Client
    server_script = os.path.join(os.path.dirname(__file__), "civil3d_mcp_server", "server.py")
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script]
    )

    print("Starting MCP Client and connecting to Civil 3D MCP Server...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Fetch tools from MCP Server
            mcp_tools = await session.list_tools()
            tools_for_claude = []
            
            for tool in mcp_tools.tools:
                tools_for_claude.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })
            
            print(f"Loaded tools from MCP: {[t['name'] for t in tools_for_claude]}")
            
            if not api_key:
                print("Cannot proceed without Anthropic API Key.")
                return

            client = Anthropic(api_key=api_key)
            
            # Simple CLI Loop
            print("\n--- Claude Civil 3D Agent Ready ---")
            print("Type 'exit' to quit.")
            while True:
                user_input = input("\nYou: ")
                if user_input.strip().lower() == 'exit':
                    break
                
                print("Claude: (thinking...)")
                response = client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=1024,
                    tools=tools_for_claude,
                    messages=[
                        {"role": "user", "content": user_input}
                    ]
                )
                
                for content_block in response.content:
                    if content_block.type == 'text':
                        print(f"Claude: {content_block.text}")
                    elif content_block.type == 'tool_use':
                        tool_name = content_block.name
                        tool_args = content_block.input
                        print(f"Claude called tool '{tool_name}' with args {tool_args}")
                        
                        # Execute tool on MCP Server
                        try:
                            result = await session.call_tool(tool_name, tool_args)
                            result_text = result.content[0].text if result.content else "Success"
                            print(f"Tool Result: {result_text}")
                            
                            # Send result back to Claude
                            follow_up = client.messages.create(
                                model="claude-3-5-sonnet-20240620",
                                max_tokens=1024,
                                tools=tools_for_claude,
                                messages=[
                                    {"role": "user", "content": user_input},
                                    {"role": "assistant", "content": response.content},
                                    {
                                        "role": "user", 
                                        "content": [
                                            {
                                                "type": "tool_result",
                                                "tool_use_id": content_block.id,
                                                "content": result_text
                                            }
                                        ]
                                    }
                                ]
                            )
                            for follow_up_content in follow_up.content:
                                if follow_up_content.type == 'text':
                                    print(f"Claude: {follow_up_content.text}")
                        except Exception as e:
                            print(f"Error executing tool: {e}")

if __name__ == "__main__":
    asyncio.run(main())
