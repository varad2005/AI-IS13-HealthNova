#!/usr/bin/env python
"""Quick test for Gemini integration"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from utils.gemini_helper import get_ai_response
    print("✓ Successfully imported gemini_helper")
    
    print("\n🤖 Testing Gemini API with a simple health question...")
    result = get_ai_response("What are common fever symptoms?")
    
    print(f"\n📊 Response Status: {'Success' if result['success'] else 'Failed'}")
    print(f"\n💬 AI Response:\n{result['message']}")
    
    if 'error' in result:
        print(f"\n⚠️ Error: {result['error']}")
    
    print("\n✓ Test completed!")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
