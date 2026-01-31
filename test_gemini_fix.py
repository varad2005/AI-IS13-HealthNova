"""
Test Gemini API integration fix
"""
import sys
sys.path.insert(0, 'backend')

from utils.gemini_helper import verify_gemini_connection, get_ai_response

print("="*60)
print("Testing Gemini API Fix")
print("="*60)

# Test 1: Verify connection
print("\n1. Verifying Gemini connection...")
if verify_gemini_connection():
    print("   Connection successful!")
else:
    print("   Connection failed!")
    sys.exit(1)

# Test 2: Test simple query
print("\n2. Testing simple health query...")
test_query = "What is diabetes?"
response = get_ai_response(test_query)

if response['success']:
    print(f"   Query successful!")
    print(f"   Response preview: {response['message'][:100]}...")
else:
    print(f"   Query failed: {response.get('error', 'Unknown error')}")

print("\n" + "="*60)
print("Test completed!")
print("="*60)
