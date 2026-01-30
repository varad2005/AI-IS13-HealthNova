from flask import Flask, jsonify, session, send_from_directory
from flask_migrate import Migrate
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from config import config
from models import db
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__, 
                static_folder='../frontend',
                static_url_path='')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Enable CORS with credentials support for all origins (development)
    CORS(app, supports_credentials=True, origins='*')
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Initialize SocketIO for video consultation signaling
    # Allow all origins for development (video calls can come from any client)
    socketio = SocketIO(app, 
                       cors_allowed_origins='*',
                       logger=False, 
                       engineio_logger=False,
                       async_mode='threading',
                       ping_timeout=60,
                       ping_interval=25)
    
    # Register SocketIO events
    from video_consultation import register_socketio_events
    register_socketio_events(socketio)
    
    # Create upload folder if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Register blueprints
    from auth.routes import auth_bp
    from patient.routes import patient_bp
    from doctor.routes import doctor_bp
    from lab.routes import lab_bp
    from chatbot import chatbot_bp
    from payments import payments_bp  # Razorpay payment integration
    from video import video_bp  # Video consultation management
    from voice_assistant import voice_assistant_bp  # AI Voice Assistant
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(patient_bp, url_prefix='/patient')
    app.register_blueprint(doctor_bp, url_prefix='/doctor')
    app.register_blueprint(lab_bp, url_prefix='/lab')
    app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
    app.register_blueprint(payments_bp, url_prefix='/payments')  # Payment routes
    app.register_blueprint(video_bp, url_prefix='/video')  # Video consultation routes
    app.register_blueprint(voice_assistant_bp, url_prefix='/voice')  # AI assistant routes (Gemini)
    
    # Root route - serve landing page
    @app.route('/')
    def index():
        return send_from_directory('../frontend', 'landing.html')
    
    # API info route
    @app.route('/api')
    def api_info():
        return jsonify({
            'status': 'success',
            'message': 'Health Nova API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/auth',
                'patient': '/patient',
                'doctor': '/doctor',
                'lab': '/lab'
            }
        })
    
    # Health check route
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'database': 'connected' if db.engine else 'disconnected'
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'status': 'error',
            'message': 'Resource not found'
        }), 404
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'status': 'error',
            'message': 'Access forbidden'
        }), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500
    
    return app, socketio


if __name__ == '__main__':
    # Get environment from environment variable, default to development
    env = os.environ.get('FLASK_ENV', 'development')
    app, socketio = create_app(env)
    
    print("\n" + "="*60)
    print("Rural Healthcare Platform Server")
    print("="*60)
    print(f"Environment: {env}")
    print(f"Local URL: http://127.0.0.1:5000")
    print(f"Network URL: http://0.0.0.0:5000")
    print("="*60)
    print("Server is running. Press CTRL+C to stop.\n")
    
    # Run with threading mode
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False,
        log_output=False
    )
