import os
from datetime import timedelta

class Config:
    """Base configuration"""
    
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration - Force SQLite for development
    db_url = os.environ.get('DATABASE_URL', '').strip()
    SQLALCHEMY_DATABASE_URI = db_url if db_url else 'sqlite:///rural_health.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # File upload configuration (for lab reports)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
    
    # Razorpay payment gateway configuration
    # WHY ENVIRONMENT VARIABLES: Never hardcode API keys in code
    # Keys are loaded from .env file (git-ignored for security)
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')
    RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')
    
    # Google Gemini API configuration (for AI chatbot and voice assistant)
    # Used for: Text generation for chatbot and voice assistant
    # Get your API key from: https://aistudio.google.com/app/apikey
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = False  # Disabled to prevent reloader issues
    

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # HTTPS only in production
    

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
