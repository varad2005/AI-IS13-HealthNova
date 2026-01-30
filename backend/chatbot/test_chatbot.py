"""
Healthcare Chatbot - Test Script
Demonstrates all safety features, RAG, and response types
"""
import requests
import json
from datetime import datetime


BASE_URL = "http://127.0.0.1:5000/chatbot"


def print_separator():
    print("\n" + "="*80 + "\n")


def test_chatbot(message, test_name):
    """Send message to chatbot and display results"""
    print(f"🧪 TEST: {test_name}")
    print(f"📝 User Message: \"{message}\"")
    print("-" * 80)
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"message": message},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Success: {data['success']}")
            print(f"\n💬 Chatbot Response:")
            print(data['response'])
            
            print(f"\n📊 Metadata:")
            for key, value in data.get('metadata', {}).items():
                print(f"   • {key}: {value}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    print_separator()


def run_comprehensive_tests():
    """Run all test scenarios"""
    
    print("="*80)
    print(" HEALTHCARE CHATBOT - COMPREHENSIVE TEST SUITE")
    print("="*80)
    print(f"⏰ Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_separator()
    
    # ========================================
    # TEST 1: Greeting (Rule-based)
    # ========================================
    test_chatbot(
        "Hello!",
        "Greeting Detection (Rule-based)"
    )
    
    # ========================================
    # TEST 2: Critical Emergency (Rule-based)
    # ========================================
    test_chatbot(
        "I'm having severe chest pain and can't breathe",
        "Critical Emergency Detection"
    )
    
    # ========================================
    # TEST 3: Urgent Situation (Rule-based)
    # ========================================
    test_chatbot(
        "I have very high fever and severe headache",
        "Urgent Situation Detection"
    )
    
    # ========================================
    # TEST 4: Diagnosis Request (Rule-based)
    # ========================================
    test_chatbot(
        "Do I have diabetes? My sugar is high",
        "Diagnosis Request Prevention"
    )
    
    # ========================================
    # TEST 5: Prescription Request (Rule-based)
    # ========================================
    test_chatbot(
        "What medicine should I take for my headache?",
        "Prescription Request Prevention"
    )
    
    # ========================================
    # TEST 6: Appointment Booking (RAG + AI)
    # ========================================
    test_chatbot(
        "How can I book an appointment with a doctor?",
        "Appointment Booking (RAG + AI)"
    )
    
    # ========================================
    # TEST 7: Lab Tests (RAG + AI)
    # ========================================
    test_chatbot(
        "How do I get my lab test results?",
        "Lab Test Information (RAG + AI)"
    )
    
    # ========================================
    # TEST 8: Medical History (RAG + AI)
    # ========================================
    test_chatbot(
        "Where can I see my medical history?",
        "Medical History Access (RAG + AI)"
    )
    
    # ========================================
    # TEST 9: Video Consultation (RAG + AI)
    # ========================================
    test_chatbot(
        "How does video consultation work?",
        "Video Consultation Information (RAG + AI)"
    )
    
    # ========================================
    # TEST 10: General Symptoms (AI with guidance)
    # ========================================
    test_chatbot(
        "I have a mild fever and cold. What should I do?",
        "General Symptom Guidance (AI)"
    )
    
    # ========================================
    # TEST 11: Mental Health (AI with empathy)
    # ========================================
    test_chatbot(
        "I'm feeling very anxious and stressed lately",
        "Mental Health Support (AI)"
    )
    
    # ========================================
    # TEST 12: Platform Features (AI)
    # ========================================
    test_chatbot(
        "What features are available on this platform?",
        "Platform Features Overview (AI)"
    )
    
    print("="*80)
    print(" ALL TESTS COMPLETED")
    print("="*80)
    print(f"⏰ Test Ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n✅ Review the metadata for each response to see:")
    print("   • response_type: rule_based | ai_generated | fallback")
    print("   • safety_check: passed | emergency | inappropriate")
    print("   • context_retrieved: whether RAG found relevant info")
    print("="*80)


def check_service_health():
    """Check if chatbot service is running"""
    print("🔍 Checking chatbot service health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Chatbot service is healthy!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"⚠️ Service returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to chatbot service: {str(e)}")
        print("\n💡 Make sure the Flask server is running:")
        print("   cd backend && python app.py")
    print_separator()


def check_knowledge_base():
    """Check knowledge base statistics"""
    print("📚 Checking knowledge base statistics...")
    try:
        response = requests.get(f"{BASE_URL}/knowledge-base-stats")
        if response.status_code == 200:
            stats = response.json()
            print("✅ Knowledge Base Stats:")
            print(f"   Total Items: {stats['total_items']}")
            print(f"   Categories: {', '.join(stats['categories'])}")
            print(f"\n   Items per Category:")
            for category, count in stats['items_per_category'].items():
                print(f"      • {category}: {count} items")
        else:
            print(f"⚠️ Could not retrieve stats: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    print_separator()


if __name__ == "__main__":
    print("\n")
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║    HEALTHCARE CHATBOT - TESTING & DEMONSTRATION SCRIPT        ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print("\n")
    
    # Check service status first
    check_service_health()
    check_knowledge_base()
    
    # Ask user to proceed
    print("This script will test all chatbot features:")
    print("  1. Emergency detection")
    print("  2. Diagnosis/prescription prevention")
    print("  3. RAG (knowledge retrieval)")
    print("  4. AI responses with context injection")
    print("  5. Metadata tracking\n")
    
    proceed = input("Press ENTER to start tests (or 'q' to quit): ")
    if proceed.lower() != 'q':
        run_comprehensive_tests()
        
        print("\n💡 TIP: Check the terminal output to see:")
        print("   • Which responses were rule-based (instant)")
        print("   • Which used RAG + AI (context-aware)")
        print("   • Safety check results for each message")
        print("\n")
    else:
        print("Tests cancelled.")
