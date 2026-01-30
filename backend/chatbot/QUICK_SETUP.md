# 🚀 Quick Setup Guide for Healthcare Chatbot

## ⚡ 3-Minute Setup

### Step 1: Get API Key (2 minutes)
1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the generated key

### Step 2: Configure Environment (30 seconds)
Edit `backend/.env` file:
```env
GEMINI_API_KEY=paste_your_key_here
```

Or create if doesn't exist:
```bash
cd backend
echo "GEMINI_API_KEY=your_key_here" >> .env
```

### Step 3: Test It (30 seconds)
```bash
cd backend
python chatbot/test_chatbot.py
```

## ✅ Verification

If setup is correct, you'll see:
```
✅ Chatbot service is healthy!
📚 Knowledge Base Stats: 25+ items
🧪 Running 12 comprehensive tests...
```

## 🔧 Troubleshooting

### Issue: "Chatbot is temporarily unavailable"
**Fix:** API key not set in `.env` file

### Issue: Import error for google.generativeai
**Fix:** Package is installed, just linting error. Ignore it or add to workspace settings.

### Issue: Server not running
**Fix:**
```bash
cd backend
python app.py
```

## 📖 Full Documentation

- **Quick Start**: `chatbot/README.md`
- **Complete Guide**: `chatbot/CHATBOT_GUIDE.md`
- **Implementation Details**: `chatbot/IMPLEMENTATION_SUMMARY.md`

## 🎯 Quick Test Commands

### Test Emergency Detection
```bash
curl -X POST http://127.0.0.1:5000/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I have chest pain"}'
```

### Test Appointment Info
```bash
curl -X POST http://127.0.0.1:5000/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I book an appointment?"}'
```

### Check Service Health
```bash
curl http://127.0.0.1:5000/chatbot/health
```

## 📝 Note on Deprecation Warning

You may see a warning about `google.generativeai` being deprecated in favor of `google.genai`. Both packages are installed and working. The current implementation uses `google.generativeai` which is still functional. To migrate to the new API later, simply update imports in `routes.py`.

**Current (works fine):**
```python
import google.generativeai as genai
```

**Future (when ready to migrate):**
```python
from google import genai
```

## ✨ You're Ready!

The chatbot is now fully functional with:
- ✅ Emergency detection
- ✅ Safety checks
- ✅ RAG system
- ✅ AI responses
- ✅ Comprehensive testing

**Start testing:** `python chatbot/test_chatbot.py`
