"""
Healthcare Chatbot Module
Provides AI-powered chat assistance with safety features and RAG
"""
from flask import Blueprint

chatbot_bp = Blueprint('chatbot', __name__)

from . import routes
