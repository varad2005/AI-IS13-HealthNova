"""
Safety Checks Module
Implements rule-based checks for medical emergencies and safety filtering
"""
import re
from typing import Dict, Optional


class SafetyChecker:
    """
    Rule-based safety checks before AI processing
    Detects medical emergencies and inappropriate queries
    """
    
    # Emergency keywords requiring immediate action
    EMERGENCY_KEYWORDS = [
        "chest pain", "heart attack", "can't breathe", "difficulty breathing",
        "severe bleeding", "bleeding heavily", "unconscious", "unresponsive",
        "stroke", "seizure", "convulsion", "suicide", "kill myself",
        "overdose", "poisoning", "choking", "severe burn",
        "broken bone", "severe injury", "car accident"
    ]
    
    # Urgent keywords requiring quick medical attention
    URGENT_KEYWORDS = [
        "severe pain", "high fever", "vomiting blood", "blood in urine",
        "severe headache", "vision loss", "paralysis", "can't move",
        "severe allergic", "anaphylaxis", "swelling throat"
    ]
    
    # Medical advice requests that should be escalated
    DIAGNOSIS_KEYWORDS = [
        "do i have", "is this", "diagnose", "what disease",
        "what's wrong with me", "why do i have", "what condition"
    ]
    
    PRESCRIPTION_KEYWORDS = [
        "what medicine", "what medication", "prescribe", "what drug",
        "should i take", "how much dosage", "medicine for"
    ]
    
    def __init__(self):
        self.emergency_keywords = self.EMERGENCY_KEYWORDS
        self.urgent_keywords = self.URGENT_KEYWORDS
        self.diagnosis_keywords = self.DIAGNOSIS_KEYWORDS
        self.prescription_keywords = self.PRESCRIPTION_KEYWORDS
    
    def check_emergency(self, message: str) -> Dict:
        """
        Check if message contains emergency keywords
        Returns emergency response if detected
        """
        message_lower = message.lower()
        
        # Check for critical emergencies
        for keyword in self.emergency_keywords:
            if keyword in message_lower:
                return {
                    "is_emergency": True,
                    "severity": "CRITICAL",
                    "matched_keyword": keyword,
                    "response": self._get_emergency_response(),
                    "metadata": {
                        "rule_triggered": "emergency_detection",
                        "response_type": "rule_based"
                    }
                }
        
        # Check for urgent situations
        for keyword in self.urgent_keywords:
            if keyword in message_lower:
                return {
                    "is_emergency": True,
                    "severity": "URGENT",
                    "matched_keyword": keyword,
                    "response": self._get_urgent_response(),
                    "metadata": {
                        "rule_triggered": "urgent_detection",
                        "response_type": "rule_based"
                    }
                }
        
        return {
            "is_emergency": False,
            "severity": None,
            "matched_keyword": None,
            "response": None,
            "metadata": None
        }
    
    def check_inappropriate_request(self, message: str) -> Optional[Dict]:
        """
        Check if user is asking for diagnosis or prescription
        Returns warning response if detected
        """
        message_lower = message.lower()
        
        # Check for diagnosis requests
        for keyword in self.diagnosis_keywords:
            if keyword in message_lower:
                return {
                    "is_inappropriate": True,
                    "type": "diagnosis_request",
                    "response": self._get_diagnosis_warning(),
                    "metadata": {
                        "rule_triggered": "diagnosis_prevention",
                        "response_type": "rule_based"
                    }
                }
        
        # Check for prescription requests
        for keyword in self.prescription_keywords:
            if keyword in message_lower:
                return {
                    "is_inappropriate": True,
                    "type": "prescription_request",
                    "response": self._get_prescription_warning(),
                    "metadata": {
                        "rule_triggered": "prescription_prevention",
                        "response_type": "rule_based"
                    }
                }
        
        return None
    
    def _get_emergency_response(self) -> str:
        """Emergency response template"""
        return """🚨 **MEDICAL EMERGENCY DETECTED**

This appears to be a medical emergency. Please:

1. **CALL EMERGENCY SERVICES IMMEDIATELY: 112 or 108**
2. If in hospital, alert nearby medical staff
3. Do NOT wait for online consultation

**Our platform is NOT for emergencies.**

For urgent medical help:
- Emergency Hotline: 112 / 108
- Our 24/7 Support: 1800-XXX-XXXX

If this is NOT an emergency, you can book an urgent video consultation through your dashboard."""
    
    def _get_urgent_response(self) -> str:
        """Urgent situation response template"""
        return """⚠️ **URGENT MEDICAL ATTENTION NEEDED**

Your symptoms suggest you need prompt medical evaluation.

**Recommended actions:**
1. Book an URGENT video consultation through your dashboard
2. If symptoms worsen, call emergency services: 112 / 108
3. Consider visiting nearest healthcare facility

**Do not delay medical care.**

Would you like help booking an urgent appointment?"""
    
    def _get_diagnosis_warning(self) -> str:
        """Warning for diagnosis requests"""
        return """I understand you're concerned about your health, but I cannot provide medical diagnoses. 

**Here's what I can help with:**
- Book an appointment with a qualified doctor
- Explain our platform features
- Provide general health information
- Guide you to appropriate care

**For proper diagnosis:**
Please consult with a doctor through our platform. They can:
- Review your symptoms thoroughly
- Order necessary tests
- Provide accurate diagnosis
- Create treatment plan

Would you like to book a consultation?"""
    
    def _get_prescription_warning(self) -> str:
        """Warning for prescription requests"""
        return """I cannot recommend or prescribe medications. Only licensed doctors can prescribe medicine after proper evaluation.

**Why this matters:**
- Wrong medication can be dangerous
- Dosage must be personalized
- Drug interactions need assessment
- Medical history must be reviewed

**What you should do:**
1. Book a video consultation with a doctor
2. Doctor will evaluate your condition
3. Receive proper prescription if needed
4. Access prescription in your dashboard

Would you like help booking an appointment with a doctor?"""
    
    def is_greeting(self, message: str) -> bool:
        """Check if message is a simple greeting"""
        greetings = ["hi", "hello", "hey", "good morning", "good evening", "good afternoon"]
        message_lower = message.lower().strip()
        return message_lower in greetings or any(message_lower.startswith(g) for g in greetings)
    
    def get_greeting_response(self) -> str:
        """Friendly greeting response"""
        return """Hello! 👋 I'm your Health Nova assistant.

I'm here to help you with:
- Booking appointments with doctors
- Understanding lab tests and results
- Navigating our platform features
- General health guidance
- Video consultation support

**Important:** I cannot diagnose conditions or prescribe medications. For medical advice, please consult with our doctors.

How can I assist you today?"""


# Singleton instance
safety_checker = SafetyChecker()
