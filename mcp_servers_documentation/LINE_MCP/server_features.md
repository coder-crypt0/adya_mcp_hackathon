# LINE MCP Server Features

## Overview
The LINE MCP Server provides comprehensive LINE Messenger integration capabilities, allowing AI assistants to send messages, manage rich content, and interact with users through LINE's messaging platform.

## Available Tools

### 1. send_text_message
**Description**: Send a text message via LINE Messenger
**Parameters**:
- `to` (required): User ID or Group ID to send message to
- `message` (required): Text message content to send
- `quick_replies` (optional): Array of quick reply buttons with label and text

**Example Usage**:
```json
{
  "to": "U1234567890",
  "message": "Hello from LINE MCP Server!",
  "quick_replies": [
    {"label": "Yes", "text": "Yes, I agree"},
    {"label": "No", "text": "No, I disagree"}
  ]
}
```

### 2. send_rich_message
**Description**: Send rich content (buttons, carousels, confirmations) via LINE
**Parameters**:
- `to` (required): User ID or Group ID to send message to
- `template_type` (required): Type of template ("buttons", "confirm", "carousel")
- `content` (required): Rich message content configuration

**Example Usage - Buttons Template**:
```json
{
  "to": "U1234567890",
  "template_type": "buttons",
  "content": {
    "title": "Choose an Option",
    "text": "What would you like to do?",
    "actions": [
      {"type": "message", "label": "View Profile", "text": "Show my profile"},
      {"type": "uri", "label": "Visit Website", "uri": "https://example.com"},
      {"type": "postback", "label": "Get Help", "data": "help_request"}
    ]
  }
}
```

**Example Usage - Carousel Template**:
```json
{
  "to": "U1234567890",
  "template_type": "carousel",
  "content": {
    "columns": [
      {
        "title": "Math Helper",
        "text": "Get mathematical calculations",
        "actions": [{"type": "message", "label": "Calculate", "text": "Start calculation"}]
      },
      {
        "title": "Email Assistant", 
        "text": "Manage your emails",
        "actions": [{"type": "message", "label": "Check Emails", "text": "Show recent emails"}]
      }
    ]
  }
}
```

### 3. send_image_message
**Description**: Send an image message via LINE Messenger
**Parameters**:
- `to` (required): User ID or Group ID to send image to
- `original_content_url` (required): URL of the original image
- `preview_image_url` (optional): URL of the preview image

**Example Usage**:
```json
{
  "to": "U1234567890",
  "original_content_url": "https://example.com/image.jpg",
  "preview_image_url": "https://example.com/preview.jpg"
}
```

### 4. get_user_profile
**Description**: Get user profile information from LINE
**Parameters**:
- `user_id` (required): LINE User ID to get profile for

**Example Usage**:
```json
{
  "user_id": "U1234567890"
}
```

**Response**:
```json
{
  "display_name": "John Doe",
  "user_id": "U1234567890", 
  "picture_url": "https://profile.line-scdn.net/...",
  "status_message": "Hello World!"
}
```

### 5. get_group_summary
**Description**: Get group summary information from LINE
**Parameters**:
- `group_id` (required): LINE Group ID to get summary for

**Example Usage**:
```json
{
  "group_id": "G1234567890"
}
```

### 6. send_flex_message
**Description**: Send a flex message (custom layout) via LINE
**Parameters**:
- `to` (required): User ID or Group ID to send flex message to
- `alt_text` (required): Alternative text for the flex message
- `flex_content` (required): Flex message content structure

**Example Usage**:
```json
{
  "to": "U1234567890",
  "alt_text": "Service Card",
  "flex_content": {
    "type": "simple_card",
    "content": {
      "title": "Our Services",
      "description": "Choose from our available services",
      "actions": [
        {"type": "uri", "label": "Learn More", "uri": "https://example.com"},
        {"type": "message", "label": "Contact Us", "text": "I want to contact support"}
      ]
    }
  }
}
```

### 7. broadcast_message
**Description**: Broadcast a message to all friends of the LINE bot
**Parameters**:
- `message` (required): Text message to broadcast

**Example Usage**:
```json
{
  "message": "Welcome to our new LINE service! We're excited to help you."
}
```

## Credentials Configuration

The LINE MCP server requires the following credentials:

```json
{
  "LINE_MCP": {
    "channel_access_token": "your_line_channel_access_token",
    "channel_secret": "your_line_channel_secret",
    "webhook_url": "your_webhook_endpoint_url"
  }
}
```

### How to Get LINE Credentials:

1. **Create a LINE Developers Account**:
   - Go to https://developers.line.biz/
   - Sign in with your LINE account

2. **Create a New Provider**:
   - Click "Create a new provider"
   - Enter provider name and confirm

3. **Create a Messaging API Channel**:
   - Click "Create a Messaging API channel"
   - Fill in the required information
   - Agree to terms and create

4. **Get Your Credentials**:
   - **Channel Access Token**: Go to "Messaging API" tab → "Channel access token" → Issue/Copy
   - **Channel Secret**: Go to "Basic settings" tab → "Channel secret"
   - **Webhook URL**: Your server endpoint for receiving webhooks

## Integration Examples

### Mathematical Assistant with LINE Notifications
```python
# User asks for matrix calculation via LINE
# 1. NUMPY_MCP calculates eigenvalues
# 2. LINE_MCP sends formatted results back to user

{
  "selected_servers": ["NUMPY_MCP", "LINE_MCP"],
  "input": "Calculate eigenvalues of [[4,2],[1,3]] and send results to user U1234567890"
}
```

### Email + LINE Workflow
```python
# Check emails and notify via LINE
# 1. MCP-GSUITE fetches recent emails  
# 2. LINE_MCP sends summary to user

{
  "selected_servers": ["MCP-GSUITE", "LINE_MCP"],
  "input": "Check my recent emails and send a summary to LINE user U1234567890"
}
```

### Interactive LINE Menu
```python
# Send interactive menu combining all services
{
  "template_type": "carousel",
  "content": {
    "columns": [
      {
        "title": "📊 Math Helper",
        "text": "Advanced calculations with NumPy",
        "actions": [{"type": "message", "label": "Calculate Matrix", "text": "Show matrix tools"}]
      },
      {
        "title": "📧 Email Manager", 
        "text": "Gmail integration powered by Google",
        "actions": [{"type": "message", "label": "Check Emails", "text": "Show recent emails"}]
      },
      {
        "title": "💬 LINE Assistant",
        "text": "Rich messaging and notifications",
        "actions": [{"type": "message", "label": "Send Message", "text": "Compose new message"}]
      }
    ]
  }
}
```

## Advanced Features

### Rich Menu Support
The server supports creating and managing LINE Rich Menus for enhanced user experience.

### Webhook Integration
Configure webhooks to receive real-time messages and events from LINE users.

### Multi-format Messaging
- Text messages with quick replies
- Image and media messages
- Interactive buttons and carousels
- Custom flex messages for complex layouts
- Confirmation dialogs

### Broadcasting
Send messages to all bot friends simultaneously for announcements and updates.

## Error Handling

The server provides detailed error messages for:
- Invalid credentials
- Missing required parameters
- LINE API errors
- Network connectivity issues
- User permission errors

## Security Considerations

- All credentials are passed securely through the MCP protocol
- Channel secrets are used for webhook signature verification
- Access tokens have configurable expiration times
- Support for IP whitelisting in LINE Developer Console

## Rate Limits

LINE API has the following rate limits:
- **Push Messages**: 500 requests per second
- **Broadcast Messages**: Limited by your plan
- **Profile API**: 1,000 requests per second

The server automatically handles rate limiting and provides appropriate error messages.
