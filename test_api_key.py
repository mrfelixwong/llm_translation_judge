#!/usr/bin/env python3
"""
Test script to verify OpenAI API key is working.
"""

import os
from openai import OpenAI

def test_api_key():
    """Test if OpenAI API key is properly configured."""
    
    # Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("\nTo set it:")
        print('export OPENAI_API_KEY="sk-your-key-here"')
        return False
    
    if not api_key.startswith("sk-"):
        print("❌ API key doesn't look valid (should start with 'sk-')")
        return False
    
    print(f"✅ API key found: {api_key[:7]}...{api_key[-4:]}")
    
    # Test API call
    try:
        client = OpenAI()
        print("🔄 Testing API connection...")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Cheaper model for testing
            messages=[{"role": "user", "content": "Say 'API test successful'"}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ API test successful: {result}")
        print(f"💰 Tokens used: {response.usage.total_tokens}")
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔑 Testing OpenAI API Setup")
    print("=" * 40)
    
    if test_api_key():
        print("\n🎉 Your API key is working correctly!")
        print("You can now run the LLM judge experiments.")
    else:
        print("\n💡 Setup instructions:")
        print("1. Get API key from: https://platform.openai.com/api-keys")
        print('2. Set environment variable: export OPENAI_API_KEY="sk-..."')
        print("3. Run this test again")