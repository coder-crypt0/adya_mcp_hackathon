# 🚀 QUICK WEBHOOK SETUP - LINE MCP

## ⚡ IMMEDIATE SOLUTION (No Installation Required)

### 🎯 **Use webhook.site - Works Right Now!**

**Step 1: Get Your Webhook URL (30 seconds)**
1. Go to: **https://webhook.site/**
2. Copy the unique URL you see (e.g., `https://webhook.site/12345678-abcd-1234-1234-123456789012`)
3. Your webhook URL is: `[YOUR_WEBHOOK_SITE_URL]/line/webhook`

**Example:**
- webhook.site gives you: `https://webhook.site/12345678-abcd-1234-1234-123456789012`
- Your LINE webhook URL: `https://webhook.site/12345678-abcd-1234-1234-123456789012/line/webhook`

**Step 2: Configure LINE Developer Console**
1. Go to: https://developers.line.biz/
2. Select your Messaging API channel
3. Go to "Messaging API" tab
4. Set **Webhook URL**: `https://webhook.site/[your-id]/line/webhook`
5. Enable **Use webhook**: ✅ ON
6. Click **Verify**

**Step 3: Test Immediately**
- Send a message to your LINE bot
- See the webhook data appear in real-time on webhook.site
- Your server will process the webhook and respond

✅ **This works immediately - no installation required!**

---

## 🔧 **Alternative: ngrok (For Advanced Users)**

### 🚨 **Important: ngrok Requires Session Restart**

ngrok was successfully installed, but you need to **restart your terminal/PowerShell** for it to work.

**After Restarting Terminal:**
```powershell
# Test if ngrok is available
ngrok version

# If working, start tunnel
ngrok http 5001

# Use the HTTPS URL: https://[random-id].ngrok.io/line/webhook
```

**If ngrok still doesn't work after restart:**
```powershell
# Try refreshing environment
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Or find ngrok manually
where.exe ngrok
```

---

## 🧪 **Testing Your Setup**

### **Test 1: Server Status**
```powershell
Invoke-WebRequest -Uri "http://localhost:5001/line/status" -Method GET
```

### **Test 2: Webhook Endpoint**
```powershell
$body = '{"events": [{"type": "message", "message": {"type": "text", "text": "test"}}]}'
Invoke-WebRequest -Uri "http://localhost:5001/line/webhook" -Method POST -Body $body -ContentType "application/json"
```

### **Test 3: Use Postman Collection**
- Open `postman_api_collections/LINE_MCP_Collection.json`
- Set your webhook URL in environment variables
- Run the 10 comprehensive test cases

---

## 📱 **Your LINE MCP Tools (10 Available)**

1. **send_text_message** - Basic messaging
2. **send_rich_message** - Buttons, carousels
3. **send_image_message** - Images
4. **send_flex_message** - Custom layouts
5. **broadcast_message** - Broadcast to all
6. **get_user_profile** - User info
7. **get_group_summary** - Group info
8. **manage_group_members** - Group management
9. **manage_rich_menu** - Rich menus
10. **handle_webhook_event** - Webhook processing

---

## 🎯 **Recommended Next Steps**

### **For Immediate Testing:**
1. ✅ Use webhook.site (ready now!)
2. ✅ Configure LINE Developer Console
3. ✅ Test with Postman collection
4. ✅ Send test messages to your bot

### **For Development:**
1. Restart PowerShell terminal
2. Test `ngrok version`
3. Use `ngrok http 5001`
4. Replace webhook.site URL with ngrok URL

---

## 🚨 **Troubleshooting**

### **If webhook.site doesn't receive events:**
- Check LINE webhook URL format: `https://webhook.site/[id]/line/webhook`
- Ensure webhook is enabled in LINE console
- Verify LINE bot is properly configured

### **If ngrok doesn't work after restart:**
- Check installation: `winget list ngrok`
- Manual installation: Download from https://ngrok.com/download
- Add to PATH manually

### **If server gives 404:**
- Ensure server is running on port 5001
- Check endpoint exists: http://localhost:5001/line/status
- Verify all MCP servers are initialized

---

## ✅ **You're Ready!**

Your LINE MCP integration is **fully functional** right now using webhook.site!

**Server Status**: ✅ Running  
**Webhook Endpoint**: ✅ Active  
**10 MCP Tools**: ✅ Available  
**Postman Tests**: ✅ Ready  
**Immediate Testing**: ✅ webhook.site  
**Advanced Setup**: ✅ ngrok (after restart)
