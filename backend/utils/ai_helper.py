"""
AI Helper - Google Gemini Integration

Provides basic health awareness using Google Gemini API.

Safety Rules:
- No medical diagnosis
- No medicine prescriptions  
- General guidance only
- Always suggests consulting real doctors

Rate Limiting: No custom rate limiting implemented. 
Relies on Google Gemini API's provider-level rate limits.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("OK: Gemini API configured successfully")
else:
    print("Warning: GEMINI_API_KEY not found in environment variables")


# Gemini prompt with safety instructions
HEALTH_GUIDANCE_PROMPT = """You are a health awareness assistant for Health Nova.

Rules:
1. Do NOT diagnose any condition
2. Do NOT prescribe medicines
3. Do NOT suggest specific treatments
4. Always tell user to consult a real doctor
5. Use simple language
6. Be kind and supportive

User's concern: {user_text}

Provide general health awareness (2-3 paragraphs). Keep it simple and caring. Always remind them to see a doctor.
"""


def get_ai_guidance(user_text: str) -> str:
    """
    Get health awareness guidance from Google Gemini.
    
    Args:
        user_text: User's health concern
    
    Returns:
        AI response with general health awareness
        or fallback message if API fails
    """
    
    # Check for empty input
    if not user_text or not user_text.strip():
        return "Please describe your health concern so I can provide some guidance."
    
    # Check if API key is configured
    if not GEMINI_API_KEY:
        return _get_fallback_message()
    
    try:
        # Create prompt with safety guidelines
        full_prompt = HEALTH_GUIDANCE_PROMPT.format(user_text=user_text.strip())
        
        # Create model instance
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Generate response
        response = model.generate_content(
            full_prompt,
            generation_config={
                'temperature': 0.7,
                'max_output_tokens': 500,
            }
        )
        
        # Extract and return text
        if response and response.text:
            return response.text.strip()
        else:
            return _get_fallback_message()
    
    except Exception as e:
        # Log error (in production, use proper logging)
        print(f"Gemini API Error: {str(e)}")
        return _get_fallback_message()


def _get_fallback_message() -> str:
    """Return safe message when AI is unavailable."""
    return (
        "Thank you for your message. While our AI assistant is currently unavailable, "
        "please note:\n\n"
        "• Your symptoms have been recorded\n"
        "• A doctor will review your case\n"
        "• For urgent issues, visit the nearest health center\n\n"
        "This platform connects you with real doctors. Stay safe!"
    )


def get_symptom_summary(symptoms: str) -> str:
    """
    Generate a brief summary of symptoms (helps doctors review cases faster).
    
    Args:
        symptoms: Patient's symptom description
    
    Returns:
        Brief summary (1-2 sentences) or original if AI fails
    """
    
    if not symptoms or not symptoms.strip():
        return "No symptoms provided"
    
    if not GEMINI_API_KEY:
        return symptoms[:100] + "..." if len(symptoms) > 100 else symptoms
    
    try:
        prompt = f"""Summarize these patient symptoms in 1-2 clear sentences. 
        Do NOT diagnose. Just describe what the patient is experiencing.
        
        Symptoms: {symptoms.strip()}
        
        Summary (1-2 sentences only):"""
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.3,
                'max_output_tokens': 100,
            }
        )
        
        if response and response.text:
            return response.text.strip()
        else:
            return symptoms[:100] + "..." if len(symptoms) > 100 else symptoms
    
    except Exception as e:
        print(f"Gemini Summary Error: {str(e)}")
        # Return truncated symptoms as fallback
        return symptoms[:100] + "..." if len(symptoms) > 100 else symptoms


# Test function (for development only)
def test_ai_helper():
    """
    Test the AI helper functions.
    Run this to verify Gemini integration is working.
    """
    print("="*60)
    print("🧪 Testing Gemini AI Integration")
    print("="*60)
    
    # Test 1: Get AI guidance
    print("\n📝 Test 1: AI Health Guidance")
    print("-" * 60)
    test_input = "I have fever and body pain for 2 days"
    guidance = get_ai_guidance(test_input)
    print(f"Input: {test_input}")
    print(f"Response:\n{guidance}\n")
    
    # Test 2: Get symptom summary
    print("📝 Test 2: Symptom Summary")
    print("-" * 60)
    symptoms = "Patient reports high fever (102°F), severe body ache, headache, and weakness. Symptoms started 2 days ago. No cough or cold. Has been taking paracetamol."
    summary = get_symptom_summary(symptoms)
    print(f"Original: {symptoms}")
    print(f"Summary: {summary}\n")
    
    # Test 3: Empty input
    print("📝 Test 3: Empty Input Handling")
    print("-" * 60)
    empty_guidance = get_ai_guidance("")
    print(f"Empty input response:\n{empty_guidance}\n")
    
    print("="*60)
    print("✅ Tests completed!")
    print("="*60)


if __name__ == "__main__":
    # Run tests when file is executed directly
    test_ai_helper()
