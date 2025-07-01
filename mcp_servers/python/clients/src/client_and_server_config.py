ClientsConfig =[
    "MCP_CLIENT_AZURE_AI",
    "MCP_CLIENT_OPENAI",
	"MCP_CLIENT_GEMINI"
]
ServersConfig = [
{
"server_name": "MCP-GSUITE",
"command":"uv",
"args": [
"--directory",
"mcp_servers/python/servers/MCP-GSUITE/mcp-gsuite",
"run",
"mcp-gsuite"
]
},
{
"server_name": "NUMPY_MCP",
"command": "python",
"args": [
"mcp_servers/python/servers/NUMPY_MCP/mcp_numpy.py"
]
}
]
