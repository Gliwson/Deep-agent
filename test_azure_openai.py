#!/usr/bin/env python3
"""
Test script for Azure OpenAI integration
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI

# Load environment variables
load_dotenv()

async def test_azure_openai():
    """Test Azure OpenAI connection and basic functionality"""
    
    # Check if required environment variables are set
    required_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT", 
        "AZURE_OPENAI_DEPLOYMENT_NAME"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file and ensure all Azure OpenAI variables are set.")
        return False
    
    try:
        # Initialize Azure OpenAI client
        client = AsyncAzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        print("🔗 Testing Azure OpenAI connection...")
        
        # Test basic chat completion
        response = await client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello from Azure OpenAI!' and nothing else."}
            ],
            max_tokens=50,
            temperature=0.1
        )
        
        message = response.choices[0].message.content.strip()
        print(f"✅ Azure OpenAI response: {message}")
        
        if "Hello from Azure OpenAI" in message:
            print("🎉 Azure OpenAI integration test successful!")
            return True
        else:
            print("⚠️  Unexpected response from Azure OpenAI")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Azure OpenAI: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Check your Azure OpenAI endpoint URL")
        print("2. Verify your API key is correct")
        print("3. Ensure your deployment name exists")
        print("4. Check if your deployment is ready and active")
        return False

async def main():
    """Main test function"""
    print("🚀 Testing Azure OpenAI Integration")
    print("=" * 40)
    
    success = await test_azure_openai()
    
    if success:
        print("\n✅ All tests passed! Your Azure OpenAI integration is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Tests failed. Please check your configuration.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())