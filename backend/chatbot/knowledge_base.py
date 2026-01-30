"""
Knowledge Base for Healthcare Chatbot
Implements simple RAG (Retrieval-Augmented Generation) using predefined FAQs
"""
import re
from typing import List, Dict, Tuple

# Healthcare FAQs organized by category
HEALTHCARE_KNOWLEDGE = {
    "appointments": [
        {
            "question": "How do I book an appointment?",
            "answer": "You can book an appointment through your patient dashboard. Navigate to 'Book Appointment', select a doctor, choose an available time slot, and confirm your booking.",
            "keywords": ["book", "appointment", "schedule", "doctor visit"]
        },
        {
            "question": "Can I cancel or reschedule my appointment?",
            "answer": "Yes! Go to your dashboard, find your upcoming appointment, and click 'Cancel' or 'Reschedule'. Please try to give at least 24 hours notice.",
            "keywords": ["cancel", "reschedule", "change appointment"]
        },
        {
            "question": "How do I start a video consultation?",
            "answer": "During your scheduled appointment time, go to your dashboard and click 'Start Video Consultation'. Make sure your camera and microphone are working. The doctor will provide a room ID.",
            "keywords": ["video", "consultation", "online", "teleconsultation", "video call"]
        }
    ],
    
    "lab_tests": [
        {
            "question": "How do I get lab test results?",
            "answer": "Lab results are automatically uploaded to your dashboard once ready. You'll receive a notification. You can view and download reports from the 'Lab Reports' section.",
            "keywords": ["lab", "test", "results", "report", "blood test"]
        },
        {
            "question": "What lab tests are available?",
            "answer": "We offer blood tests (CBC, sugar, cholesterol), urine tests, X-rays, ECG, and more. Your doctor will recommend appropriate tests based on your symptoms.",
            "keywords": ["available tests", "test types", "lab services"]
        },
        {
            "question": "How long do test results take?",
            "answer": "Most blood tests: 24-48 hours. X-rays/ECG: Same day. Specialized tests may take 3-5 days. Urgent tests are prioritized.",
            "keywords": ["how long", "test duration", "wait time"]
        }
    ],
    
    "platform_features": [
        {
            "question": "How do I access my medical history?",
            "answer": "Go to your patient dashboard and click on 'Medical History' or 'My Records'. You'll see your complete timeline of visits, prescriptions, and test results.",
            "keywords": ["medical history", "records", "past visits", "prescription history"]
        },
        {
            "question": "Is my data secure and private?",
            "answer": "Yes! We use industry-standard encryption for all data. Only you and your healthcare providers can access your medical records. We comply with healthcare privacy regulations.",
            "keywords": ["privacy", "security", "data protection", "confidential"]
        },
        {
            "question": "How do I contact support?",
            "answer": "You can call our 24/7 helpline at 1800-XXX-XXXX or use the 'Help' section in your dashboard to send a message. Emergency medical issues should call emergency services.",
            "keywords": ["support", "help", "contact", "customer service"]
        }
    ],
    
    "symptoms_guidance": [
        {
            "question": "I have a fever. What should I do?",
            "answer": "For mild fever (under 102°F): Rest, stay hydrated, and monitor your temperature. If fever persists for more than 3 days, is above 103°F, or you have severe symptoms, please consult a doctor immediately through our platform.",
            "keywords": ["fever", "temperature", "hot"]
        },
        {
            "question": "I have a headache. Is it serious?",
            "answer": "Most headaches are not serious. Try resting in a dark room and staying hydrated. However, seek immediate medical help if you have: sudden severe headache, headache with fever/stiff neck, vision changes, or confusion.",
            "keywords": ["headache", "head pain", "migraine"]
        },
        {
            "question": "I'm feeling anxious or stressed.",
            "answer": "Mental health is important! Try deep breathing, regular exercise, and adequate sleep. If anxiety persists or interferes with daily life, please book an appointment with a doctor. We support mental health consultations.",
            "keywords": ["anxiety", "stress", "worried", "mental health", "depression"]
        },
        {
            "question": "I have cold or cough symptoms.",
            "answer": "For common cold: Rest, drink fluids, and use steam inhalation. Most colds resolve in 7-10 days. Seek medical help if: difficulty breathing, high fever, symptoms worsen after 10 days, or chest pain occurs.",
            "keywords": ["cold", "cough", "flu", "sneeze", "runny nose"]
        }
    ],
    
    "general_health": [
        {
            "question": "How can I maintain good health?",
            "answer": "Focus on: balanced diet with fruits and vegetables, regular exercise (30 min daily), adequate sleep (7-8 hours), staying hydrated, regular health checkups, and managing stress.",
            "keywords": ["healthy lifestyle", "wellness", "prevention", "stay healthy"]
        },
        {
            "question": "When should I get a health checkup?",
            "answer": "Adults should get annual checkups. If you have chronic conditions, more frequent visits may be needed. Book a checkup through our platform if you haven't had one recently.",
            "keywords": ["checkup", "health screening", "routine examination"]
        }
    ]
}

# Emergency keywords that require immediate escalation
EMERGENCY_KEYWORDS = {
    "critical": ["chest pain", "difficulty breathing", "can't breathe", "suicide", "kill myself", 
                 "severe bleeding", "unconscious", "stroke", "heart attack", "seizure"],
    "urgent": ["severe pain", "broken bone", "high fever", "vomiting blood", "bleeding heavily"]
}


class KnowledgeBase:
    """Simple RAG system using keyword matching and similarity"""
    
    def __init__(self):
        self.knowledge = HEALTHCARE_KNOWLEDGE
        self.emergency_keywords = EMERGENCY_KEYWORDS
        
    def search_knowledge(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Search knowledge base using keyword matching
        Returns top-k most relevant Q&A pairs
        """
        query_lower = query.lower()
        results = []
        
        # Search across all categories
        for category, qa_list in self.knowledge.items():
            for qa in qa_list:
                # Calculate relevance score based on keyword matches
                score = 0
                for keyword in qa["keywords"]:
                    if keyword in query_lower:
                        score += 1
                
                # Add partial word matches
                query_words = set(re.findall(r'\w+', query_lower))
                keyword_words = set(' '.join(qa["keywords"]).split())
                common_words = query_words & keyword_words
                score += len(common_words) * 0.5
                
                if score > 0:
                    results.append({
                        "category": category,
                        "question": qa["question"],
                        "answer": qa["answer"],
                        "score": score
                    })
        
        # Sort by relevance score and return top-k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    def get_context_string(self, relevant_items: List[Dict]) -> str:
        """
        Format retrieved knowledge into context string for prompt injection
        """
        if not relevant_items:
            return "No specific knowledge base matches found."
        
        context_parts = ["Relevant information from knowledge base:"]
        for idx, item in enumerate(relevant_items, 1):
            context_parts.append(f"\n{idx}. Q: {item['question']}")
            context_parts.append(f"   A: {item['answer']}")
        
        return "\n".join(context_parts)
    
    def get_all_platform_features(self) -> str:
        """
        Get comprehensive platform feature list for context
        """
        features = [
            "Platform Features Available:",
            "- Book appointments with doctors",
            "- Video consultations with doctors",
            "- View and manage lab test results",
            "- Access complete medical history timeline",
            "- Upload and download medical reports",
            "- Secure messaging with healthcare providers",
            "- Prescription management",
            "- Health records management"
        ]
        return "\n".join(features)


# Singleton instance
knowledge_base = KnowledgeBase()
