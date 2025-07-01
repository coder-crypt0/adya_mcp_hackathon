"""
Simplified MCP Client Server Starter
"""
import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    print("Starting MCP Client Server...")
    print("╔═══════════════════════════════════════════════════════════════════════════════════════════╗")
    print("║                                📈🚀✨ ADYA  📈🚀✨                                        ║")
    print("║  🎉 Welcome to the MCP(Model Context Protocol) Server Integration Hackathon 2k25 !! 🎉    ║")
    print("║  ✅ Server running on http://0.0.0.0:5001 ✅                                              ║")
    print("╚═══════════════════════════════════════════════════════════════════════════════════════════╝")
    
    # Import the main run functionality
    from run import app, Config, serve
    import asyncio
    
    # Create config
    config = Config()
    config.bind = ["0.0.0.0:5001"]
    
    # Start server
    asyncio.run(serve(app, config))
    
except ImportError as e:
    print(f"Import Error: {e}")
    print("Please install required dependencies: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Server Error: {e}")
    sys.exit(1)
