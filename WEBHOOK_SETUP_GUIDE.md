# 🚀 LINE Webhook Setup Guide

## Your Current Setup

✅ **LINE MCP Server**: Created and integrated with 10 powerful tools  
✅ **Webhook Endpoint**: Added to your server at `/line/webhook`  
✅ **Status Endpoint**: Available at `/line/status`  

## 🔗 Get Your Webhook URL (Choose Your Method)

### Option 1: Using ngrok (Recommended for Development)

#### Step 1: Install ngrok
**For Windows (Recommended):**
```powershell
# Option 1: Using winget (Windows Package Manager) - RECOMMENDED
winget install ngrok

# Option 2: Using npm (if you have Node.js)
npm install -g ngrok

# Option 3: Using Chocolatey
choco install ngrok

# Option 4: Manual download from https://ngrok.com/download
# Download, extract, and add to PATH
```

**Important Notes:**
- After installation, **restart your terminal/PowerShell** for ngrok to be recognized
- Or open a new terminal window
- The PATH environment variable needs to be refreshed

#### Step 2: Start Your Server
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

#### Step 3: Create Public Tunnel with ngrok
```bash
# In a new terminal window
ngrok http 5001
```

Copy the **HTTPS** URL from ngrok output:
```
Forwarding    https://abc123.ngrok.io -> http://localhost:5001
```

**Your Webhook URL**: `https://abc123.ngrok.io/line/webhook`

### Option 2: Using webhook.site (Quick Testing)

#### For Quick Testing Without Installation:

1. **Go to [webhook.site](https://webhook.site/)**
2. **Copy your unique URL** (e.g., `https://webhook.site/12345678-1234-1234-1234-123456789012`)
3. **Use this URL + `/line/webhook`** in LINE Developer Console
4. **Note**: This method only receives webhooks for testing - it won't forward to your local server

**Your Webhook URL**: `https://webhook.site/your-unique-id/line/webhook`

#### For Testing with Forwarding:
1. Visit [webhook.site](https://webhook.site/)
2. Click **"Custom Actions"** or **"Edit"**
3. Set up forwarding to `http://your-local-ip:5001/line/webhook`
4. Use the webhook.site URL in LINE Developer Console

### Option 3: Cloud Deployment (Production)

Deploy your server to:
- **Railway**: `railway deploy`
- **Heroku**: `git push heroku main`  
- **Digital Ocean**: Use App Platform
- **AWS/Azure**: Deploy as container or serverless function

## 🎯 Your Webhook URL Formats

| Method | URL Format | Example |
|--------|------------|---------|
| **ngrok** | `https://[random-id].ngrok.io/line/webhook` | `https://abc123.ngrok.io/line/webhook` |
| **webhook.site** | `https://webhook.site/[unique-id]/line/webhook` | `https://webhook.site/12345678-abcd/line/webhook` |
| **Cloud Deploy** | `https://[your-app].platform.com/line/webhook` | `https://myapp.railway.app/line/webhook` |

## 📝 Configure in LINE Developer Console

1. Go to [LINE Developers Console](https://developers.line.biz/)
2. Select your Messaging API channel
3. Go to "Messaging API" tab
4. Set **Webhook URL**: Use your chosen webhook URL from above
5. Enable **Use webhook**: ✅ ON
6. Click **Verify** to test the connection

## 🧪 Test Your Setup

### Check Webhook Status (Local Server)
```bash
curl http://localhost:5001/line/status
```

### Test Webhook Endpoint (Local Server)
```bash
curl -X POST http://localhost:5001/line/webhook \
  -H "Content-Type: application/json" \
  -d '{"events": [{"type": "message", "message": {"type": "text", "text": "test"}}]}'
```

### Test with webhook.site
- Visit your webhook.site URL in browser
- Send a message to your LINE bot
- See real-time webhook data in webhook.site dashboard

## 🔄 Using Your Webhook

Once configured, your LINE bot will:

1. **Receive Messages**: LINE sends webhook events to your server
2. **Process Events**: Your server processes incoming messages using MCP tools
3. **Send Responses**: Use MCP servers to send replies back
4. **Log Activity**: Monitor webhook activity in your server logs

## 📱 Example Webhook Flow

```
LINE User sends message → LINE Platform → Your Webhook URL → Your Server → MCP Processing → Response back to user
```

## 🔧 Available Endpoints

| Endpoint | Method | Purpose |  
|----------|--------|---------|
| `/line/webhook` | POST | Receive LINE webhook events |
| `/line/status` | GET | Check webhook configuration |
| `/api/v1/mcp/process_message` | POST | Send messages via MCP |

## 🛠️ LINE MCP Tools Available (10 Total)

1. **send_text_message** - Send text messages with quick replies
2. **send_rich_message** - Send buttons, carousels, confirmations  
3. **send_image_message** - Send image messages
4. **send_flex_message** - Send custom flex layouts
5. **broadcast_message** - Broadcast to all friends
6. **get_user_profile** - Get user profile information
7. **get_group_summary** - Get group information
8. **handle_webhook_event** - Process incoming webhooks
9. **manage_rich_menu** - Create and manage rich menus
10. **manage_group_members** - Handle group member operations

## 🚨 Important Notes

- **HTTPS Required**: LINE only accepts HTTPS webhook URLs
- **Keep Services Running**: Your chosen method must stay active
- **ngrok Limitations**: Free tier gives random URL each restart
- **webhook.site**: Limited to testing, not for production
- **Production**: Use cloud deployment for permanent setup

## 🎉 Quick Start Commands

### Method 1: ngrok (Full Development)
```bash
# Terminal 1: Start server
cd mcp_servers/python/clients && python run.py

# Terminal 2: Start ngrok  
ngrok http 5001

# Use: https://[random-id].ngrok.io/line/webhook
```

### Method 2: webhook.site (Quick Test)
```bash
# 1. Go to webhook.site
# 2. Copy URL: https://webhook.site/[unique-id] 
# 3. Use: https://webhook.site/[unique-id]/line/webhook
```

## 🚀 You're Ready!

Choose your preferred method and use the corresponding webhook URL in your LINE Developer Console!

---

**Next Steps:**
1. Start your server
2. Get your webhook URL using your preferred method
3. Configure in LINE Developer Console  
4. Test with a message to your bot
5. Explore the 10 powerful MCP tools!
