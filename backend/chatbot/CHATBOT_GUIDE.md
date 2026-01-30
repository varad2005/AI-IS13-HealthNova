# Healthcare Chatbot - Implementation Guide

## 🎯 Overview

A production-ready healthcare chatbot built with **Flask + Gemini API** that prioritizes safety through:
- Rule-based emergency detection
- Simple RAG (Retrieval-Augmented Generation)
- Strong system prompts
- No model training required

Perfect for hackathons and demos!

---

## 🏗️ Architecture

```
User Message
    ↓
1. SAFETY CHECKS (Rule-based)
    ├─ Emergency Detection → Immediate Response
    ├─ Greeting Detection → Friendly Response
    └─ Inappropriate Request → Warning
    ↓
2. RAG - Knowledge Retrieval
    └─ Search FAQs by keyword matching
    ↓
3. CONTEXT INJECTION
    └─ Inject retrieved context + system prompt
    ↓
4. GEMINI API CALL
    └─ Generate safe, context-aware response
    ↓
5. RETURN WITH METADATA
    └─ Response + metadata (type, safety status)
```

---

## 📁 File Structure

```
backend/chatbot/
├── __init__.py              # Blueprint registration
├── routes.py                # Main API endpoint + Gemini integration
├── knowledge_base.py        # RAG system with healthcare FAQs
├── safety_checks.py         # Rule-based safety filters
└── CHATBOT_GUIDE.md        # This file
```

---

## 🔒 Safety Features

### 1. **Emergency Detection**
Checks for critical keywords BEFORE AI processing:
- "chest pain", "can't breathe", "suicide", etc.
- Returns immediate emergency response
- Directs to emergency services (112/108)

### 2. **Diagnosis Prevention**
Detects when users ask for diagnosis:
- "do I have", "what disease", etc.
- Returns warning + redirects to doctor booking

### 3. **Prescription Prevention**
Blocks medication requests:
- "what medicine", "prescribe", etc.
- Explains only doctors can prescribe

### 4. **System Prompt Constraints**
AI is instructed to:
- NEVER diagnose conditions
- NEVER recommend medications
- ALWAYS escalate serious symptoms
- Stay within assistant role

---

## 💡 RAG Implementation

### Simple Keyword-Based Retrieval

```python
# knowledge_base.py
HEALTHCARE_KNOWLEDGE = {
    "appointments": [...],
    "lab_tests": [...],
    "symptoms_guidance": [...]
}

# Search by keyword matching
relevant_items = knowledge_base.search_knowledge(user_message, top_k=3)
```

### Context Injection

Retrieved knowledge is injected into prompt:
```
SYSTEM PROMPT
+ RETRIEVED CONTEXT
+ PLATFORM FEATURES
+ USER QUESTION
→ Gemini API
```

---

## 🚀 API Endpoint

### POST `/chatbot/chat`

**Request:**
```json
{
    "message": "How do I book an appointment?",
    "user_id": "optional",
    "session_id": "optional"
}
```

**Response:**
```json
{
    "success": true,
    "response": "You can book an appointment through your patient dashboard...",
    "metadata": {
        "response_type": "ai_generated",
        "safety_check": "passed",
        "context_retrieved": true,
        "knowledge_items_found": 2,
        "model": "gemini-1.5-flash"
    }
}
```

**Response Types:**
- `rule_based` - Emergency/greeting/safety response
- `ai_generated` - Gemini response with context
- `fallback` - Error fallback
- `error` - System error

---

## 🎯 System Prompt Highlights

```python
SYSTEM_PROMPT = """
You are a helpful healthcare assistant for Health Nova.

STRICT SAFETY RULES:
1. NEVER diagnose medical conditions
2. NEVER prescribe medications
3. ALWAYS escalate serious symptoms
4. Medical disclaimers in responses
5. Stay within assistant scope

YOUR CAPABILITIES:
- Explain platform features
- Guide through processes
- Provide general health info
- Show empathy and support

TONE: Friendly, professional, culturally sensitive
"""
```

---

## 🧪 Testing Examples

### Test 1: Emergency Detection (Rule-based)
```bash
curl -X POST http://127.0.0.1:5000/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I have severe chest pain"}'
```
**Expected:** Emergency response, NO AI call

---

### Test 2: Appointment Booking (RAG + AI)
```bash
curl -X POST http://127.0.0.1:5000/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I book an appointment?"}'
```
**Expected:** AI response with injected FAQ context

---

### Test 3: Diagnosis Request (Rule-based)
```bash
curl -X POST http://127.0.0.1:5000/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Do I have diabetes?"}'
```
**Expected:** Warning about not providing diagnosis

---

### Test 4: General Health Question (AI)
```bash
curl -X POST http://127.0.0.1:5000/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are symptoms of fever?"}'
```
**Expected:** AI response with symptom guidance from RAG

---

## 🔑 Environment Setup

Add to `.env` file:
```
GEMINI_API_KEY=your_api_key_here
```

Get API key: https://makersuite.google.com/app/apikey

---

## 📊 Metadata Explained

Every response includes metadata:

| Field | Values | Meaning |
|-------|--------|---------|
| `response_type` | `rule_based`, `ai_generated`, `fallback`, `error` | How response was generated |
| `safety_check` | `passed`, `emergency`, `inappropriate` | Safety check result |
| `context_retrieved` | `true`, `false` | Was RAG context found? |
| `knowledge_items_found` | number | How many FAQ items matched |
| `rule_triggered` | string | Which rule fired (if any) |

**Use metadata for:**
- Analytics and monitoring
- Understanding chatbot behavior
- Debugging issues
- Improving knowledge base

---

## 🎨 Frontend Integration

### Simple JavaScript Example

```javascript
async function sendMessage(message) {
    const response = await fetch('http://127.0.0.1:5000/chatbot/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
    });
    
    const data = await response.json();
    
    // Display response
    displayMessage(data.response);
    
    // Check metadata
    if (data.metadata.safety_check === 'emergency') {
        highlightAsUrgent();
    }
}
```

---

## 🚨 Important Notes

### What This Chatbot CAN Do:
✅ Guide users through platform features  
✅ Provide general health information  
✅ Help book appointments  
✅ Explain lab tests  
✅ Offer emotional support  
✅ Detect emergencies and escalate  

### What This Chatbot CANNOT Do:
❌ Diagnose medical conditions  
❌ Prescribe medications  
❌ Replace doctor consultations  
❌ Provide detailed medical procedures  
❌ Interpret test results  

---

## 🔄 How to Extend

### Add More FAQs
Edit `knowledge_base.py`:
```python
HEALTHCARE_KNOWLEDGE = {
    "new_category": [
        {
            "question": "Your question",
            "answer": "Your answer",
            "keywords": ["keyword1", "keyword2"]
        }
    ]
}
```

### Add More Safety Rules
Edit `safety_checks.py`:
```python
NEW_KEYWORDS = ["new", "emergency", "keywords"]
```

### Modify System Prompt
Edit `routes.py` → `SYSTEM_PROMPT` variable

---

## 📈 Performance Tips

1. **Use Gemini 1.5 Flash** - Fast, cost-effective
2. **Cache knowledge base** - Already done (singleton)
3. **Limit context injection** - top_k=3 is optimal
4. **Short system prompts** - Faster generation
5. **Rule-based first** - Avoid unnecessary AI calls

---

## 🎓 Key Concepts Explained

### 1. **Why Rule-based Checks First?**
- Faster response for emergencies
- No AI cost for simple queries
- 100% predictable for safety-critical cases
- Reduces liability

### 2. **Why Simple RAG (Not Vector DB)?**
- Sufficient for small knowledge base
- No additional dependencies
- Fast keyword matching
- Easy to debug and extend
- Perfect for hackathons

### 3. **Why System Prompt So Detailed?**
- Gemini needs clear constraints
- Safety requires explicit rules
- Reduces hallucinations
- Ensures consistent behavior

### 4. **Why Return Metadata?**
- Transparency in decision-making
- Analytics and monitoring
- Debugging and testing
- User trust (show reasoning)

---

## 🏆 Demo Script

**For judges/presentations:**

1. **Show Emergency Detection:**
   - Input: "I have chest pain"
   - Result: Instant emergency response (no AI delay)

2. **Show Diagnosis Prevention:**
   - Input: "Do I have COVID?"
   - Result: Polite refusal + doctor booking suggestion

3. **Show RAG in Action:**
   - Input: "How do I get my lab results?"
   - Result: Detailed answer from knowledge base

4. **Show Empathy:**
   - Input: "I'm feeling very anxious"
   - Result: Supportive response + mental health resources

5. **Check Metadata:**
   - Show response_type for each
   - Highlight safety_check status

---

## 🐛 Troubleshooting

**Q: "Chatbot is unavailable"**  
A: Check `GEMINI_API_KEY` in `.env`

**Q: "Emergency not detected"**  
A: Check exact keyword in `safety_checks.py`

**Q: "No context retrieved"**  
A: Add more keywords to FAQs in `knowledge_base.py`

**Q: "AI gives medical advice"**  
A: Strengthen system prompt, add more examples

---

## 📚 Resources

- **Gemini API Docs:** https://ai.google.dev/docs
- **Flask Docs:** https://flask.palletsprojects.com/
- **Medical AI Ethics:** https://www.who.int/publications/i/item/9789240029200

---

## ✅ Production Checklist

Before deploying:
- [ ] Test all emergency keywords
- [ ] Add rate limiting (prevent abuse)
- [ ] Log all conversations (for review)
- [ ] Add user feedback mechanism
- [ ] Set up monitoring alerts
- [ ] Add conversation history
- [ ] Implement session management
- [ ] Add human handoff option
- [ ] Test with real users
- [ ] Legal review of disclaimers

---

## 👨‍💻 Author Notes

This implementation prioritizes:
1. **Safety First** - Rule-based checks before AI
2. **Simplicity** - No complex ML infrastructure
3. **Transparency** - Metadata shows reasoning
4. **Extensibility** - Easy to add FAQs and rules
5. **Demo-Ready** - Works out of the box

**Perfect for:**
- Hackathons
- MVPs
- Proof of concepts
- Learning AI safety
- Healthcare demos

---

## 🎉 Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set API key in `.env`:
```
GEMINI_API_KEY=your_key_here
```

3. Start server:
```bash
python app.py
```

4. Test endpoint:
```bash
curl -X POST http://127.0.0.1:5000/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

**That's it! 🚀**
