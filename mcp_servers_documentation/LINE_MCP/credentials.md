# LINE MCP Server Credentials Setup

## Prerequisites

Before setting up the LINE MCP server, you need:

1. A LINE account
2. Access to LINE Developers Console
3. A valid webhook endpoint (for receiving messages)

## Step-by-Step Setup

### 1. Create LINE Developers Account

1. Go to [LINE Developers Console](https://developers.line.biz/)
2. Click "Log in" and sign in with your LINE account
3. If you don't have a LINE account, create one first at [LINE](https://line.me/)

### 2. Create a Provider

1. After logging in, click "Create a new provider"
2. Enter your provider name (e.g., "My Company Bot")
3. Click "Create"

### 3. Create a Messaging API Channel

1. Click "Create a Messaging API channel"
2. Fill in the required information:
   - **Channel name**: Your bot's name (e.g., "MCP Assistant Bot")
   - **Channel description**: Description of your bot's purpose
   - **Category**: Select appropriate category (e.g., "Business")
   - **Subcategory**: Select appropriate subcategory
   - **Email address**: Your contact email
3. Upload channel icon (optional but recommended)
4. Agree to the terms and conditions
5. Click "Create"

### 4. Configure Channel Settings

1. Go to the "Messaging API" tab
2. **Enable webhook**: Turn this ON
3. **Webhook URL**: Enter your webhook endpoint (e.g., `https://yourdomain.com/webhook`)
4. **Use webhook**: Turn this ON
5. **Auto-reply messages**: Turn this OFF (unless you want automatic replies)
6. **Greeting messages**: Configure as needed

### 5. Get Your Credentials

#### Channel Access Token
1. Go to "Messaging API" tab
2. Scroll down to "Channel access token"
3. Click "Issue" to generate a new token
4. Copy the token and save it securely
5. **Important**: This token is used to authenticate your bot's API calls

#### Channel Secret
1. Go to "Basic settings" tab
2. Find "Channel secret" section
3. Copy the channel secret
4. **Important**: This is used to verify webhook signatures

#### Webhook URL
1. This is your server endpoint that will receive LINE webhook events
2. Must be HTTPS (HTTP not allowed for production)
3. Should respond to POST requests from LINE

## Credentials Configuration

Add the following credentials to your MCP client configuration:

```json
{
  "selected_server_credentials": {
    "LINE_MCP": {
      "channel_access_token": "YOUR_CHANNEL_ACCESS_TOKEN_HERE",
      "channel_secret": "YOUR_CHANNEL_SECRET_HERE", 
      "webhook_url": "https://yourdomain.com/webhook"
    }
  }
}
```

### Example Configuration in Postman

```json
{
  "selected_server_credentials": {
    "LINE_MCP": {
      "channel_access_token": "abcdef123456789...",
      "channel_secret": "1234567890abcdef...",
      "webhook_url": "https://mybot.example.com/line/webhook"
    }
  },
  "client_details": {
    "api_key": "your_llm_api_key",
    "temperature": 0.1,
    "max_token": 20000,
    "input": "Send a welcome message to user U1234567890",
    "input_type": "text", 
    "prompt": "you are a helpful LINE messaging assistant",
    "chat_model": "gemini-2.0-flash",
    "chat_history": []
  },
  "selected_client": "MCP_CLIENT_GEMINI",
  "selected_servers": ["LINE_MCP"]
}
```

## Testing Your Setup

### 1. Add Your Bot as Friend

1. Go to "Messaging API" tab in LINE Developers Console
2. Find "QR code" section
3. Scan the QR code with your LINE app to add the bot as friend
4. Or use the "Basic ID" or "LINE ID" to search and add

### 2. Get User/Group IDs

To send messages, you need the recipient's User ID or Group ID:

**For User ID**:
- Send a message to your bot from a LINE account
- Check your webhook logs to see the user ID in the webhook payload
- User IDs start with "U" (e.g., "U1234567890abcdef")

**For Group ID**:
- Add your bot to a LINE group
- Send a message in the group
- Check webhook logs for the group ID
- Group IDs start with "G" (e.g., "G1234567890abcdef")

### 3. Test API Calls

Use the provided Postman collection to test:

1. **Send Text Message**: Test basic text messaging
2. **Send Rich Message**: Test buttons and carousels  
3. **Get User Profile**: Test user information retrieval
4. **Broadcast Message**: Test broadcasting to all friends

## Security Best Practices

### 1. Protect Your Credentials
- Never commit credentials to version control
- Use environment variables or secure configuration files
- Rotate tokens periodically

### 2. Webhook Security
- Verify webhook signatures using channel secret
- Use HTTPS for all webhook endpoints
- Implement proper error handling

### 3. Rate Limiting
- Implement rate limiting to avoid hitting LINE API limits
- Monitor API usage in LINE Developers Console
- Handle rate limit errors gracefully

## Troubleshooting Common Issues

### Invalid Credentials Error
- Verify channel access token is correct and not expired
- Check if channel secret matches
- Ensure credentials are properly formatted in configuration

### Webhook Not Receiving Events  
- Verify webhook URL is accessible from internet
- Check if webhook URL is HTTPS
- Ensure webhook is enabled in channel settings

### Permission Denied
- Check if bot has necessary permissions
- Verify the bot is friends with target users
- For groups, ensure bot is added to the group

### Message Sending Failures
- Verify recipient User/Group ID is correct
- Check if user has blocked the bot
- Ensure message content follows LINE guidelines

## Additional Resources

- [LINE Developers Documentation](https://developers.line.biz/en/docs/)
- [Messaging API Reference](https://developers.line.biz/en/reference/messaging-api/)
- [Webhook Events Reference](https://developers.line.biz/en/reference/messaging-api/#webhook-event-objects)
- [Rich Message Examples](https://developers.line.biz/en/docs/messaging-api/message-types/)

## Support

For issues specific to:
- **LINE API**: Contact LINE Developer Support
- **MCP Integration**: Check MCP documentation or raise an issue
- **Server Setup**: Refer to the server features documentation
