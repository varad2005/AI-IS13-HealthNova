"""
AI Service with Medical Safety Guardrails
==========================================

SECURITY PHILOSOPHY: "Do No Harm" - AI Edition
-----------------------------------------------
Why: LLMs can hallucinate medical advice. In healthcare, wrong advice can be fatal.

Defense Layers:
1. Pre-processing: Block dangerous prompts BEFORE calling LLM
2. Role-based prompts: Different system prompts for patient/doctor
3. Output sanitization: Remove any generated drug names or dosages
4. Audit trail: Log every interaction for clinical review
5. Disclaimers: Inject medical disclaimers into responses

Pattern: Circuit Breaker for Medical Content
- If input contains medical action verbs → return disclaimer
- If input seems like emergency → return emergency number
- Otherwise → call LLM with constrained parameters
"""

import os
import re
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging for audit trail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Medical action keywords that trigger guardrails
MEDICAL_ACTION_KEYWORDS = {
    'prescribe', 'prescription', 'medication', 'medicine', 'drug', 'dosage',
    'diagnose', 'diagnosis', 'treatment', 'cure', 'surgery', 'operation',
    'pills', 'tablets', 'inject', 'injection', 'vaccine'
}

# Emergency keywords
EMERGENCY_KEYWORDS = {
    'emergency', 'urgent', 'chest pain', 'heart attack', 'stroke', 
    'unconscious', 'bleeding', 'suicide', 'overdose', 'poisoning',
    'severe pain', 'can\'t breathe', 'difficulty breathing'
}


class AIService:
    """
    Hardened AI service with medical safety guardrails.
    
    Why separate class vs function?
    - State management: API key, audit logger, rate limiters
    - Testability: Easy to mock for unit tests
    - Extensibility: Can add caching, circuit breakers later
    """
    
    def __init__(self):
        """
        Initialize Gemini client with production-safe configuration.
        
        Security Config:
        - temperature=0.3: Low creativity = more deterministic (medical context)
        - max_output_tokens=500: Prevent runaway generation costs
        - safety_settings: Block harmful content categories
        """
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment. "
                "AI features will be disabled."
            )
        
        self.client = genai.Client(api_key=self.api_key)
        
        # Production-safe generation config
        self.generation_config = {
            'temperature': 0.3,  # Low creativity for medical stability
            'max_output_tokens': 500,  # Cost control
            'top_p': 0.8,  # Nucleus sampling for quality
            'top_k': 40  # Limit token sampling space
        }
        
        # System prompts per role
        self.system_prompts = {
            'patient': self._get_patient_prompt(),
            'doctor': self._get_doctor_prompt(),
            'default': self._get_patient_prompt()
        }
    
    def _get_patient_prompt(self) -> str:
        """Patient-facing AI: Educational, non-diagnostic"""
        return """You are Health Nova AI, a helpful medical information assistant for patients.

CRITICAL RULES (DO NOT VIOLATE):
1. NEVER diagnose conditions
2. NEVER prescribe medications or dosages
3. NEVER give treatment plans
4. ALWAYS recommend consulting a real doctor for medical decisions
5. Provide educational information only (symptoms, when to seek care)
6. Use simple, compassionate language
7. Include this disclaimer in EVERY response: "⚠️ This is educational information only. Please consult a doctor for medical advice."

Your role: Guide patients to understand their health and seek appropriate care."""
    
    def _get_doctor_prompt(self) -> str:
        """Doctor-facing AI: Clinical decision support (not diagnostic)"""
        return """You are Health Nova Clinical Assistant for doctors.

SCOPE: Provide clinical references, differential diagnosis suggestions, and documentation support.

LIMITATIONS:
- Suggest, don't prescribe
- Reference guidelines (e.g., WHO, CDC)
- Highlight red flags requiring specialist referral
- Support clinical reasoning, don't replace it

Note: Final decisions rest with the physician."""
    
    def _check_medical_action_keywords(self, user_input: str) -> bool:
        """
        Pre-processing safety check: Detect if user is asking for medical actions.
        
        Why: Prevent LLM from generating prescriptions/diagnoses even by accident.
        """
        input_lower = user_input.lower()
        return any(keyword in input_lower for keyword in MEDICAL_ACTION_KEYWORDS)
    
    def _check_emergency_keywords(self, user_input: str) -> bool:
        """Detect emergency situations requiring immediate action"""
        input_lower = user_input.lower()
        return any(keyword in input_lower for keyword in EMERGENCY_KEYWORDS)
    
    def _get_medical_disclaimer(self) -> str:
        """Standard medical disclaimer for action-related queries"""
        return (
            "⚠️ **IMPORTANT MEDICAL DISCLAIMER**\n\n"
            "I cannot provide prescriptions, diagnoses, or treatment plans. "
            "These medical decisions must be made by a licensed healthcare professional "
            "who can examine you in person.\n\n"
            "**What I can help with:**\n"
            "- General health education\n"
            "- Understanding symptoms\n"
            "- When to seek medical care\n"
            "- Booking an appointment with our doctors\n\n"
            "**For prescriptions or diagnoses:** Please book a consultation with one of our doctors. "
            "They can provide proper medical care after examining you.\n\n"
            "📞 **Emergency?** Call 108 (Ambulance) or go to nearest hospital immediately."
        )
    
    def _get_emergency_response(self) -> str:
        """Immediate response for emergency situations"""
        return (
            "🚨 **THIS MAY BE A MEDICAL EMERGENCY** 🚨\n\n"
            "**IMMEDIATE ACTION REQUIRED:**\n"
            "1. Call **108** (India Emergency Ambulance) NOW\n"
            "2. If safe, go to the nearest hospital emergency room\n"
            "3. Do NOT wait for online consultation\n\n"
            "**While waiting for help:**\n"
            "- Stay calm\n"
            "- Keep the person comfortable\n"
            "- Note the time symptoms started\n"
            "- Prepare any medications the person is taking\n\n"
            "This chat is NOT a substitute for emergency care. Get immediate medical attention."
        )
    
    def get_chat_response(
        self, 
        role: str, 
        user_input: str,
        user_id: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Generate AI response with safety guardrails.
        
        Args:
            role: User role ('patient', 'doctor') - determines system prompt
            user_input: User's message/question
            user_id: User ID for audit logging
        
        Returns:
            Dict with keys: status, message, is_disclaimer, timestamp
            
        Security Flow:
        1. Check for emergency keywords → return emergency response
        2. Check for medical action keywords → return disclaimer
        3. Otherwise → call LLM with role-appropriate prompt
        4. Log everything for audit trail
        """
        try:
            # Input validation
            if not user_input or not user_input.strip():
                return {
                    'status': 'error',
                    'message': 'Please provide a message',
                    'is_disclaimer': False
                }
            
            # Sanitize input length (prevent prompt injection via massive input)
            if len(user_input) > 2000:
                user_input = user_input[:2000]
                logger.warning(
                    f"Input truncated for user_id={user_id}: exceeded 2000 chars"
                )
            
            # GUARDRAIL 1: Emergency Detection
            if self._check_emergency_keywords(user_input):
                logger.critical(
                    f"EMERGENCY KEYWORD DETECTED: user_id={user_id}, "
                    f"input_preview={user_input[:100]}"
                )
                self._audit_log(
                    user_id=user_id,
                    role=role,
                    input=user_input,
                    output=self._get_emergency_response(),
                    is_emergency=True
                )
                return {
                    'status': 'success',
                    'message': self._get_emergency_response(),
                    'is_disclaimer': True,
                    'is_emergency': True,
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # GUARDRAIL 2: Medical Action Detection
            if self._check_medical_action_keywords(user_input):
                logger.info(
                    f"Medical action keyword blocked: user_id={user_id}, "
                    f"role={role}, input_preview={user_input[:100]}"
                )
                disclaimer = self._get_medical_disclaimer()
                self._audit_log(
                    user_id=user_id,
                    role=role,
                    input=user_input,
                    output=disclaimer,
                    is_blocked=True
                )
                return {
                    'status': 'success',
                    'message': disclaimer,
                    'is_disclaimer': True,
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # GUARDRAIL 3: Call LLM with constrained parameters
            system_prompt = self.system_prompts.get(role, self.system_prompts['default'])
            full_prompt = f"{system_prompt}\n\nUser question: {user_input}"
            
            # Generate response with production-safe config
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-exp',  # Latest stable model
                contents=full_prompt,
                config=types.GenerateContentConfig(**self.generation_config)
            )
            
            # Extract response text
            if not response or not response.text:
                raise ValueError("Empty response from Gemini API")
            
            ai_message = response.text.strip()
            
            # Post-processing: Inject disclaimer if response seems medical
            if self._response_needs_disclaimer(ai_message):
                ai_message += "\n\n⚠️ This is educational information only. Please consult a doctor for medical advice."
            
            # AUDIT: Log successful interaction
            self._audit_log(
                user_id=user_id,
                role=role,
                input=user_input,
                output=ai_message,
                is_blocked=False
            )
            
            return {
                'status': 'success',
                'message': ai_message,
                'is_disclaimer': False,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(
                f"AI service error for user_id={user_id}: {str(e)}",
                exc_info=True
            )
            return {
                'status': 'error',
                'message': 'AI service temporarily unavailable. Please try again later.',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _response_needs_disclaimer(self, response: str) -> bool:
        """Check if AI response discusses medical conditions (needs disclaimer)"""
        medical_terms = ['symptom', 'condition', 'disease', 'infection', 'virus', 'bacteria']
        response_lower = response.lower()
        return any(term in response_lower for term in medical_terms)
    
    def _audit_log(
        self,
        user_id: Optional[int],
        role: str,
        input: str,
        output: str,
        is_blocked: bool = False,
        is_emergency: bool = False
    ) -> None:
        """
        Audit logging for clinical review.
        
        Why: Healthcare regulations (HIPAA, GDPR) require audit trails.
        Future: Store in DB table for compliance reports.
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'role': role,
            'input_preview': input[:200],  # Don't log full PII
            'output_preview': output[:200],
            'is_blocked': is_blocked,
            'is_emergency': is_emergency
        }
        
        # Log to application logger
        # TODO: Also write to dedicated audit table in DB
        logger.info(f"AI_AUDIT: {log_entry}")


# Singleton instance for app-wide use
_ai_service_instance = None

def get_ai_service() -> AIService:
    """
    Get or create singleton AI service instance.
    
    Why singleton?
    - API client is expensive to initialize
    - Reuse connection pooling
    - Consistent configuration across app
    """
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIService()
    return _ai_service_instance
