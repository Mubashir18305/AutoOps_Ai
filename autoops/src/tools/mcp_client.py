import asyncio
from contextlib import AsyncExitStack
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession
from langchain_core.tools import StructuredTool
from pydantic import create_model

class MCPClientManager:
    """
    Manages connections to standalone MCP Servers via SSE
    and dynamically converts their tools into LangChain tools.
    """
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.session = None
        self.exit_stack = AsyncExitStack()

    async def connect(self):
        """Establish SSE connection to the MCP server."""
        # sse_client returns (read_stream, write_stream)
        read_stream, write_stream = await self.exit_stack.enter_async_context(sse_client(self.server_url))
        self.session = await self.exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
        await self.session.initialize()

    async def get_langchain_tools(self):
        """Fetch tools from MCP and convert to LangChain format."""
        if not self.session:
            await self.connect()
            
        response = await self.session.list_tools()
        langchain_tools = []
        
        for tool_schema in response.tools:
            # We create a closure to hold the tool name
            def create_tool_func(name=tool_schema.name):
                async def invoke_tool(**kwargs):
                    result = await self.session.call_tool(name, arguments=kwargs)
                    return result.content[0].text if result.content else "No output"
                return invoke_tool

            # In a full implementation, we'd convert JSON Schema to Pydantic dynamically.
            # Here we wrap it in a generic LangChain StructuredTool.
            lc_tool = StructuredTool.from_function(
                func=create_tool_func(tool_schema.name),
                name=tool_schema.name,
                description=tool_schema.description or "MCP Tool",
                coroutine=create_tool_func(tool_schema.name)
            )
            langchain_tools.append(lc_tool)
            
        return langchain_tools

    async def close(self):
        await self.exit_stack.aclose()
