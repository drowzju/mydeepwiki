import os
import sys
import logging
import signal
import asyncio

# Add parent directory to path before any api imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from api.logging_config import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

# Add the current directory to the path so we can import the api package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Apply watchfiles monkey patch BEFORE uvicorn import
is_development = os.environ.get("NODE_ENV") != "production"
if is_development:
    import watchfiles
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(current_dir, "logs")

    original_watch = watchfiles.watch
    def patched_watch(*args, **kwargs):
        # Only watch the api directory but exclude logs subdirectory
        # Instead of watching the entire api directory, watch specific subdirectories
        api_subdirs = []
        for item in os.listdir(current_dir):
            item_path = os.path.join(current_dir, item)
            if os.path.isdir(item_path) and item != "logs":
                api_subdirs.append(item_path)
            elif os.path.isfile(item_path) and item.endswith(".py"):
                api_subdirs.append(item_path)

        return original_watch(*api_subdirs, **kwargs)
    watchfiles.watch = patched_watch

import uvicorn

# Check for available API keys (all optional now)
available_keys = []
if os.environ.get('GOOGLE_API_KEY'):
    available_keys.append('GOOGLE_API_KEY')
if os.environ.get('OPENAI_API_KEY'):
    available_keys.append('OPENAI_API_KEY')
if os.environ.get('OPENROUTER_API_KEY'):
    available_keys.append('OPENROUTER_API_KEY')
if os.environ.get('DASHSCOPE_API_KEY'):
    available_keys.append('DASHSCOPE_API_KEY')
if os.environ.get('DASHSCOPE_WORKSPACE_ID'):
    available_keys.append('DASHSCOPE_WORKSPACE_ID')

if available_keys:
    logger.info(f"Available API keys: {', '.join(available_keys)}")
else:
    logger.warning("No API keys configured. You need at least one LLM provider key (GOOGLE_API_KEY, OPENAI_API_KEY, etc.)")

# Configure Google Generative AI
import google.generativeai as genai
from api.config import GOOGLE_API_KEY

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    logger.warning("GOOGLE_API_KEY not configured")

# Setup graceful shutdown handling
def handle_exit(signum, frame):
    """Handle exit signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down...")
    # Force exit after a short delay
    import threading
    def force_exit():
        import time
        time.sleep(2)  # Give 2 seconds for graceful shutdown
        logger.info("Force exiting...")
        os._exit(0)
    threading.Thread(target=force_exit, daemon=True).start()

# Register signal handlers
signal.signal(signal.SIGINT, handle_exit)   # Ctrl+C
signal.signal(signal.SIGTERM, handle_exit)  # Termination signal

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8091))

    # Import the app here to ensure environment variables are set first
    from api.api import app

    logger.info(f"Starting Streaming API on port {port}")
    logger.info("Press Ctrl+C to stop the server")

    try:
        # Run the FastAPI app with uvicorn (reload disabled for stability)
        uvicorn.run(
            "api.api:app",
            host="0.0.0.0",
            port=port,
            reload=False,
            timeout_graceful_shutdown=5,  # 5 second timeout for graceful shutdown
        )
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, exiting...")
        os._exit(0)
    except Exception as e:
        logger.error(f"Error running server: {e}")
        os._exit(1)
