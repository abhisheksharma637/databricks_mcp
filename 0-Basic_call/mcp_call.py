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
from LangChainMcp.lang_mcp_tool import McpTool

##########Choosing profile from databricks cli#########
#databricks_cli_profile = "abhishek637"
#######Workspace client#########
client = WorkspaceClient(profile=databricks_cli_profile)
############databricks auth###########

auth=DatabricksOAuthClientProvider(client)

##########App / custom mcp URL#############
#########Remember to put /mcp at end else it wont work###############
app_url = "https://mcp-custom-server-539843816408256.16.azure.databricksapps.com/mcp"

#######List to hold tools in mcp server
agent_tools=[]

##########Creating llm##############
import os
#########Define your model or LLM key here########33
llm=ChatGroq(model='llama-3.1-8b-instant')

#########Creating MCP tools into langchain tool class format and reading args from tools and using
async def get_langchain_format_tools(tools):
    if tools.tools:
        for t in tools.tools:
            print(t)
            schema=t.inputSchema.copy()
            properties=schema.get('properties',{})
            type_mapping={"integer":int,"number":float,"boolean":bool}
            field_definations={}
            for field_name,field_info in properties.items():
                field_type_str=field_info.get('type','string')
                field_type=type_mapping.get(field_type_str,'str')
                field_definations[field_name]=(field_type,None)
            args_schema=create_model(f"{t.name}Args",**field_definations)
            langchain_tools=McpTool(
                        name=t.name,             # Use the MCP tool's name
                        description=t.description,                                    
                        args_schema=args_schema,
                        mcp_url=app_url,
                        ws=client    # Store the original MCP tool name
                    )
            agent_tools.append(langchain_tools)

async def get_mcp_tools():
    async with connect(app_url, auth=auth) as (
        read_stream,
        write_stream,
        _,
    ):
        # Create a session using the client streams
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()
            # Call a tool
            # 1. Extract the arguments from the fixed key 'tool_args'
            
            #print("🔍 Fetching tool list...")
            return(await session.list_tools())
    



##########Async main loop for calling mcp and using client##########
async def main():
    # Connect to a streamable HTTP server
    #print("Get List of tools in mcp server")
    tools=await get_mcp_tools()
    await get_langchain_format_tools(tools)
    print(agent_tools)
async def agent_run(question):
    agent=create_agent(model=llm,tools=agent_tools)
    #########Calling agent#############
    response = await \
            agent.ainvoke({"messages":question})
    print("--- Agent Response ---")
    #print(response)

if __name__ == "__main__":
    asyncio.run(main())
    question="""You are a helpful assistant.Use the tool "get_nyc_taxi_sample" on mcp server dont use brave search
provide some data about new york taxi trips"""
    asyncio.run(agent_run(question))
    
