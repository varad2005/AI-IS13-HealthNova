#!/usr/bin/env python
"""List available Gemini models"""
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

try:
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    print("🔍 Listing available Gemini models...\n")
    
    models = client.models.list()
    
    for model in models:
        print(f"✓ {model.name}")
        if hasattr(model, 'supported_generation_methods'):
            print(f"  Supported methods: {model.supported_generation_methods}")
        print()
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
