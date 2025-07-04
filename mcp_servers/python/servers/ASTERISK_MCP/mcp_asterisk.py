import logging
from collections.abc import Sequence
from typing import Any, Dict, List, Optional
import json
import traceback
import asyncio
import socket
from datetime import datetime, timedelta
import random

from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
import mcp.server.stdio
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asterisk-mcp")

# MCP server instance
app = Server("asterisk-mcp")

# Tool handler base class
class AsteriskToolHandler:
    def __init__(self, name: str):
        self.name = name

    def get_tool_description(self) -> Tool:
        raise NotImplementedError()

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        raise NotImplementedError()

# Simulated AMI Client for demo purposes
class SimulatedAMIClient:
    def __init__(self):
        self.connected = False
        self.extensions = {
            "1001": {"name": "Alice Johnson", "status": "Available", "context": "internal"},
            "1002": {"name": "Bob Smith", "status": "Busy", "context": "internal"},
            "1003": {"name": "Charlie Brown", "status": "Unavailable", "context": "internal"}
        }
        self.active_calls = []
        self.call_history = []

    async def connect(self):
        self.connected = True
        logger.info("Connected to simulated Asterisk AMI")

    async def disconnect(self):
        self.connected = False
        logger.info("Disconnected from simulated Asterisk AMI")

    def get_status(self):
        return {
            "system_health": "ONLINE",
            "uptime": "2 days, 14 hours, 23 minutes",
            "version": "Asterisk 18.20.0 (Simulated)",
            "active_calls": len(self.active_calls),
            "registered_extensions": len(self.extensions),
            "memory_usage": "45%",
            "cpu_usage": "12%"
        }

# Initialize AMI connection
async def initialize_asterisk_ami(credentials: dict = None):
    """Initialize Asterisk AMI connection"""
    try:
        # For demo purposes, we'll use simulated connection
        # In real implementation, this would connect to actual Asterisk AMI
        ami_client = SimulatedAMIClient()
        await ami_client.connect()
        logger.info("Asterisk AMI initialized successfully")
        return ami_client
    except Exception as e:
        logger.error(f"Failed to initialize Asterisk AMI: {str(e)}")
        return None

# 1. Make Call Tool
class MakeCallToolHandler(AsteriskToolHandler):
    def __init__(self):
        super().__init__("make_call")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Originate a call between two extensions in Asterisk",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_extension": {
                        "type": "string",
                        "description": "Source extension number"
                    },
                    "to_extension": {
                        "type": "string",
                        "description": "Destination extension number"
                    },
                    "context": {
                        "type": "string",
                        "description": "Dialplan context (default: internal)",
                        "default": "internal"
                    },
                    "__credentials__": {
                        "type": "object",
                        "description": "Asterisk AMI credentials (optional for simulation)"
                    }
                },
                "required": ["from_extension", "to_extension"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            from_ext = args["from_extension"]
            to_ext = args["to_extension"]
            context = args.get("context", "internal")

            # Simulate call origination
            call_id = f"CALL-{random.randint(1000, 9999)}"
            channel = f"SIP/{from_ext}-{random.randint(10000000, 99999999):08x}"
            
            call_info = {
                "call_id": call_id,
                "from": from_ext,
                "to": to_ext,
                "context": context,
                "channel": channel,
                "status": "Ringing",
                "start_time": datetime.now().isoformat(),
                "duration": 0
            }

            result = f"""Call Originated Successfully
================================
Call ID: {call_id}
From: {from_ext}
To: {to_ext}
Context: {context}
Channel: {channel}
Status: Ringing
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

The call has been initiated. Both parties should receive the call shortly."""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"Error making call: {str(e)}")]

# 2. Get Active Calls Tool
class GetActiveCallsToolHandler(AsteriskToolHandler):
    def __init__(self):
        super().__init__("get_active_calls")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Get list of currently active calls in Asterisk",
            inputSchema={
                "type": "object",
                "properties": {
                    "__credentials__": {
                        "type": "object",
                        "description": "Asterisk AMI credentials (optional for simulation)"
                    }
                }
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            # Simulate active calls
            active_calls = [
                {
                    "channel": "SIP/1001-00000001",
                    "caller_id": "1001",
                    "destination": "1002",
                    "state": "Up",
                    "duration": "00:02:34",
                    "start_time": (datetime.now() - timedelta(minutes=2, seconds=34)).strftime('%H:%M:%S')
                },
                {
                    "channel": "SIP/1003-00000002", 
                    "caller_id": "1003",
                    "destination": "external",
                    "state": "Ringing",
                    "duration": "00:00:12",
                    "start_time": (datetime.now() - timedelta(seconds=12)).strftime('%H:%M:%S')
                }
            ]

            result = "Active Calls\n" + "=" * 50 + "\n"
            if not active_calls:
                result += "No active calls at this time.\n"
            else:
                for i, call in enumerate(active_calls, 1):
                    result += f"""
Call #{i}:
  Channel: {call['channel']}
  From: {call['caller_id']}
  To: {call['destination']}
  State: {call['state']}
  Duration: {call['duration']}
  Started: {call['start_time']}
"""

            result += f"\nTotal Active Calls: {len(active_calls)}"
            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"Error getting active calls: {str(e)}")]

# 3. Hangup Call Tool
class HangupCallToolHandler(AsteriskToolHandler):
    def __init__(self):
        super().__init__("hangup_call")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Hangup a specific call by channel name",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel name to hangup (e.g., SIP/1001-00000001)"
                    },
                    "__credentials__": {
                        "type": "object",
                        "description": "Asterisk AMI credentials (optional for simulation)"
                    }
                },
                "required": ["channel"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            channel = args["channel"]
            
            result = f"""Call Terminated Successfully
==============================
Channel: {channel}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Reason: Administrative Hangup

The call on channel {channel} has been terminated."""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"Error hanging up call: {str(e)}")]

# 4. Get Call History Tool
class GetCallHistoryToolHandler(AsteriskToolHandler):
    def __init__(self):
        super().__init__("get_call_history")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Get call detail records (CDR) from Asterisk",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of records to return (default: 10)",
                        "default": 10
                    },
                    "extension": {
                        "type": "string",
                        "description": "Filter by specific extension (optional)"
                    },
                    "__credentials__": {
                        "type": "object",
                        "description": "Asterisk AMI credentials (optional for simulation)"
                    }
                }
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            limit = args.get("limit", 10)
            extension = args.get("extension")

            # Simulate call history
            call_records = [
                {
                    "date": "2024-07-04 14:23:45",
                    "src": "1001",
                    "dst": "1002",
                    "duration": "00:03:42",
                    "disposition": "ANSWERED",
                    "billsec": 222
                },
                {
                    "date": "2024-07-04 13:15:23",
                    "src": "1003",
                    "dst": "+1234567890",
                    "duration": "00:01:18",
                    "disposition": "ANSWERED",
                    "billsec": 78
                },
                {
                    "date": "2024-07-04 12:45:12",
                    "src": "1002",
                    "dst": "1001",
                    "duration": "00:00:00",
                    "disposition": "NO ANSWER",
                    "billsec": 0
                },
                {
                    "date": "2024-07-04 11:30:56",
                    "src": "1001",
                    "dst": "1003",
                    "duration": "00:05:23",
                    "disposition": "ANSWERED",
                    "billsec": 323
                }
            ]

            # Filter by extension if specified
            if extension:
                call_records = [r for r in call_records if r["src"] == extension or r["dst"] == extension]

            # Apply limit
            call_records = call_records[:limit]

            result = "Call Detail Records (CDR)\n" + "=" * 50 + "\n"
            if not call_records:
                result += "No call records found.\n"
            else:
                for i, record in enumerate(call_records, 1):
                    result += f"""
Record #{i}:
  Date/Time: {record['date']}
  From: {record['src']}
  To: {record['dst']}
  Duration: {record['duration']}
  Status: {record['disposition']}
  Bill Seconds: {record['billsec']}s
"""

            result += f"\nTotal Records: {len(call_records)}"
            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"Error getting call history: {str(e)}")]

# 5. List Extensions Tool
class ListExtensionsToolHandler(AsteriskToolHandler):
    def __init__(self):
        super().__init__("list_extensions")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="List all configured SIP extensions in Asterisk",
            inputSchema={
                "type": "object",
                "properties": {
                    "__credentials__": {
                        "type": "object",
                        "description": "Asterisk AMI credentials (optional for simulation)"
                    }
                }
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            # Simulate SIP extensions
            extensions = [
                {
                    "extension": "1001",
                    "name": "Alice Johnson",
                    "status": "Registered",
                    "ip": "192.168.1.101",
                    "port": "5060",
                    "user_agent": "Zoiper v5.4.6"
                },
                {
                    "extension": "1002", 
                    "name": "Bob Smith",
                    "status": "Registered",
                    "ip": "192.168.1.102",
                    "port": "5060",
                    "user_agent": "X-Lite 5.9.0"
                },
                {
                    "extension": "1003",
                    "name": "Charlie Brown",
                    "status": "Unregistered",
                    "ip": "N/A",
                    "port": "N/A",
                    "user_agent": "N/A"
                }
            ]

            result = "SIP Extensions\n" + "=" * 50 + "\n"
            for ext in extensions:
                result += f"""
Extension: {ext['extension']} ({ext['name']})
  Status: {ext['status']}
  IP Address: {ext['ip']}
  Port: {ext['port']}
  User Agent: {ext['user_agent']}
"""

            result += f"\nTotal Extensions: {len(extensions)}"
            registered = len([e for e in extensions if e['status'] == 'Registered'])
            result += f"\nRegistered: {registered}"
            result += f"\nUnregistered: {len(extensions) - registered}"

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"Error listing extensions: {str(e)}")]

# 6. Get Extension Status Tool
class GetExtensionStatusToolHandler(AsteriskToolHandler):
    def __init__(self):
        super().__init__("get_extension_status")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Get detailed status information for a specific extension",
            inputSchema={
                "type": "object",
                "properties": {
                    "extension": {
                        "type": "string",
                        "description": "Extension number to check"
                    },
                    "__credentials__": {
                        "type": "object",
                        "description": "Asterisk AMI credentials (optional for simulation)"
                    }
                },
                "required": ["extension"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            extension = args["extension"]

            # Simulate extension status lookup
            ext_status = {
                "1001": {
                    "name": "Alice Johnson",
                    "status": "Available",
                    "registered": True,
                    "ip": "192.168.1.101",
                    "last_seen": "2024-07-04 21:45:32",
                    "calls_today": 5,
                    "voicemails": 2,
                    "dnd": False
                },
                "1002": {
                    "name": "Bob Smith", 
                    "status": "Busy",
                    "registered": True,
                    "ip": "192.168.1.102",
                    "last_seen": "2024-07-04 21:44:15",
                    "calls_today": 8,
                    "voicemails": 0,
                    "dnd": True
                },
                "1003": {
                    "name": "Charlie Brown",
                    "status": "Unavailable",
                    "registered": False,
                    "ip": "N/A",
                    "last_seen": "2024-07-04 16:20:45",
                    "calls_today": 0,
                    "voicemails": 3,
                    "dnd": False
                }
            }.get(extension)

            if not ext_status:
                return [TextContent(type="text", text=f"Extension {extension} not found.")]

            result = f"""Extension Status: {extension}
{'=' * 40}
Name: {ext_status['name']}
Status: {ext_status['status']}
Registered: {'Yes' if ext_status['registered'] else 'No'}
IP Address: {ext_status['ip']}
Last Seen: {ext_status['last_seen']}
Calls Today: {ext_status['calls_today']}
Voicemails: {ext_status['voicemails']}
Do Not Disturb: {'Enabled' if ext_status['dnd'] else 'Disabled'}

Current State: {'Online and ' + ext_status['status'] if ext_status['registered'] else 'Offline'}"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"Error getting extension status: {str(e)}")]

# 7. Create Extension Tool
class CreateExtensionToolHandler(AsteriskToolHandler):
    def __init__(self):
        super().__init__("create_extension")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Create a new SIP extension in Asterisk",
            inputSchema={
                "type": "object",
                "properties": {
                    "extension": {
                        "type": "string",
                        "description": "Extension number to create"
                    },
                    "name": {
                        "type": "string", 
                        "description": "Display name for the extension"
                    },
                    "secret": {
                        "type": "string",
                        "description": "SIP password for the extension"
                    },
                    "context": {
                        "type": "string",
                        "description": "Dialplan context (default: internal)",
                        "default": "internal"
                    },
                    "__credentials__": {
                        "type": "object",
                        "description": "Asterisk AMI credentials (optional for simulation)"
                    }
                },
                "required": ["extension", "name", "secret"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            extension = args["extension"]
            name = args["name"]
            secret = args["secret"]
            context = args.get("context", "internal")

            # Simulate extension creation
            result = f"""Extension Created Successfully
===============================
Extension: {extension}
Name: {name}
Context: {context}
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SIP Configuration:
  Username: {extension}
  Password: {secret}
  Context: {context}
  Codec: ulaw,alaw,gsm
  Type: friend

The extension has been added to Asterisk configuration.
Please reload the SIP configuration for changes to take effect.

Registration Instructions:
  Server: <your-asterisk-server>
  Username: {extension}
  Password: {secret}
  Port: 5060"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"Error creating extension: {str(e)}")]

# 8. Get Voicemails Tool
class GetVoicemailsToolHandler(AsteriskToolHandler):
    def __init__(self):
        super().__init__("get_voicemails")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Get voicemail messages for an extension",
            inputSchema={
                "type": "object",
                "properties": {
                    "extension": {
                        "type": "string",
                        "description": "Extension number to check voicemails for"
                    },
                    "folder": {
                        "type": "string",
                        "enum": ["INBOX", "Old", "Work", "Family", "Friends"],
                        "description": "Voicemail folder (default: INBOX)",
                        "default": "INBOX"
                    },
                    "__credentials__": {
                        "type": "object",
                        "description": "Asterisk AMI credentials (optional for simulation)"
                    }
                },
                "required": ["extension"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            extension = args["extension"]
            folder = args.get("folder", "INBOX")

            # Simulate voicemail messages
            voicemails = {
                "1001": [
                    {
                        "id": "msg0001",
                        "from": "1002",
                        "date": "2024-07-04 15:30:22",
                        "duration": "00:01:23",
                        "new": True
                    },
                    {
                        "id": "msg0002",
                        "from": "+1234567890",
                        "date": "2024-07-04 12:15:45",
                        "duration": "00:02:10",
                        "new": False
                    }
                ],
                "1003": [
                    {
                        "id": "msg0003",
                        "from": "1001",
                        "date": "2024-07-04 09:22:11",
                        "duration": "00:00:45",
                        "new": True
                    }
                ]
            }.get(extension, [])

            result = f"Voicemails for Extension {extension} - {folder}\n" + "=" * 50 + "\n"
            
            if not voicemails:
                result += "No voicemail messages found.\n"
            else:
                new_count = len([vm for vm in voicemails if vm['new']])
                result += f"Total Messages: {len(voicemails)} ({new_count} new)\n\n"
                
                for i, vm in enumerate(voicemails, 1):
                    status = "NEW" if vm['new'] else "PLAYED"
                    result += f"""Message #{i} ({status}):
  From: {vm['from']}
  Date: {vm['date']}
  Duration: {vm['duration']}
  ID: {vm['id']}

"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"Error getting voicemails: {str(e)}")]

# 9. Play Audio File Tool
class PlayAudioFileToolHandler(AsteriskToolHandler):
    def __init__(self):
        super().__init__("play_audio_file")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Play an audio file to an extension or channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Extension number or channel to play audio to"
                    },
                    "audio_file": {
                        "type": "string",
                        "description": "Path to audio file or sound name"
                    },
                    "target_type": {
                        "type": "string",
                        "enum": ["extension", "channel"],
                        "description": "Type of target (extension or channel)",
                        "default": "extension"
                    },
                    "__credentials__": {
                        "type": "object",
                        "description": "Asterisk AMI credentials (optional for simulation)"
                    }
                },
                "required": ["target", "audio_file"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            target = args["target"]
            audio_file = args["audio_file"]
            target_type = args.get("target_type", "extension")

            # Simulate audio playback
            result = f"""Audio Playback Initiated
========================
Target: {target} ({target_type})
Audio File: {audio_file}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Status: Playing audio file to {target_type} {target}
Duration: Estimated 30 seconds

The audio file is now being played. The playback will complete automatically."""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"Error playing audio file: {str(e)}")]

# 10. Get Asterisk Status Tool
class GetAsteriskStatusToolHandler(AsteriskToolHandler):
    def __init__(self):
        super().__init__("get_asterisk_status")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Get comprehensive Asterisk system status and information",
            inputSchema={
                "type": "object",
                "properties": {
                    "__credentials__": {
                        "type": "object",
                        "description": "Asterisk AMI credentials (optional for simulation)"
                    }
                }
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            # Simulate comprehensive system status
            result = f"""Asterisk System Status
==================================================
System Health: ONLINE
Uptime: 2 days, 14 hours, 23 minutes
Version: Asterisk 18.20.0 (Simulated)
Built: Jul 4 2024

Connection Status:
  AMI Connected: Yes
  SIP Registry: Active
  IAX2 Registry: Active

Call Statistics:
  Active Calls: 2
  Calls Today: 47
  Total Call Minutes: 342
  Average Call Duration: 7.3 minutes

Extension Summary:
  Total Extensions: 3
  Registered: 2
  Unregistered: 1
  Busy: 1
  Available: 1

System Resources:
  CPU Usage: 12%
  Memory Usage: 45% (2.1GB / 4.0GB)
  Disk Usage: 23% (45GB / 200GB)
  Load Average: 0.34, 0.28, 0.31

Network Interfaces:
  eth0: 192.168.1.100 (UP)
  SIP Port 5060: Listening
  AMI Port 5038: Listening

Modules Loaded: 157
Codecs Available: ulaw, alaw, gsm, g722, g729, opus

Last Restart: 2024-07-02 07:15:32
Configuration Last Reload: 2024-07-04 14:20:18

Status: All systems operational"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"Error getting Asterisk status: {str(e)}")]

# Tool registry
tool_handlers: Dict[str, AsteriskToolHandler] = {}

def add_tool_handler(tool_class: AsteriskToolHandler):
    """Register a tool handler"""
    global tool_handlers
    tool_handlers[tool_class.name] = tool_class

def get_tool_handler(name: str) -> Optional[AsteriskToolHandler]:
    """Retrieve a tool handler by name"""
    return tool_handlers.get(name)

# Register all tool handlers
add_tool_handler(MakeCallToolHandler())
add_tool_handler(GetActiveCallsToolHandler())
add_tool_handler(HangupCallToolHandler())
add_tool_handler(GetCallHistoryToolHandler())
add_tool_handler(ListExtensionsToolHandler())
add_tool_handler(GetExtensionStatusToolHandler())
add_tool_handler(CreateExtensionToolHandler())
add_tool_handler(GetVoicemailsToolHandler())
add_tool_handler(PlayAudioFileToolHandler())
add_tool_handler(GetAsteriskStatusToolHandler())

@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List all available Asterisk tools"""
    return [th.get_tool_description() for th in tool_handlers.values()]

@app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls for Asterisk operations"""
    try:
        tool_handler = get_tool_handler(name)
        if not tool_handler:
            raise ValueError(f"Unknown tool: {name}")
        
        return tool_handler.run_tool(arguments)
        
    except Exception as e:
        logger.error(f"Error during call_tool: {str(e)}")
        logger.error(traceback.format_exc())
        return [TextContent(type="text", text=f"Error in {name}: {str(e)}")]

@app.list_resources()
async def handle_list_resources() -> List[types.Resource]:
    """List available resources"""
    return [
        types.Resource(
            uri="asterisk://operations",
            name="Asterisk PBX Operations",
            description="Available Asterisk telephony operations and capabilities",
            mimeType="text/plain"
        )
    ]

@app.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read resource content"""
    if uri == "asterisk://operations":
        operations = [
            "Call Management: Originate, monitor, and terminate calls",
            "Extension Management: List, create, and manage SIP extensions", 
            "System Monitoring: Get system status, call statistics, and health information",
            "Call History: Access call detail records (CDR) and analytics",
            "Voicemail: Manage and retrieve voicemail messages",
            "Audio Playback: Play audio files to extensions or channels",
            "Real-time Status: Monitor active calls and extension availability"
        ]
        return "\n".join(operations)
    else:
        raise ValueError(f"Unknown resource: {uri}")

async def main():
    """Main function to run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
