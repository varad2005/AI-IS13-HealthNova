import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("Gemini API configured with key")
else:
    print("Warning: GEMINI_API_KEY not found in environment")

def verify_gemini_connection():
    """
    Verify Gemini API connection and list available models.
    Called during server startup for diagnostics.
    """
    if not GEMINI_API_KEY:
        print("Gemini API: No API key configured")
        return False
    
    try:
        # Try to list available models
        models = genai.list_models()
        available = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        print(f"Gemini API: Connected successfully")
        print(f"  Available models: {', '.join(available[:3])}")
        return True
    except Exception as e:
        print(f"Gemini API: Connection failed - {str(e)}")
        return False

# System prompt for health context
SYSTEM_PROMPT = """You are Health Nova AI, a helpful and professional medical AI assistant. Your role is to:
1. Provide general health information and advice
2. Help understand symptoms (but always recommend professional consultation for diagnosis)
3. Offer wellness and preventive health tips
4. Guide users on booking appointments
5. Provide emergency guidance when needed

Important guidelines:
- Always be empathetic and supportive
- Never provide specific medical diagnosis - recommend consulting a doctor
- Use clear, simple language
- For serious symptoms, always advise seeing a doctor immediately
- Keep responses concise but informative (max 300 words)
- Add relevant emojis to make responses friendly
- If asked about booking appointments, guide them to the booking page
- For emergencies, provide the helpline: 108 (Ambulance)

Current context: You are assisting patients of Health Nova, a rural healthcare platform in India."""

def get_ai_response(user_message):
    """
    Get AI response from Google Gemini
    
    Args:
        user_message (str): User's question or message
        
    Returns:
        dict: Response with success status and message
    """
    if not GEMINI_API_KEY:
        return {
            'success': False,
            'message': get_fallback_response(user_message),
            'error': 'Gemini API key not configured'
        }
    
    try:
        # Create the full prompt with system context
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser question: {user_message}"
        
        # Generate response using Gemini 2.5 Flash
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(full_prompt)
        
        # Check if response has text
        if not response.text:
            return {
                'success': False,
                'message': 'I apologize, but I cannot provide a response to that query. Please rephrase your question or ask something else.',
                'error': 'Response blocked by safety filters'
            }
        
        return {
            'success': True,
            'message': response.text
        }
        
    except Exception as e:
        print(f"Gemini API Error: {str(e)}")
        
        # Return fallback response based on keywords
        return {
            'success': False,
            'message': get_fallback_response(user_message),
            'error': str(e)
        }

def get_fallback_response(message):
    """
    Provide fallback responses when Gemini API is unavailable
    
    Args:
        message (str): User's message
        
    Returns:
        str: Fallback response
    """
    message_lower = message.lower()
    
    if 'fever' in message_lower or 'temperature' in message_lower:
        return """🌡️ **Fever Management:**

Common fever symptoms:
• Body temperature above 100.4°F (38°C)
• Chills and shivering
• Headache and body aches
• Fatigue and weakness

**What you can do:**
✓ Rest and stay hydrated
✓ Take fever-reducing medication (paracetamol)
✓ Use cool compresses
✓ Monitor temperature regularly

⚠️ **See a doctor if:**
• Fever exceeds 103°F (39.4°C)
• Lasts more than 3 days
• Accompanied by severe symptoms

Would you like to book an appointment with a doctor?"""
    
    elif 'appointment' in message_lower or 'book' in message_lower:
        return """📅 **Book Your Appointment:**

I can help you schedule a consultation:

**Available Options:**
1️⃣ **Video Consultation** - Available 24/7
2️⃣ **In-Person Visit** - Next available slot: Tomorrow
3️⃣ **Specialist Consultation** - Based on your needs

**How to book:**
• Click on "Book Consultation" from your dashboard
• Select your preferred doctor and time slot
• Complete the booking

💡 Average consultation fee: ₹400-800

Would you like me to guide you through the booking process?"""
    
    elif 'health tip' in message_lower or 'wellness' in message_lower:
        return """💪 **Daily Health & Wellness Tips:**

🏃‍♂️ **Stay Active**
• 30 minutes of moderate exercise daily
• Walking, yoga, or home workouts

💧 **Hydration**
• Drink 8-10 glasses of water daily
• Limit sugary drinks

🥗 **Balanced Diet**
• Include fruits, vegetables, whole grains
• Reduce processed foods and sugar

😴 **Quality Sleep**
• 7-8 hours of sleep per night
• Maintain consistent sleep schedule

🧘‍♀️ **Stress Management**
• Practice meditation or deep breathing
• Take breaks during work

📊 **Regular Checkups**
• Annual health screenings
• Monitor blood pressure and blood sugar

Which area would you like more specific advice on?"""
    
    elif 'emergency' in message_lower or 'urgent' in message_lower:
        return """🚨 **EMERGENCY GUIDANCE:**

**For Immediate Medical Emergency:**
📞 **Call: 108** (Ambulance - India)
📞 **Emergency: 102**

**Warning Signs - Call Immediately:**
• Chest pain or pressure
• Difficulty breathing
• Severe bleeding
• Loss of consciousness
• Severe head injury
• Suspected stroke (face drooping, arm weakness, speech difficulty)
• Severe allergic reaction

**Health Nova Emergency:**
📍 **Nearest Facility:** Health Nova Medical Center
🚗 **Distance:** 2.3 km
⏰ **24/7 Emergency Services**

For non-life-threatening issues, you can:
• Book an urgent video consultation
• Visit walk-in clinic

Are you currently experiencing a medical emergency?"""
    
    elif 'checkup' in message_lower or 'package' in message_lower:
        return """🏥 **Health Checkup Packages:**

**Basic Screening - ₹999**
• Complete Blood Count
• Blood Sugar (Fasting)
• Lipid Profile
• Liver Function Test

**Comprehensive - ₹2,499**
• All Basic tests +
• Thyroid Profile
• Kidney Function Test
• Vitamin D & B12
• ECG

**Premium Full Body - ₹4,999**
• All Comprehensive tests +
• Ultrasound Abdomen
• Chest X-Ray
• Stress Test
• Cancer Markers

🎁 **Special Offer:** 40% OFF until Jan 31, 2026

📋 All reports available in 24-48 hours

Would you like to book a health checkup?"""
    
    else:
        return """Thank you for your question! 😊

I'm here to help with:
• **Health Information** - Symptoms, conditions, general advice
• **Appointments** - Book consultations with doctors
• **Wellness Tips** - Diet, exercise, preventive care
• **Emergency Guidance** - What to do in urgent situations
• **Health Packages** - Checkup and screening options

Could you please provide more details about what you'd like to know? I'll do my best to assist you!

💡 **Pro Tip:** The more specific your question, the better I can help you."""
