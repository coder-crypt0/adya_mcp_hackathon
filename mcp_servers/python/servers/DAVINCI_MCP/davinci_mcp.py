import logging
from collections.abc import Sequence
from typing import Any, Dict, List
import json
import traceback

from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
import mcp.server.stdio
import mcp.types as types

# Try importing DaVinci Resolve scripting API
# Note: This import only works inside DaVinci Resolve's Python environment.
try:
    import DaVinciResolveScript as dvr_script  # type: ignore
except ImportError:
    dvr_script = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("davinci-mcp")

app = Server("davinci-mcp")

import socket

import time

def call_resolve(command: str, args: dict = None):
    """
    Communicate with the DaVinci Resolve bridge service over a local socket.
    Includes retry logic and robust error/result validation.
    """
    HOST = "127.0.0.1"
    PORT = 6060
    args = args or {}
    action = "get_current_project_name" if command == "get_current_project" else command
    request = {"action": action, "args": args}
    last_error = None
    for _ in range(10):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT))
                s.sendall(json.dumps(request).encode())
                response = json.loads(s.recv(16384).decode())
                if "error" in response:
                    raise Exception(response["error"])
                result = response.get("result")
                if result is None or (isinstance(result, str) and ("object at 0x" in result or "function" in result.lower())):
                    raise Exception(f"Bridge returned invalid result for '{action}'. Likely returned a function instead of value.")
                return result
        except Exception as e:
            last_error = str(e)
            time.sleep(0.5)
    raise Exception(f"[Bridge Error] Failed to reach Resolve bridge for '{action}': {last_error}")

class DaVinciToolHandler:
    def __init__(self, name: str):
        self.name = name

    def get_tool_description(self) -> Tool:
        raise NotImplementedError()

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        raise NotImplementedError()

# Example Tool: Get Project List
class GetProjectListToolHandler(DaVinciToolHandler):
    def __init__(self):
        super().__init__("get_project_list")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="List all DaVinci Resolve projects in the current database",
            inputSchema={"type": "object", "properties": {}, "required": []}
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("get_project_list", args)
            return [TextContent(type="text", text=f"Projects: {json.dumps(result, indent=2)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

# --- TOOL HANDLERS ---

class OpenProjectToolHandler(DaVinciToolHandler):
    def __init__(self):
        super().__init__("open_project")
    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Open a DaVinci Resolve project by name",
            inputSchema={"type": "object", "properties": {"project_name": {"type": "string"}}, "required": ["project_name"]}
        )
    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("open_project", args)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

class CreateProjectToolHandler(DaVinciToolHandler):
    def __init__(self):
        super().__init__("create_project")
    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Create a new DaVinci Resolve project",
            inputSchema={"type": "object", "properties": {"project_name": {"type": "string"}}, "required": ["project_name"]}
        )
    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("create_project", args)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

class DeleteProjectToolHandler(DaVinciToolHandler):
    def __init__(self):
        super().__init__("delete_project")
    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Delete a DaVinci Resolve project by name",
            inputSchema={"type": "object", "properties": {"project_name": {"type": "string"}}, "required": ["project_name"]}
        )
    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("delete_project", args)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

class GetCurrentProjectToolHandler(DaVinciToolHandler):
    def __init__(self):
        super().__init__("get_current_project")
    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Get the name of the currently open DaVinci Resolve project",
            inputSchema={"type": "object", "properties": {}, "required": []}
        )
    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("get_current_project", args)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

class ListTimelinesToolHandler(DaVinciToolHandler):
    def __init__(self):
        super().__init__("list_timelines")
    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="List all timelines in the current project",
            inputSchema={"type": "object", "properties": {}, "required": []}
        )
    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("list_timelines", args)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

class CreateTimelineToolHandler(DaVinciToolHandler):
    def __init__(self):
        super().__init__("create_timeline")
    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Create a new timeline in the current project",
            inputSchema={"type": "object", "properties": {"timeline_name": {"type": "string"}}, "required": ["timeline_name"]}
        )
    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("create_timeline", args)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

class DeleteTimelineToolHandler(DaVinciToolHandler):
    def __init__(self):
        super().__init__("delete_timeline")
    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Delete a timeline by name in the current project",
            inputSchema={"type": "object", "properties": {"timeline_name": {"type": "string"}}, "required": ["timeline_name"]}
        )
    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("delete_timeline", args)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

class ImportMediaToolHandler(DaVinciToolHandler):
    def __init__(self):
        super().__init__("import_media")
    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Import media files into the media pool",
            inputSchema={"type": "object", "properties": {"file_paths": {"type": "array", "items": {"type": "string"}}}, "required": ["file_paths"]}
        )
    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("import_media", args)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

class ListMediaPoolItemsToolHandler(DaVinciToolHandler):
    def __init__(self):
        super().__init__("list_media_pool_items")
    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="List all media pool items in the current project",
            inputSchema={"type": "object", "properties": {}, "required": []}
        )
    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("list_media_pool_items", args)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

class DeleteMediaPoolItemToolHandler(DaVinciToolHandler):
    def __init__(self):
        super().__init__("delete_media_pool_item")
    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Delete a media pool item by name",
            inputSchema={"type": "object", "properties": {"item_name": {"type": "string"}}, "required": ["item_name"]}
        )
    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("delete_media_pool_item", args)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

class AddTimelineMarkerToolHandler(DaVinciToolHandler):
    def __init__(self):
        super().__init__("add_timeline_marker")
    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Add a marker to the current timeline",
            inputSchema={"type": "object", "properties": {"frame_id": {"type": "integer"}, "color": {"type": "string"}, "name": {"type": "string"}, "note": {"type": "string"}}, "required": ["frame_id", "color"]}
        )
    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("add_timeline_marker", args)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

class ListTimelineMarkersToolHandler(DaVinciToolHandler):
    def __init__(self):
        super().__init__("list_timeline_markers")
    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="List all markers in the current timeline",
            inputSchema={"type": "object", "properties": {}, "required": []}
        )
    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("list_timeline_markers", args)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

class DeleteTimelineMarkerToolHandler(DaVinciToolHandler):
    def __init__(self):
        super().__init__("delete_timeline_marker")
    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Delete a marker at a specific frame in the current timeline",
            inputSchema={"type": "object", "properties": {"frame_id": {"type": "integer"}}, "required": ["frame_id"]}
        )
    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("delete_timeline_marker", args)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

class StartRenderJobToolHandler(DaVinciToolHandler):
    def __init__(self):
        super().__init__("start_render_job")
    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Start a render job for the current timeline",
            inputSchema={"type": "object", "properties": {"render_preset": {"type": "string"}}, "required": ["render_preset"]}
        )
    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("start_render_job", args)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

class ListRenderJobsToolHandler(DaVinciToolHandler):
    def __init__(self):
        super().__init__("list_render_jobs")
    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="List all render jobs in the current project",
            inputSchema={"type": "object", "properties": {}, "required": []}
        )
    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("list_render_jobs", args)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

class StopRenderingToolHandler(DaVinciToolHandler):
    def __init__(self):
        super().__init__("stop_rendering")
    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Stop the current rendering process",
            inputSchema={"type": "object", "properties": {}, "required": []}
        )
    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("stop_rendering", args)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

class ApplyLUTToolHandler(DaVinciToolHandler):
    def __init__(self):
        super().__init__("apply_lut")
    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Apply a LUT to the current timeline",
            inputSchema={"type": "object", "properties": {"lut_path": {"type": "string"}}, "required": ["lut_path"]}
        )
    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("apply_lut", args)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

class ExportTimelineToolHandler(DaVinciToolHandler):
    def __init__(self):
        super().__init__("export_timeline")
    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Export the current timeline to a file",
            inputSchema={"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]}
        )
    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("export_timeline", args)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

class RunFusionScriptToolHandler(DaVinciToolHandler):
    def __init__(self):
        super().__init__("run_fusion_script")
    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Run a Fusion script in the current project",
            inputSchema={"type": "object", "properties": {"script_path": {"type": "string"}}, "required": ["script_path"]}
        )
    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("run_fusion_script", args)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

class BatchProjectExportToolHandler(DaVinciToolHandler):
    def __init__(self):
        super().__init__("batch_project_export")
    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Export all projects in the database to a folder",
            inputSchema={"type": "object", "properties": {"folder_path": {"type": "string"}}, "required": ["folder_path"]}
        )
    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            result = call_resolve("batch_project_export", args)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

# Register tool handlers (20+)
tool_handlers: Dict[str, DaVinciToolHandler] = {}
def add_tool_handler(tool_class: DaVinciToolHandler):
    global tool_handlers
    tool_handlers[tool_class.name] = tool_class

add_tool_handler(GetProjectListToolHandler())
add_tool_handler(OpenProjectToolHandler())
add_tool_handler(CreateProjectToolHandler())
add_tool_handler(DeleteProjectToolHandler())
add_tool_handler(GetCurrentProjectToolHandler())
add_tool_handler(ListTimelinesToolHandler())
add_tool_handler(CreateTimelineToolHandler())
add_tool_handler(DeleteTimelineToolHandler())
add_tool_handler(ImportMediaToolHandler())
add_tool_handler(ListMediaPoolItemsToolHandler())
add_tool_handler(DeleteMediaPoolItemToolHandler())
add_tool_handler(AddTimelineMarkerToolHandler())
add_tool_handler(ListTimelineMarkersToolHandler())
add_tool_handler(DeleteTimelineMarkerToolHandler())
add_tool_handler(StartRenderJobToolHandler())
add_tool_handler(ListRenderJobsToolHandler())
add_tool_handler(StopRenderingToolHandler())
add_tool_handler(ApplyLUTToolHandler())
add_tool_handler(ExportTimelineToolHandler())
add_tool_handler(RunFusionScriptToolHandler())
add_tool_handler(BatchProjectExportToolHandler())

@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    return [th.get_tool_description() for th in tool_handlers.values()]

@app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    try:
        tool_handler = tool_handlers.get(name)
        if not tool_handler:
            raise ValueError(f"Unknown tool: {name}")
        return tool_handler.run_tool(arguments)
    except Exception as e:
        logger.error(f"Error during call_tool: {str(e)}")
        logger.error(traceback.format_exc())
        return [TextContent(type="text", text=f"Error in {name}: {str(e)}")]

@app.list_resources()
async def handle_list_resources() -> List[types.Resource]:
    return [
        types.Resource(
            uri="davinci://operations",
            name="DaVinci Resolve Operations",
            description="Available DaVinci Resolve operations and capabilities",
            mimeType="text/plain"
        )
    ]

@app.read_resource()
async def handle_read_resource(uri: str) -> str:
    if uri == "davinci://operations":
        operations = [
            "Project Management: List, open, create, delete projects",
            "Timeline: List, create, delete, export timelines",
            "Media: Import, list, delete media pool items",
            "Render: Start, stop, list render jobs",
            "Color: Apply LUTs, grades, export stills",
            "Fusion: Run fusion scripts, apply effects",
            "Markers: Add, list, delete timeline markers",
            "Automation: Batch operations, scripting"
        ]
        return "\n".join(operations)
    else:
        raise ValueError(f"Unknown resource: {uri}")

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
