# 🚀 LINE Webhook Setup Guide

## Your Current Setup

✅ **LINE MCP Server**: Created and integrated  
✅ **Webhook Endpoint**: Added to your server at `/line/webhook`  
✅ **Status Endpoint**: Available at `/line/status`  

## 🔗 Get Your Webhook URL (3 Simple Steps)

### Step 1: Install ngrok
```bash
# Option 1: Using npm
npm install -g ngrok

# Option 2: Download from https://ngrok.com/download
```

### Step 2: Start Your Server
```bash
# In your project directory
cd mcp_servers/python/clients
python run.py
```

You'll see this banner with webhook info:
```
╔═══════════════════════════════════════════════════════════════╗
║  ✅ MCP Server running on http://0.0.0.0:5001 ✅              ║
║  📱 LINE Webhook endpoint: /line/webhook                     ║
║  🔗 Webhook status: http://localhost:5001/line/status         ║
╚═══════════════════════════════════════════════════════════════╝
```

### Step 3: Create Public Tunnel
```bash
# In a new terminal window
ngrok http 5001
```

Copy the **HTTPS** URL from ngrok output:
```
Forwarding    https://abc123.ngrok.io -> http://localhost:5001
```

## 🎯 Your Webhook URL

**Format**: `https://[your-ngrok-subdomain].ngrok.io/line/webhook`

**Example**: `https://abc123.ngrok.io/line/webhook`

## 📝 Configure in LINE Developer Console

1. Go to [LINE Developers Console](https://developers.line.biz/)
2. Select your Messaging API channel
3. Go to "Messaging API" tab
4. Set **Webhook URL**: `https://your-ngrok-url.ngrok.io/line/webhook`
5. Enable **Use webhook**: ON
6. Click **Verify** to test the connection

## 🧪 Test Your Setup

### Check Webhook Status
```bash
curl http://localhost:5001/line/status
```

### Test Webhook Endpoint
```bash
curl -X POST http://localhost:5001/line/webhook \
  -H "Content-Type: application/json" \
  -d '{"events": [{"type": "message", "message": {"type": "text", "text": "test"}}]}'
```

## 🔄 Using Your Webhook

Once configured, your LINE bot will:

1. **Receive Messages**: LINE sends webhook events to your server
2. **Process Events**: Your server processes incoming messages
3. **Send Responses**: Use MCP servers to send replies back
4. **Log Activity**: Monitor webhook activity in your server logs

## 📱 Example Webhook Flow

```
LINE User sends message → LINE Platform → Your ngrok URL → Your Server → MCP Processing → Response back to user
```

## 🔧 Available Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/line/webhook` | POST | Receive LINE webhook events |
| `/line/status` | GET | Check webhook configuration |
| `/api/v1/mcp/process_message` | POST | Send messages via MCP |

## 🚨 Important Notes

- **HTTPS Required**: LINE only accepts HTTPS webhook URLs
- **Keep ngrok Running**: Your webhook will stop working if ngrok is closed
- **Free Limitations**: ngrok free tier gives you a random URL each time
- **Production**: For permanent deployment, use a cloud service

## 🎉 You're Ready!

Your webhook URL is: **`https://[your-ngrok-domain].ngrok.io/line/webhook`**

Use this URL in your LINE Developer Console webhook settings!
