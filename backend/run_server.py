"""
Simple server runner without reloader issues
"""
import os
import sys
from app import create_app

if __name__ == '__main__':
    try:
        env = os.environ.get('FLASK_ENV', 'development')
        app, socketio = create_app(env)
        
        print("=" * 60)
        print("🚀 Rural Healthcare Platform Server Starting")
        print("=" * 60)
        print(f"Environment: {env}")
        print(f"Debug Mode: {app.config['DEBUG']}")
        print(f"Server: http://127.0.0.1:5000")
        print("=" * 60)
        print("Socket.IO initialized and ready")
        print("Listening for connections...")
        print("=" * 60)
        
        # Run with socketio, disable reloader to avoid issues
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=False,  # Disable debug to prevent reloader
            use_reloader=False,
            log_output=True
        )
    except Exception as e:
        print(f"ERROR: Failed to start server: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
