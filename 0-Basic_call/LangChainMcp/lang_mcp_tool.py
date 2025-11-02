from langchain.agents import create_agent
from langchain_groq import ChatGroq
from databricks.sdk import WorkspaceClient
from databricks_mcp import DatabricksOAuthClientProvider
from mcp.client.streamable_http import streamablehttp_client as connect
from mcp import ClientSession
import asyncio
from langchain_core.tools import BaseTool
from pydantic import BaseModel,Field,create_model
from typing import Any,Dict

class McpTool(BaseTool):
    """LangChain Tool wrapper for an MCP tool."""


    def __init__(
        self,
        name: str,
        description: str,
        args_schema: type,
        mcp_url:str,
        ws:WorkspaceClient
        ):
        # Initialize the tool
        #self.session=session
        super().__init__(name=name, description=description, args_schema=args_schema)
        object.__setattr__(self,"server_url",mcp_url)
        object.__setattr__(self,"ws",ws)
    def _run(self, *args, **kwargs):
        raise NotImplementedError("This tool is async. Use _arun.")
        
    async def _arun(self, **kwargs) -> str:
        async with connect(self.server_url, auth=DatabricksOAuthClientProvider(self.ws)) as (
        read_stream,
        write_stream,
        _,
    ):
        # Create a session using the client streams
            async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
                await session.initialize()
            
                try:
                    # Call the tool using the active session
                    tool_arguments = kwargs
                    tool_result = await session.call_tool(self.name, tool_arguments)
                    # The result is a dict/object, convert it to a string for the agent
                    print(f"✅ MCP Tool Result Received: {tool_result}")
                    return str(tool_result)
                except Exception as e:
                    return f"Error calling tool {self.name}: {e}"
