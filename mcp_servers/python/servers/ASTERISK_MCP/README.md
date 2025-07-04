# Asterisk MCP Server

A Model Context Protocol (MCP) server for Asterisk PBX telephony operations.

## Features

This MCP server provides 10 comprehensive telephony tools:

### Call Management (4 tools)
- **make_call** - Originate calls between extensions
- **get_active_calls** - List currently active calls
- **hangup_call** - Terminate specific calls by channel
- **get_call_history** - View call detail records (CDR)

### Extension Management (3 tools)
- **list_extensions** - Show all configured SIP extensions
- **get_extension_status** - Check detailed extension status
- **create_extension** - Add new SIP extensions

### Advanced Features (3 tools)
- **get_voicemails** - List voicemail messages for extensions
- **play_audio_file** - Play audio files to extensions or channels
- **get_asterisk_status** - Get comprehensive system status

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the MCP server:
```bash
python mcp_asterisk.py
```

## Configuration

The server runs in simulation mode by default, providing realistic telephony data without requiring an actual Asterisk installation. 

For production use with real Asterisk:
- Modify the `initialize_asterisk_ami()` function to connect to your Asterisk AMI
- Update credentials handling in the tool handlers
- Configure your Asterisk server with AMI access

## Demo Data

The simulation includes:
- **Extensions**: 1001 (Alice Johnson), 1002 (Bob Smith), 1003 (Charlie Brown)
- **Active Calls**: Sample ongoing conversations
- **Call History**: Recent call records with various dispositions
- **Voicemails**: Sample messages in different folders
- **System Status**: Comprehensive Asterisk health information

## Usage Examples

### Make a Call
```json
{
  "from_extension": "1001",
  "to_extension": "1002",
  "context": "internal"
}
```

### Get Extension Status
```json
{
  "extension": "1001"
}
```

### List Voicemails
```json
{
  "extension": "1001",
  "folder": "INBOX"
}
```

## Integration

This server follows the standard MCP protocol and can be integrated with:
- MCP-compatible clients
- AI assistants and chatbots
- Telephony management interfaces
- Call center applications

## License

MIT License - See LICENSE file for details.
