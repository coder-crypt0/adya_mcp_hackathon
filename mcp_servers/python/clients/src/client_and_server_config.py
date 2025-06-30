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
			"../servers/MCP-GSUITE/mcp-gsuite",
			"run",
			"mcp-gsuite"
		]
	},
	{
		"server_name": "NUMPY_MCP",
		"command": "uvicorn",
		"args": [
			"--app-dir", "../servers/NUMPY_MCP",
			"mcp_numpy:app",
			"--port", "8010"
		]
	}
]