"""
Voice Assistant Module

AI-powered voice assistant for healthcare education and awareness.
Uses OpenAI Whisper (speech-to-text), ChatGPT (text generation), and TTS (text-to-speech).

SAFETY FEATURES:
- NO medical diagnosis
- NO prescription recommendations
- Educational and awareness focus only
- Encourages consulting real doctors
- Simple, voice-friendly language
"""

from flask import Blueprint

voice_assistant_bp = Blueprint('voice_assistant', __name__, url_prefix='/voice')

from . import routes
