import logging
from collections.abc import Sequence
from typing import Any, Dict, List, Optional
import json
import traceback
import requests
import base64
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage, VideoMessage, AudioMessage, FileMessage,
    TextSendMessage, ImageSendMessage, VideoSendMessage, AudioSendMessage,
    TemplateSendMessage, ButtonsTemplate, ConfirmTemplate, CarouselTemplate, CarouselColumn,
    PostbackAction, MessageAction, URIAction,
    QuickReply, QuickReplyButton,
    FlexSendMessage, BubbleContainer, BoxComponent, TextComponent, ButtonComponent,
    RichMenu, RichMenuSize, RichMenuArea, RichMenuBounds
)

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
logger = logging.getLogger("line-mcp")

# MCP server instance
app = Server("line-mcp")

# Global variables for LINE Bot API
line_bot_api = None
handler = None

# Tool handler base class
class LineToolHandler:
    def __init__(self, name: str):
        self.name = name

    def get_tool_description(self) -> Tool:
        raise NotImplementedError()

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        raise NotImplementedError()

# Initialize LINE Bot API
def initialize_line_bot(credentials: dict):
    """Initialize LINE Bot API with credentials"""
    global line_bot_api, handler
    try:
        channel_access_token = credentials.get("channel_access_token")
        channel_secret = credentials.get("channel_secret")
        
        if not channel_access_token or not channel_secret:
            raise ValueError("Missing LINE credentials: channel_access_token and channel_secret required")
        
        line_bot_api = LineBotApi(channel_access_token)
        # Only initialize webhook handler if channel_secret is provided
        # Webhook handler is optional for one-way messaging
        if channel_secret:
            handler = WebhookHandler(channel_secret)
        
        logger.info("LINE Bot API initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize LINE Bot API: {str(e)}")
        return False

# Send Text Message Tool
class SendTextMessageToolHandler(LineToolHandler):
    def __init__(self):
        super().__init__("send_text_message")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Send a text message via LINE Messenger",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "User ID or Group ID to send message to"
                    },
                    "message": {
                        "type": "string",
                        "description": "Text message content to send"
                    },
                    "quick_replies": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "label": {"type": "string"},
                                "text": {"type": "string"}
                            }
                        },
                        "description": "Optional quick reply buttons"
                    },
                    "__credentials__": {
                        "type": "object",
                        "description": "LINE Bot credentials"
                    }
                },
                "required": ["to", "message"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            if not initialize_line_bot(credentials):
                return [TextContent(type="text", text="Error: Failed to initialize LINE Bot API")]

            to = args["to"]
            message_text = args["message"]
            quick_replies_data = args.get("quick_replies", [])

            # Create quick replies if provided
            quick_reply = None
            if quick_replies_data:
                quick_reply_buttons = []
                for qr in quick_replies_data:
                    quick_reply_buttons.append(
                        QuickReplyButton(action=MessageAction(label=qr["label"], text=qr["text"]))
                    )
                quick_reply = QuickReply(items=quick_reply_buttons)

            # Send message
            message = TextSendMessage(text=message_text, quick_reply=quick_reply)
            line_bot_api.push_message(to, message)

            return [TextContent(type="text", text=f"Text message sent successfully to {to}")]

        except LineBotApiError as e:
            return [TextContent(type="text", text=f"LINE API Error: {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error sending text message: {str(e)}")]

# Send Rich Message Tool
class SendRichMessageToolHandler(LineToolHandler):
    def __init__(self):
        super().__init__("send_rich_message")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Send rich content (buttons, carousels, confirmations) via LINE",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "User ID or Group ID to send message to"
                    },
                    "template_type": {
                        "type": "string",
                        "enum": ["buttons", "confirm", "carousel"],
                        "description": "Type of rich message template"
                    },
                    "content": {
                        "type": "object",
                        "description": "Rich message content configuration"
                    },
                    "__credentials__": {
                        "type": "object",
                        "description": "LINE Bot credentials"
                    }
                },
                "required": ["to", "template_type", "content"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            if not initialize_line_bot(credentials):
                return [TextContent(type="text", text="Error: Failed to initialize LINE Bot API")]

            to = args["to"]
            template_type = args["template_type"]
            content = args["content"]

            template = None

            if template_type == "buttons":
                actions = []
                for action in content.get("actions", []):
                    if action["type"] == "message":
                        actions.append(MessageAction(label=action["label"], text=action["text"]))
                    elif action["type"] == "uri":
                        actions.append(URIAction(label=action["label"], uri=action["uri"]))
                    elif action["type"] == "postback":
                        actions.append(PostbackAction(label=action["label"], data=action["data"]))

                template = ButtonsTemplate(
                    thumbnail_image_url=content.get("thumbnail_image_url"),
                    title=content.get("title"),
                    text=content["text"],
                    actions=actions
                )

            elif template_type == "confirm":
                actions = []
                for action in content["actions"]:
                    if action["type"] == "message":
                        actions.append(MessageAction(label=action["label"], text=action["text"]))
                    elif action["type"] == "postback":
                        actions.append(PostbackAction(label=action["label"], data=action["data"]))

                template = ConfirmTemplate(
                    text=content["text"],
                    actions=actions
                )

            elif template_type == "carousel":
                columns = []
                for col in content["columns"]:
                    actions = []
                    for action in col.get("actions", []):
                        if action["type"] == "message":
                            actions.append(MessageAction(label=action["label"], text=action["text"]))
                        elif action["type"] == "uri":
                            actions.append(URIAction(label=action["label"], uri=action["uri"]))
                        elif action["type"] == "postback":
                            actions.append(PostbackAction(label=action["label"], data=action["data"]))

                    columns.append(CarouselColumn(
                        thumbnail_image_url=col.get("thumbnail_image_url"),
                        title=col.get("title"),
                        text=col["text"],
                        actions=actions
                    ))

                template = CarouselTemplate(columns=columns)

            if template:
                message = TemplateSendMessage(alt_text=content.get("alt_text", "Rich message"), template=template)
                line_bot_api.push_message(to, message)
                return [TextContent(type="text", text=f"Rich message ({template_type}) sent successfully to {to}")]

            return [TextContent(type="text", text=f"Unsupported template type: {template_type}")]

        except LineBotApiError as e:
            return [TextContent(type="text", text=f"LINE API Error: {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error sending rich message: {str(e)}")]

# Send Image Message Tool
class SendImageMessageToolHandler(LineToolHandler):
    def __init__(self):
        super().__init__("send_image_message")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Send an image message via LINE Messenger",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "User ID or Group ID to send image to"
                    },
                    "original_content_url": {
                        "type": "string",
                        "description": "URL of the original image"
                    },
                    "preview_image_url": {
                        "type": "string",
                        "description": "URL of the preview image (optional, defaults to original)"
                    },
                    "__credentials__": {
                        "type": "object",
                        "description": "LINE Bot credentials"
                    }
                },
                "required": ["to", "original_content_url"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            if not initialize_line_bot(credentials):
                return [TextContent(type="text", text="Error: Failed to initialize LINE Bot API")]

            to = args["to"]
            original_content_url = args["original_content_url"]
            preview_image_url = args.get("preview_image_url", original_content_url)

            message = ImageSendMessage(
                original_content_url=original_content_url,
                preview_image_url=preview_image_url
            )
            
            line_bot_api.push_message(to, message)
            return [TextContent(type="text", text=f"Image message sent successfully to {to}")]

        except LineBotApiError as e:
            return [TextContent(type="text", text=f"LINE API Error: {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error sending image message: {str(e)}")]

# Get User Profile Tool
class GetUserProfileToolHandler(LineToolHandler):
    def __init__(self):
        super().__init__("get_user_profile")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Get user profile information from LINE",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "LINE User ID to get profile for"
                    },
                    "__credentials__": {
                        "type": "object",
                        "description": "LINE Bot credentials"
                    }
                },
                "required": ["user_id"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            if not initialize_line_bot(credentials):
                return [TextContent(type="text", text="Error: Failed to initialize LINE Bot API")]

            user_id = args["user_id"]
            profile = line_bot_api.get_profile(user_id)

            profile_info = {
                "display_name": profile.display_name,
                "user_id": profile.user_id,
                "picture_url": profile.picture_url,
                "status_message": profile.status_message
            }

            return [TextContent(type="text", text=f"User Profile: {json.dumps(profile_info, indent=2)}")]

        except LineBotApiError as e:
            return [TextContent(type="text", text=f"LINE API Error: {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting user profile: {str(e)}")]

# Get Group Summary Tool
class GetGroupSummaryToolHandler(LineToolHandler):
    def __init__(self):
        super().__init__("get_group_summary")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Get group summary information from LINE",
            inputSchema={
                "type": "object",
                "properties": {
                    "group_id": {
                        "type": "string",
                        "description": "LINE Group ID to get summary for"
                    },
                    "__credentials__": {
                        "type": "object",
                        "description": "LINE Bot credentials"
                    }
                },
                "required": ["group_id"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            if not initialize_line_bot(credentials):
                return [TextContent(type="text", text="Error: Failed to initialize LINE Bot API")]

            group_id = args["group_id"]
            group_summary = line_bot_api.get_group_summary(group_id)

            summary_info = {
                "group_id": group_summary.group_id,
                "group_name": group_summary.group_name,
                "picture_url": group_summary.picture_url
            }

            return [TextContent(type="text", text=f"Group Summary: {json.dumps(summary_info, indent=2)}")]

        except LineBotApiError as e:
            return [TextContent(type="text", text=f"LINE API Error: {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting group summary: {str(e)}")]

# Send Flex Message Tool
class SendFlexMessageToolHandler(LineToolHandler):
    def __init__(self):
        super().__init__("send_flex_message")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Send a flex message (custom layout) via LINE",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "User ID or Group ID to send flex message to"
                    },
                    "alt_text": {
                        "type": "string",
                        "description": "Alternative text for the flex message"
                    },
                    "flex_content": {
                        "type": "object",
                        "description": "Flex message content structure"
                    },
                    "__credentials__": {
                        "type": "object",
                        "description": "LINE Bot credentials"
                    }
                },
                "required": ["to", "alt_text", "flex_content"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            if not initialize_line_bot(credentials):
                return [TextContent(type="text", text="Error: Failed to initialize LINE Bot API")]

            to = args["to"]
            alt_text = args["alt_text"]
            flex_content = args["flex_content"]

            # Create a simple bubble flex message
            if flex_content.get("type") == "simple_card":
                content = flex_content["content"]
                bubble = BubbleContainer(
                    body=BoxComponent(
                        layout="vertical",
                        contents=[
                            TextComponent(text=content["title"], weight="bold", size="xl"),
                            TextComponent(text=content["description"], wrap=True),
                        ]
                    )
                )
                
                if content.get("actions"):
                    footer_buttons = []
                    for action in content["actions"]:
                        if action["type"] == "uri":
                            footer_buttons.append(
                                ButtonComponent(action=URIAction(label=action["label"], uri=action["uri"]))
                            )
                        elif action["type"] == "message":
                            footer_buttons.append(
                                ButtonComponent(action=MessageAction(label=action["label"], text=action["text"]))
                            )
                    
                    bubble.footer = BoxComponent(
                        layout="vertical",
                        contents=footer_buttons,
                        spacing="sm"
                    )

                message = FlexSendMessage(alt_text=alt_text, contents=bubble)
                line_bot_api.push_message(to, message)
                return [TextContent(type="text", text=f"Flex message sent successfully to {to}")]

            return [TextContent(type="text", text="Unsupported flex message type")]

        except LineBotApiError as e:
            return [TextContent(type="text", text=f"LINE API Error: {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error sending flex message: {str(e)}")]

# Broadcast Message Tool
class BroadcastMessageToolHandler(LineToolHandler):
    def __init__(self):
        super().__init__("broadcast_message")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Broadcast a message to all friends of the LINE bot",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Text message to broadcast"
                    },
                    "__credentials__": {
                        "type": "object",
                        "description": "LINE Bot credentials"
                    }
                },
                "required": ["message"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            if not initialize_line_bot(credentials):
                return [TextContent(type="text", text="Error: Failed to initialize LINE Bot API")]

            message_text = args["message"]
            message = TextSendMessage(text=message_text)
            
            line_bot_api.broadcast(message)
            return [TextContent(type="text", text="Message broadcast successfully to all friends")]

        except LineBotApiError as e:
            return [TextContent(type="text", text=f"LINE API Error: {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error broadcasting message: {str(e)}")]

# Webhook Event Handler Tool
class WebhookEventHandlerToolHandler(LineToolHandler):
    def __init__(self):
        super().__init__("handle_webhook_event")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Handle incoming webhook events from LINE platform",
            inputSchema={
                "type": "object",
                "properties": {
                    "webhook_data": {
                        "type": "object",
                        "description": "Raw webhook event data from LINE"
                    },
                    "signature": {
                        "type": "string",
                        "description": "X-Line-Signature header for verification"
                    },
                    "__credentials__": {
                        "type": "object",
                        "description": "LINE Bot credentials"
                    }
                },
                "required": ["webhook_data"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            if not initialize_line_bot(credentials):
                return [TextContent(type="text", text="Error: Failed to initialize LINE Bot API")]

            webhook_data = args["webhook_data"]
            signature = args.get("signature", "")

            # Process webhook events
            events = webhook_data.get("events", [])
            processed_events = []

            for event in events:
                event_type = event.get("type", "unknown")
                
                if event_type == "message":
                    message_type = event.get("message", {}).get("type", "unknown")
                    user_id = event.get("source", {}).get("userId", "unknown")
                    message_text = event.get("message", {}).get("text", "")
                    
                    processed_events.append({
                        "type": "message",
                        "message_type": message_type,
                        "user_id": user_id,
                        "text": message_text,
                        "timestamp": event.get("timestamp")
                    })
                
                elif event_type == "follow":
                    user_id = event.get("source", {}).get("userId", "unknown")
                    processed_events.append({
                        "type": "follow",
                        "user_id": user_id,
                        "timestamp": event.get("timestamp")
                    })
                
                elif event_type == "unfollow":
                    user_id = event.get("source", {}).get("userId", "unknown")
                    processed_events.append({
                        "type": "unfollow", 
                        "user_id": user_id,
                        "timestamp": event.get("timestamp")
                    })

            return [TextContent(type="text", text=f"Processed {len(processed_events)} webhook events: {json.dumps(processed_events, indent=2)}")]

        except Exception as e:
            return [TextContent(type="text", text=f"Error handling webhook event: {str(e)}")]

# Rich Menu Management Tool
class RichMenuToolHandler(LineToolHandler):
    def __init__(self):
        super().__init__("manage_rich_menu")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Create and manage LINE Rich Menus for enhanced user interaction",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "delete", "set_default", "link_to_user"],
                        "description": "Rich menu action to perform"
                    },
                    "rich_menu_data": {
                        "type": "object",
                        "description": "Rich menu configuration data"
                    },
                    "rich_menu_id": {
                        "type": "string",
                        "description": "Rich menu ID for delete/set operations"
                    },
                    "user_id": {
                        "type": "string", 
                        "description": "User ID for linking rich menu"
                    },
                    "__credentials__": {
                        "type": "object",
                        "description": "LINE Bot credentials"
                    }
                },
                "required": ["action"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            if not initialize_line_bot(credentials):
                return [TextContent(type="text", text="Error: Failed to initialize LINE Bot API")]

            action = args["action"]

            if action == "create":
                rich_menu_data = args.get("rich_menu_data", {})
                
                # Create a basic rich menu structure
                rich_menu = RichMenu(
                    size=RichMenuSize(width=2500, height=1686),
                    selected=False,
                    name=rich_menu_data.get("name", "Default Rich Menu"),
                    chat_bar_text=rich_menu_data.get("chat_bar_text", "Menu"),
                    areas=[
                        RichMenuArea(
                            bounds=RichMenuBounds(x=0, y=0, width=1250, height=1686),
                            action=MessageAction(text="Option 1")
                        ),
                        RichMenuArea(
                            bounds=RichMenuBounds(x=1250, y=0, width=1250, height=1686),
                            action=MessageAction(text="Option 2")
                        )
                    ]
                )
                
                rich_menu_id = line_bot_api.create_rich_menu(rich_menu)
                return [TextContent(type="text", text=f"Rich menu created with ID: {rich_menu_id}")]

            elif action == "delete":
                rich_menu_id = args.get("rich_menu_id")
                if not rich_menu_id:
                    return [TextContent(type="text", text="Error: rich_menu_id required for delete action")]
                
                line_bot_api.delete_rich_menu(rich_menu_id)
                return [TextContent(type="text", text=f"Rich menu {rich_menu_id} deleted successfully")]

            elif action == "set_default":
                rich_menu_id = args.get("rich_menu_id")
                if not rich_menu_id:
                    return [TextContent(type="text", text="Error: rich_menu_id required for set_default action")]
                
                line_bot_api.set_default_rich_menu(rich_menu_id)
                return [TextContent(type="text", text=f"Rich menu {rich_menu_id} set as default")]

            elif action == "link_to_user":
                rich_menu_id = args.get("rich_menu_id")
                user_id = args.get("user_id")
                if not rich_menu_id or not user_id:
                    return [TextContent(type="text", text="Error: rich_menu_id and user_id required for link_to_user action")]
                
                line_bot_api.link_rich_menu_to_user(user_id, rich_menu_id)
                return [TextContent(type="text", text=f"Rich menu {rich_menu_id} linked to user {user_id}")]

            return [TextContent(type="text", text=f"Unknown rich menu action: {action}")]

        except LineBotApiError as e:
            return [TextContent(type="text", text=f"LINE API Error: {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error managing rich menu: {str(e)}")]

# Group Member Management Tool
class GroupMemberToolHandler(LineToolHandler):
    def __init__(self):
        super().__init__("manage_group_members")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Manage LINE group members and get group member information",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["get_member_profile", "get_member_ids", "leave_group"],
                        "description": "Group member action to perform"
                    },
                    "group_id": {
                        "type": "string",
                        "description": "LINE Group ID"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User ID for getting member profile"
                    },
                    "__credentials__": {
                        "type": "object",
                        "description": "LINE Bot credentials"
                    }
                },
                "required": ["action", "group_id"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            if not initialize_line_bot(credentials):
                return [TextContent(type="text", text="Error: Failed to initialize LINE Bot API")]

            action = args["action"]
            group_id = args["group_id"]

            if action == "get_member_profile":
                user_id = args.get("user_id")
                if not user_id:
                    return [TextContent(type="text", text="Error: user_id required for get_member_profile action")]
                
                profile = line_bot_api.get_group_member_profile(group_id, user_id)
                profile_info = {
                    "display_name": profile.display_name,
                    "user_id": profile.user_id,
                    "picture_url": profile.picture_url
                }
                return [TextContent(type="text", text=f"Group Member Profile: {json.dumps(profile_info, indent=2)}")]

            elif action == "get_member_ids":
                member_ids = line_bot_api.get_group_member_ids(group_id)
                return [TextContent(type="text", text=f"Group Member IDs: {json.dumps(member_ids.member_ids, indent=2)}")]

            elif action == "leave_group":
                line_bot_api.leave_group(group_id)
                return [TextContent(type="text", text=f"Successfully left group {group_id}")]

            return [TextContent(type="text", text=f"Unknown group member action: {action}")]

        except LineBotApiError as e:
            return [TextContent(type="text", text=f"LINE API Error: {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error managing group members: {str(e)}")]

# Tool registry
tool_handlers: Dict[str, LineToolHandler] = {}

def add_tool_handler(tool_class: LineToolHandler):
    """Register a tool handler"""
    global tool_handlers
    tool_handlers[tool_class.name] = tool_class

def get_tool_handler(name: str) -> Optional[LineToolHandler]:
    """Retrieve a tool handler by name"""
    return tool_handlers.get(name)

# Register all tool handlers
add_tool_handler(SendTextMessageToolHandler())
add_tool_handler(SendRichMessageToolHandler())
add_tool_handler(SendImageMessageToolHandler())
add_tool_handler(GetUserProfileToolHandler())
add_tool_handler(GetGroupSummaryToolHandler())
add_tool_handler(SendFlexMessageToolHandler())
add_tool_handler(BroadcastMessageToolHandler())
add_tool_handler(WebhookEventHandlerToolHandler())
add_tool_handler(RichMenuToolHandler())
add_tool_handler(GroupMemberToolHandler())

@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List all available LINE tools"""
    return [th.get_tool_description() for th in tool_handlers.values()]

@app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls for LINE operations"""
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
            uri="line://operations",
            name="LINE Messenger Operations",
            description="Available LINE Messenger operations and capabilities",
            mimeType="text/plain"
        )
    ]

@app.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read resource content"""
    if uri == "line://operations":
        operations = [
            "Messaging: Send text, rich content, images, and broadcast messages",
            "User Management: Get user profiles and group information", 
            "Rich Content: Send buttons, carousels, confirmations, and flex messages",
            "Interactive Features: Quick replies, postback actions, and URI actions",
            "Broadcasting: Send messages to all bot friends",
            "Group Operations: Get group summaries and manage group interactions"
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
