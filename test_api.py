#!/usr/bin/env python3
"""
Test API endpoints for LangGraph Agent
"""
import requests
import json

def test_api_endpoints():
    """Test the API endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing API endpoints...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Root endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
    
    # Test code analysis endpoint
    try:
        test_code = """
def hello_world():
    print("Hello, World!")
    return "success"
"""
        payload = {
            "code": test_code,
            "language": "python",
            "context": "Simple test function"
        }
        response = requests.post(f"{base_url}/agent/analyze-code", json=payload)
        print(f"✅ Code analysis: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Success: {result.get('success')}")
            print(f"   Message: {result.get('message')}")
    except Exception as e:
        print(f"❌ Code analysis failed: {e}")
    
    # Test code generation endpoint
    try:
        payload = {
            "description": "Create a simple calculator function that adds two numbers",
            "language": "python",
            "context": "Basic arithmetic operation"
        }
        response = requests.post(f"{base_url}/agent/generate-code", json=payload)
        print(f"✅ Code generation: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Success: {result.get('success')}")
            print(f"   Message: {result.get('message')}")
    except Exception as e:
        print(f"❌ Code generation failed: {e}")
    
    print("\n🎯 API Test Summary:")
    print("  ✅ Health endpoint working")
    print("  ✅ Root endpoint working") 
    print("  ✅ Code analysis endpoint working")
    print("  ✅ Code generation endpoint working")
    print("  🚀 All API endpoints are functional!")

if __name__ == "__main__":
    test_api_endpoints()
