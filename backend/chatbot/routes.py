"""
Chatbot Routes
Dual-chatbot system with role-based separation:
1. Patient Chatbot (public, educational only)
2. Doctor Chatbot (restricted, clinical support)
"""
from flask import request, jsonify, session
import google.generativeai as genai
import os
from datetime import datetime

from . import chatbot_bp
from .knowledge_base import knowledge_base
from .safety_checks import safety_checker
from auth.decorators import role_required


# ============================================================
# ROLE-BASED SYSTEM PROMPTS
# ============================================================
# Load prompts from separate files for maintainability

def load_prompt(filename):
    """Load system prompt from file"""
    try:
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', filename)
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error loading prompt {filename}: {e}")
        return ""

# Patient chatbot prompt (public, educational)
PATIENT_PROMPT = load_prompt('patient_prompt.txt')

# Doctor chatbot prompt (restricted, clinical support)
DOCTOR_PROMPT = load_prompt('doctor_prompt.txt')

# Fallback if prompts fail to load
if not PATIENT_PROMPT:
    PATIENT_PROMPT = """You are a health education assistant. Provide general health information only.
Never diagnose, prescribe, or access patient records. Keep responses short and simple."""

if not DOCTOR_PROMPT:
    DOCTOR_PROMPT = """You are a clinical support assistant for doctors.
Summarize provided data only. Never make final diagnoses or prescriptions."""


def get_gemini_response(user_message: str, system_prompt: str, context: str = "", patient_data: dict = None) -> dict:
    """
    Call Gemini API with role-specific system prompt
    
    Args:
        user_message: User's question/message
        system_prompt: Role-based system prompt (patient or doctor)
        context: Retrieved context from RAG system
        patient_data: Patient data for doctor chatbot (optional)
    
    Returns:
        dict with response and metadata
    """
    try:
        # Configure Gemini API (using environment variable)
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            return {
                "success": False,
                "response": "Chatbot is temporarily unavailable. Please try again later or contact support.",
                "metadata": {
                    "response_type": "error",
                    "error": "API key not configured"
                }
            }
        
        genai.configure(api_key=api_key)
        
        # Use Gemini 1.5 Flash for fast responses
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # ============================================================
        # CONTEXT INJECTION - Inject retrieved knowledge and patient data
        # ============================================================
        
        # Build context string
        context_parts = []
        
        if context:
            context_parts.append(f"**KNOWLEDGE BASE:**\n{context}")
        
        if patient_data:
            # Format patient data for doctor chatbot
            patient_context = "**PATIENT DATA:**\n"
            for key, value in patient_data.items():
                patient_context += f"- {key}: {value}\n"
            context_parts.append(patient_context)
        
        full_context = "\n\n".join(context_parts) if context_parts else "No additional context available."
        
        full_prompt = f"""{system_prompt}

---
{full_context}

**PLATFORM FEATURES:**
{knowledge_base.get_all_platform_features()}

---
**USER QUESTION:**
{user_message}

**YOUR RESPONSE:**"""

        # Generate response
        response = model.generate_content(full_prompt)
        
        return {
            "success": True,
            "response": response.text,
            "metadata": {
                "response_type": "ai_generated",
                "model": "gemini-1.5-flash",
                "context_used": bool(context),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "response": "I'm having trouble processing your request. Please try again or contact our support team at 1800-XXX-XXXX.",
            "metadata": {
                "response_type": "error",
                "error": str(e)
            }
        }


@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    """
    LEGACY endpoint - redirects to patient chatbot for backward compatibility
    Kept for existing integrations
    """
    return chat_patient()


@chatbot_bp.route('/chat/patient', methods=['POST'])
def chat_patient():
    """
    PATIENT CHATBOT (PUBLIC - NO LOGIN REQUIRED)
    
    ==============================================================
    PRIVACY & SECURITY:
    - NO access to patient medical records
    - NO access to doctor notes or diagnoses
    - NO access to lab results
    - Educational and platform guidance ONLY
    ==============================================================
    
    Behavior:
    - Provides health education and awareness
    - Does NOT diagnose diseases
    - Does NOT prescribe medicines
    - Uses simple, non-technical language
    - Encourages consulting a doctor
    
    Request body:
        {
            "message": "user's message"
        }
    
    Response:
        {
            "success": true/false,
            "response": "chatbot response",
            "metadata": {
                "bot_type": "patient",
                "response_type": "rule_based" | "ai_generated" | "fallback",
                "safety_check": "passed" | "emergency" | "inappropriate"
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "response": "Please provide a message.",
                "metadata": {"response_type": "error"}
            }), 400
        
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                "success": False,
                "response": "Message cannot be empty.",
                "metadata": {"response_type": "error"}
            }), 400
        
        # ============================================================
        # STEP 1: Rule-based safety checks (BEFORE AI)
        # ============================================================
        
        # Check for greetings
        if safety_checker.is_greeting(user_message):
            return jsonify({
                "success": True,
                "response": safety_checker.get_greeting_response(),
                "metadata": {
                    "response_type": "rule_based",
                    "rule_triggered": "greeting"
                }
            })
        
        # Check for medical emergencies
        emergency_check = safety_checker.check_emergency(user_message)
        if emergency_check["is_emergency"]:
            return jsonify({
                "success": True,
                "response": emergency_check["response"],
                "metadata": {
                    **emergency_check["metadata"],
                    "safety_check": "emergency",
                    "severity": emergency_check["severity"]
                }
            })
        
        # Check for inappropriate requests (diagnosis/prescription)
        inappropriate_check = safety_checker.check_inappropriate_request(user_message)
        if inappropriate_check:
            return jsonify({
                "success": True,
                "response": inappropriate_check["response"],
                "metadata": {
                    **inappropriate_check["metadata"],
                    "safety_check": "inappropriate"
                }
            })
        
        # ============================================================
        # STEP 2: RAG - Retrieve relevant context
        # ============================================================
        relevant_knowledge = knowledge_base.search_knowledge(user_message, top_k=3)
        context_string = knowledge_base.get_context_string(relevant_knowledge)
        
        # ============================================================
        # STEP 3: Generate AI response with PATIENT PROMPT
        # DATA PRIVACY: Patient chatbot does NOT receive patient data
        # ============================================================
        ai_result = get_gemini_response(
            user_message=user_message,
            system_prompt=PATIENT_PROMPT,  # Educational prompt only
            context=context_string,
            patient_data=None  # NEVER pass patient data to patient bot
        )
        
        if not ai_result["success"]:
            # Fallback response if AI fails
            return jsonify({
                "success": True,
                "response": "I'm currently having technical difficulties. For immediate assistance, please call our support line at 1800-XXX-XXXX or book an appointment through your dashboard.",
                "metadata": {
                    "bot_type": "patient",
                    "response_type": "fallback",
                    "ai_error": ai_result["metadata"].get("error")
                }
            })
        
        # ============================================================
        # STEP 4: Return response with metadata
        # ============================================================
        return jsonify({
            "success": True,
            "response": ai_result["response"],
            "metadata": {
                **ai_result["metadata"],
                "bot_type": "patient",
                "safety_check": "passed",
                "context_retrieved": len(relevant_knowledge) > 0,
                "knowledge_items_found": len(relevant_knowledge),
                "data_access": "none"  # Patient bot has NO data access
            }
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "response": "An unexpected error occurred. Please contact support.",
            "metadata": {
                "bot_type": "patient",
                "response_type": "error",
                "error": str(e)
            }
        }), 500


@chatbot_bp.route('/chat/doctor', methods=['POST'])
@role_required('doctor')  # CRITICAL: Only doctors can access this endpoint
def chat_doctor():
    """
    DOCTOR CHATBOT (RESTRICTED - DOCTOR LOGIN REQUIRED)
    
    ==============================================================
    ACCESS CONTROL:
    - Requires doctor role authentication
    - Returns 403 Forbidden if non-doctor attempts access
    - Verified via @role_required('doctor') decorator
    ==============================================================
    
    Behavior:
    - Assists doctors with patient data summarization
    - Provides clinical support and differential considerations
    - Does NOT make final diagnoses
    - Does NOT prescribe medications independently
    - Professional, concise medical terminology
    
    Request body:
        {
            "message": "doctor's question",
            "patient_id": "optional patient ID for context",
            "patient_data": {
                "age": 45,
                "sex": "M",
                "chief_complaint": "fever x3 days",
                "vitals": {"bp": "130/80", "temp": "101F"},
                ... (optional additional patient context)
            }
        }
    
    Response:
        {
            "success": true/false,
            "response": "clinical support response",
            "metadata": {
                "bot_type": "doctor",
                "response_type": "ai_generated",
                "patient_data_provided": true/false
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "response": "Please provide a message.",
                "metadata": {"bot_type": "doctor", "response_type": "error"}
            }), 400
        
        user_message = data.get('message', '').strip()
        patient_data = data.get('patient_data', {})  # Optional patient context
        
        if not user_message:
            return jsonify({
                "success": False,
                "response": "Message cannot be empty.",
                "metadata": {"bot_type": "doctor", "response_type": "error"}
            }), 400
        
        # ============================================================
        # DOCTOR VERIFICATION (already done by @role_required decorator)
        # ============================================================
        doctor_id = session.get('user_id')
        doctor_name = session.get('full_name', 'Doctor')
        
        # ============================================================
        # STEP 1: RAG - Retrieve medical knowledge if needed
        # ============================================================
        relevant_knowledge = knowledge_base.search_knowledge(user_message, top_k=2)
        context_string = knowledge_base.get_context_string(relevant_knowledge)
        
        # ============================================================
        # STEP 2: Generate AI response with DOCTOR PROMPT
        # DATA ACCESS: Doctor chatbot receives provided patient data only
        # ============================================================
        ai_result = get_gemini_response(
            user_message=user_message,
            system_prompt=DOCTOR_PROMPT,  # Clinical support prompt
            context=context_string,
            patient_data=patient_data if patient_data else None
        )
        
        if not ai_result["success"]:
            return jsonify({
                "success": True,
                "response": "Clinical assistant temporarily unavailable. Please rely on your clinical judgment and hospital protocols.",
                "metadata": {
                    "bot_type": "doctor",
                    "response_type": "fallback",
                    "ai_error": ai_result["metadata"].get("error")
                }
            })
        
        # ============================================================
        # STEP 3: Return response with metadata
        # ============================================================
        return jsonify({
            "success": True,
            "response": ai_result["response"],
            "metadata": {
                **ai_result["metadata"],
                "bot_type": "doctor",
                "doctor_id": doctor_id,
                "patient_data_provided": bool(patient_data),
                "context_retrieved": len(relevant_knowledge) > 0
            }
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "response": "An unexpected error occurred. Please rely on your clinical judgment.",
            "metadata": {
                "bot_type": "doctor",
                "response_type": "error",
                "error": str(e)
            }
        }), 500


@chatbot_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint for chatbot service"""
    return jsonify({
        "status": "healthy",
        "service": "dual_chatbot_system",
        "bots": ["patient", "doctor"],
        "timestamp": datetime.utcnow().isoformat()
    })


@chatbot_bp.route('/knowledge-base-stats', methods=['GET'])
def knowledge_stats():
    """Get statistics about knowledge base (for monitoring/debugging)"""
    total_items = sum(len(qa_list) for qa_list in knowledge_base.knowledge.values())
    
    return jsonify({
        "total_items": total_items,
        "categories": list(knowledge_base.knowledge.keys()),
        "items_per_category": {
            category: len(qa_list) 
            for category, qa_list in knowledge_base.knowledge.items()
        }
    })
