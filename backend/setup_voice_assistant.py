"""
Voice Assistant Setup Script

Installs OpenAI package and verifies configuration.
Run this before using the voice assistant.
"""

import subprocess
import sys
import os

def install_openai():
    """Install openai package"""
    print("=" * 60)
    print("VOICE ASSISTANT SETUP")
    print("=" * 60)
    print()
    print("Step 1: Installing OpenAI package...")
    print()
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openai>=1.0.0"])
        print()
        print("✓ OpenAI package installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install OpenAI package: {e}")
        return False

def check_api_key():
    """Check if OpenAI API key is configured"""
    print()
    print("Step 2: Checking OpenAI API key...")
    print()
    
    api_key = os.environ.get('OPENAI_API_KEY', '')
    
    if api_key and api_key.startswith('sk-'):
        print(f"✓ API key found: {api_key[:10]}...")
        return True
    else:
        print("✗ OpenAI API key not configured!")
        print()
        print("TO FIX:")
        print("1. Get API key from: https://platform.openai.com/api-keys")
        print("2. Set environment variable:")
        print()
        print("   Windows PowerShell:")
        print('   $env:OPENAI_API_KEY="sk-your-key-here"')
        print()
        print("   Or create .env file:")
        print('   OPENAI_API_KEY=sk-your-key-here')
        print()
        return False

def verify_import():
    """Verify openai can be imported"""
    print()
    print("Step 3: Verifying installation...")
    print()
    
    try:
        import openai
        print(f"✓ OpenAI package imported successfully!")
        print(f"  Version: {openai.__version__}")
        return True
    except ImportError as e:
        print(f"✗ Failed to import openai: {e}")
        return False

def main():
    """Run setup"""
    success = True
    
    # Install package
    if not install_openai():
        success = False
    
    # Verify import
    if not verify_import():
        success = False
    
    # Check API key
    if not check_api_key():
        success = False
    
    print()
    print("=" * 60)
    
    if success:
        print("✓ SETUP COMPLETE!")
        print()
        print("NEXT STEPS:")
        print("1. Start Flask server: python app.py")
        print("2. Open browser: http://127.0.0.1:5000/voice-assistant.html")
        print("3. Click microphone and speak!")
    else:
        print("⚠ SETUP INCOMPLETE")
        print()
        print("Please fix the issues above and run this script again.")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
