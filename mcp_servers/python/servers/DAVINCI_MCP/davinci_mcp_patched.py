
import socket
import json
import time
from typing import Sequence
from mcp_sdk.models import TextContent
from .base import DaVinciToolHandler

def call_resolve(command: str, args: dict = None):
    HOST = "127.0.0.1"
    PORT = 6060
    args = args or {}
    action = "get_current_project_name" if command == "get_current_project" else command
    request = {"action": action, "args": args}

    for _ in range(10):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT))
                s.sendall(json.dumps(request).encode())
                response = json.loads(s.recv(16384).decode())
                if "error" in response:
                    raise Exception(response["error"])
                result = response.get("result")
                if result is None or isinstance(result, str) and ("object at 0x" in result or "function" in result.lower()):
                    raise Exception(f"Bridge returned invalid result for '{action}'. Likely returned a function instead of value.")
                return result
        except Exception as e:
            last_error = str(e)
            time.sleep(0.5)
    raise Exception(f"[Bridge Error] Failed to reach Resolve bridge for '{action}': {last_error}")

class GetProjectListToolHandler(DaVinciToolHandler):
    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("get_project_list")
            if not isinstance(result, list):
                raise TypeError("Expected list, got: " + str(result))
            return [TextContent(type="text", text="Projects:\n" + json.dumps(result, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
