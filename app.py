# app.py — CUSTOS Security Platform Unified Application Entry Point
import os
import sys
import argparse

# Ensure current directory is on sys.path
_app_dir = os.path.dirname(os.path.abspath(__file__))
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

from web.server import app, socket, camera_manager, start
from config import settings as config
from core.logging import app_logger

def main():
    parser = argparse.ArgumentParser(description="CUSTOS Security Platform Server")
    parser.add_argument("--host", default=os.getenv("HOST", "0.0.0.0"), help="Host IP to bind to")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 5000)), help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    os.makedirs(os.path.join(_app_dir, "frontend"), exist_ok=True)
    os.makedirs(config.SNAPSHOT_DIR, exist_ok=True)
    os.makedirs(config.RECORDING_DIR, exist_ok=True)

    app_logger.info(f"Launching CUSTOS Security Platform on {args.host}:{args.port} (Debug: {args.debug})")
    
    print("\n" + "=" * 65)
    print(f"   CUSTOS SECURITY PLATFORM — COMMAND CENTER READY")
    print(f"   URL:           http://localhost:{args.port}")
    print(f"   NETWORK:       http://{args.host}:{args.port}")
    print(f"   DEFAULT LOGIN: admin / admin123")
    print("=" * 65 + "\n")

    camera_manager.start_cameras(config.CAMERA_SOURCES)
    socket.run(app, host=args.host, port=args.port, debug=args.debug, use_reloader=False, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    main()
