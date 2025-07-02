from quart import Quart, request, jsonify, make_response, Response
import json
import asyncio
import sys
import os
import logging
import time
import hmac
import hashlib
import base64
from typing import Optional, Dict, Any
import pandas as pd
from asyncio import Lock
from hypercorn.asyncio import serve
from hypercorn.config import Config
from contextlib import AsyncExitStack

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.llm.azureopenai import azure_openai_processor
from src.server_connection import initialize_all_mcp, MCPServers
from src.client_and_server_validation import client_and_server_validation
from src.client_and_server_execution import client_and_server_execution
import logging


# Configure clean logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('api')

app = Quart(__name__)

# Clean request logging middleware
@app.before_request
async def log_request_start():
    request.start_time = time.time()

# Clean response logging middleware
@app.after_request
async def log_request_complete(response):
    request_time = time.time() - request.start_time
    logger.info(f"{request.method} {request.path} - {response.status_code} - {request_time:.3f}s")
    return response

app.mcp_exit_stack = None
# Initialize the clients when the app starts
@app.before_serving
async def startup():
    try:
        app.mcp_exit_stack = AsyncExitStack()
        await app.mcp_exit_stack.__aenter__()
        print("\n✅ MCP servers initialization started.")
        success = await initialize_all_mcp(app.mcp_exit_stack)
        if success: 
            print(f"\nAvailable servers: {list(MCPServers.keys())}")
            print("\n✅ MCP servers initialized successfully.\n")
        else:
            print("\n❌ Failed to initialize MCP clients.")
        
    except Exception as err:
        print(f"Error initializing MCP clients =========>>>> {err}")


@app.route("/api/v1/mcp/process_message", methods=["POST"])
async def process_message():
    try:
        data = await request.get_json()
        
        # Set streaming to false
        if "client_details" in data:
            data["client_details"]["is_stream"] = False
        
        # Validation check
        validation_result = await client_and_server_validation(data, {"streamCallbacks": None, "is_stream": False})
        if not validation_result["status"]:
            return jsonify({
                "Data": None,
                "Error": validation_result["error"],
                "Status": False
            }), 200
            
        print(f"\n✅ Validation Successful")
        # print(validation_result)
        print(f"\n✅ Execution Started")
        
        # Execution
        generated_payload = validation_result["payload"]
        execution_response = await client_and_server_execution(generated_payload, {"streamCallbacks": None, "is_stream": False})
        
        print(f"\n✅ Execution Completed")
        response_dict = {
            "Data": execution_response.Data,
            "Error": execution_response.Error,
            "Status": execution_response.Status
        }
        return jsonify(response_dict), 200
    
    except Exception as error:
        print(f"Error ========>>>>> {error}")
        return jsonify({
            "Data": None,
            "Error": str(error),
            "Status": False
        }), 500


class CustomStreamHandler:
    def __init__(self, response_queue: asyncio.Queue):
        self.response_queue = response_queue
    
    async def on_data(self, chunk: str):
        """Send data chunk to the stream"""
        await self.response_queue.put(f"data: {chunk}\n\n")
    
    async def on_end(self):
        """Send completion message and end the stream"""
        completion_data = {
            "Data": None,
            "Error": None,
            "Status": True,
            "StreamingStatus": "COMPLETED",
            "Action": "NO-ACTION"
        }
        await self.response_queue.put(f"data: {json.dumps(completion_data)}\n\n")
        await self.response_queue.put(None)  # Signal end of stream
    
    async def on_error(self, error: Exception):
        """Send error message and end the stream"""
        print(f"Streaming Error: {error}")
        error_data = {"error": str(error)}
        await self.response_queue.put(f"data: {json.dumps(error_data)}\n\n")
        await self.response_queue.put(None)  # Signal end of stream

async def stream_generator(response_queue: asyncio.Queue):
    """Generator function for streaming responses"""
    while True:
        try:
            # Wait for data with a timeout to prevent hanging
            data = await asyncio.wait_for(response_queue.get(), timeout=30.0)
            if data is None:  # End of stream signal
                break
            yield data
        except asyncio.TimeoutError:
            # Send keepalive or break on timeout
            break
        except Exception as e:
            print(f"Stream generator error: {e}")
            break

@app.route('/api/v1/mcp/process_message_stream', methods=['POST'])
async def process_message_stream():
    # Create a queue for streaming responses
    response_queue = asyncio.Queue()
    custom_stream_handler = CustomStreamHandler(response_queue)
    
    try:
        # Get request data
        data = await request.get_json()
        if not data:
            data = {}
        
        # Modify client details
        if 'client_details' not in data:
            data['client_details'] = {}
        data['client_details']['is_stream'] = False
        
        # Start streaming response
        async def generate_response():
            try:
                # Send initial status
                start_data = {
                    "Data": None,
                    "Error": None,
                    "Status": True,
                    "StreamingStatus": "STARTED",
                    "Action": "NO-ACTION"
                }
                await custom_stream_handler.on_data(json.dumps(start_data))
                
                # =========================================== validation check start =============================================================
                validation_result = await client_and_server_validation(data, {"streamCallbacks": custom_stream_handler, "is_stream": True})
                
                if not validation_result.get('status', False):
                    error_data = {
                        "Data": None,
                        "Error": validation_result.get('error'),
                        "Status": False,
                        "StreamingStatus": "ERROR",
                        "Action": "ERROR"
                    }
                    await custom_stream_handler.on_data(json.dumps(error_data))
                    await custom_stream_handler.on_end()
                    return
                # =========================================== validation check end =============================================================
                
                # =========================================== execution start ====================================================================
                generated_payload = validation_result.get('payload')
                execution_response = await client_and_server_execution(generated_payload, {"streamCallbacks": custom_stream_handler, "is_stream": True})
                # =========================================== execution end ======================================================================
                print(f"\n✅ ------------------------" , execution_response.Data)
                if not execution_response.Status:
                    error_data = {
                        "Data": execution_response.Data,
                        "Error": execution_response.Error,
                        "Status": False,
                        "StreamingStatus": "ERROR",
                        "Action": "ERROR"
                    }
                    await custom_stream_handler.on_data(json.dumps(error_data))
                    await custom_stream_handler.on_end()
                    return
                
                # Send successful response
                success_data = {
                    "Data": execution_response.Data,
                    "Error": execution_response.Error,
                    "Status": execution_response.Status,
                    "StreamingStatus": "IN-PROGRESS",
                    "Action": "AI-RESPONSE"
                }
                await custom_stream_handler.on_data(json.dumps(success_data))
                await custom_stream_handler.on_end()
                
            except Exception as error:
                print(f"Error ========>>>>> {error}")
                error_data = {
                    "Data": None,
                    "Error": str(error),
                    "Status": False,
                    "StreamingStatus": "ERROR",
                    "Action": "ERROR"
                }
                await custom_stream_handler.on_data(json.dumps(error_data))
                await custom_stream_handler.on_end()
        
        # Start the response generation in the background
        asyncio.create_task(generate_response())
        
        # Return streaming response
        return Response(
            stream_generator(response_queue),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        )
        
    except Exception as error:
        print(f"Error ========>>>>> {error}")
        
        # Send error response immediately
        error_data = {
            "Data": None,
            "Error": str(error),
            "Status": False,
            "StreamingStatus": "ERROR",
            "Action": "ERROR"
        }
        
        async def error_generator():
            yield f"data: {json.dumps(error_data)}\n\n"
        
        return Response(
            error_generator(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive'
            }
        )


# LINE Webhook functionality
def verify_line_signature(body: bytes, signature: str, channel_secret: str) -> bool:
    """Verify LINE webhook signature"""
    try:
        hash_digest = hmac.new(
            channel_secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).digest()
        expected_signature = base64.b64encode(hash_digest).decode('utf-8')
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False

@app.route("/line/webhook", methods=["POST"])
async def line_webhook():
    """Handle LINE webhook events"""
    try:
        # Get request body and headers
        body = await request.get_data()
        signature = request.headers.get('X-Line-Signature', '')
        
        # For demo purposes, we'll skip signature verification
        # In production, you should verify the signature with your channel secret
        # if not verify_line_signature(body, signature, YOUR_CHANNEL_SECRET):
        #     return jsonify({"error": "Invalid signature"}), 403
        
        # Parse webhook event
        try:
            webhook_data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON"}), 400
        
        logger.info(f"📱 LINE Webhook received: {webhook_data}")
        
        # Process each event
        events = webhook_data.get('events', [])
        for event in events:
            await process_line_event(event)
        
        return jsonify({"status": "success"}), 200
        
    except Exception as error:
        logger.error(f"LINE Webhook Error: {error}")
        return jsonify({"error": str(error)}), 500

async def process_line_event(event: dict):
    """Process individual LINE webhook events"""
    try:
        event_type = event.get('type')
        source = event.get('source', {})
        user_id = source.get('userId')
        
        logger.info(f"📱 Processing LINE event: {event_type} from user: {user_id}")
        
        if event_type == 'message':
            message = event.get('message', {})
            message_type = message.get('type')
            
            if message_type == 'text':
                text = message.get('text', '')
                logger.info(f"📱 Received text message: {text}")
                
                # Here you can process the message and respond using your MCP servers
                # Example: Auto-respond with a helpful message
                await send_line_response(user_id, f"Thanks for your message: '{text}'. I'm your MCP-powered assistant!")
                
        elif event_type == 'follow':
            logger.info(f"📱 User {user_id} followed the bot")
            await send_line_response(user_id, "🎉 Welcome! I'm your AI assistant powered by MCP servers. I can help with math calculations, email management, and more!")
            
        elif event_type == 'unfollow':
            logger.info(f"📱 User {user_id} unfollowed the bot")
            
    except Exception as e:
        logger.error(f"Error processing LINE event: {e}")

async def send_line_response(user_id: str, message: str):
    """Send a response back to LINE user using MCP"""
    try:
        # Create MCP request to send LINE message
        mcp_request = {
            "selected_server_credentials": {
                "LINE_MCP": {
                    "channel_access_token": "demo_mode",  # Will be replaced with actual credentials
                    "channel_secret": "demo_mode",
                    "webhook_url": "demo_mode"
                }
            },
            "client_details": {
                "api_key": "demo_mode",
                "temperature": 0.1,
                "max_token": 1000,
                "input": f"Send a text message '{message}' to user {user_id}",
                "input_type": "text",
                "prompt": "you are a helpful LINE messaging assistant",
                "chat_model": "gemini-2.0-flash",
                "chat_history": []
            },
            "selected_client": "MCP_CLIENT_GEMINI",
            "selected_servers": ["LINE_MCP"]
        }
        
        logger.info(f"📱 Sending LINE response via MCP: {message[:50]}...")
        
        # Note: In production, you would process this through your MCP pipeline
        # For now, we'll just log it
        logger.info(f"📱 Would send via MCP: {message}")
        
    except Exception as e:
        logger.error(f"Error sending LINE response: {e}")

@app.route("/line/status", methods=["GET"])
async def line_status():
    """Get LINE webhook status"""
    return jsonify({
        "webhook_url": "Configure this with your ngrok URL + /line/webhook",
        "status": "active",
        "mcp_servers": list(MCPServers.keys()) if MCPServers else [],
        "example_webhook_url": "https://your-ngrok-url.ngrok.io/line/webhook"
    })

@app.after_serving
async def shutdown():
    if app.mcp_exit_stack:
        await app.mcp_exit_stack.__aexit__(None, None, None)
        app.mcp_exit_stack = None
        print("\n✅ MCP servers cleaned up on shutdown.\n")
    
if __name__ == "__main__":
    # Create a config instance
    config = Config()
    # Configure bind address and port 
    config.bind = [f"0.0.0.0:5001"]

    # Print welcome banner
    print("╔═══════════════════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                                           ║")
    print("║                                📈🚀✨ ADYA  📈🚀✨                                        ║")
    print("║                                                                                           ║")
    print("║  🎉 Welcome to the MCP(Model Context Protocol) Server Integration Hackathon 2k25 !! 🎉    ║")
    print("║                                                                                           ║")
    print("║  ✅ MCP Server running on http://0.0.0.0:5001 ✅                                          ║")
    print("║  📱 LINE Webhook endpoint: /line/webhook                                                 ║")
    print("║  🔗 Webhook status: http://localhost:5001/line/status                                     ║")
    print("║                                                                                           ║")
    print("║  💡 To get your webhook URL:                                                              ║")
    print("║     1. Install ngrok: npm install -g ngrok                                               ║")
    print("║     2. Run: ngrok http 5001                                                               ║")
    print("║     3. Copy HTTPS URL + /line/webhook                                                     ║")
    print("║                                                                                           ║") 
    print("╚═══════════════════════════════════════════════════════════════════════════════════════════╝")

    # Start the Quart app
    asyncio.run(serve(app, config))
