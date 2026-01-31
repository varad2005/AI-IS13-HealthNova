"""
Voice Assistant Routes

POST /voice/chat - Main endpoint for text-based AI interaction
- Accepts text message
- Returns AI response text

NOTE: Switched from OpenAI to Google Gemini (free tier available)
Gemini doesn't have built-in speech-to-text and text-to-speech,
so this is now a text-based assistant instead of voice.

WORKFLOW:
1. Receive text message from frontend
2. Generate response using Google Gemini with healthcare system prompt
3. Return JSON with AI response
"""

import os
import google.generativeai as genai
from flask import request, jsonify, current_app
from . import voice_assistant_bp

# Load system prompt from file
PROMPT_FILE = os.path.join(os.path.dirname(__file__), 'prompt.txt')

def load_system_prompt():
    """Load the healthcare voice assistant system prompt"""
    try:
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        # Fallback system prompt if file doesn't exist
        return """You are a helpful healthcare voice assistant for non-literate users in rural India. 
Speak in very simple language with short sentences. 
You provide health education and awareness ONLY. 
NEVER diagnose diseases or prescribe medicines. 
Always encourage consulting a doctor for medical issues. 
Be calm, respectful, and supportive."""

SYSTEM_PROMPT = load_system_prompt()


@voice_assistant_bp.route('/chat', methods=['POST'])
def ai_chat():
    """
    Text-based AI chat endpoint using Google Gemini
    
    ACCEPTS:
    - JSON with 'message' field
    
    RETURNS:
    - JSON with ai_response_text
    
    ERROR HANDLING:
    - 400: No message provided
    - 500: Gemini API errors or processing errors
    """
    try:
        # Step 1: Validate message
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'No message provided'
            }), 400
        
        user_message = data['message'].strip()
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Message cannot be empty'
            }), 400
        
        # Step 2: Configure Gemini
        api_key = current_app.config.get('GEMINI_API_KEY')
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'Gemini API key not configured'
            }), 500
        
        genai.configure(api_key=api_key)
        
        # Step 3: Generate AI response using Gemini
        print(f"[Voice Assistant] User message: {user_message}")
        print("[Voice Assistant] Generating AI response with Gemini...")
        
        # Create model with system instructions
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=SYSTEM_PROMPT
        )
        
        # Generate response
        response = model.generate_content(
            user_message,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=150,
                top_p=0.9
            )
        )
        
        ai_response_text = response.text.strip()
        print(f"[Voice Assistant] AI Response: {ai_response_text}")
        
        # Step 4: Return response
        return jsonify({
            'success': True,
            'ai_response_text': ai_response_text,
            'message': ai_response_text  # Alias for compatibility
        }), 200
        
    except Exception as e:
        print(f"[Voice Assistant] Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Processing error: {str(e)}'
        }), 500


@voice_assistant_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for AI assistant service"""
    try:
        # Verify Gemini API key is configured
        api_key = current_app.config.get('GEMINI_API_KEY')
        
        return jsonify({
            'success': True,
            'service': 'AI Assistant (Gemini)',
            'status': 'healthy',
            'api_configured': bool(api_key)
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'service': 'AI Assistant',
            'status': 'unhealthy',
            'error': str(e)
        }), 500
