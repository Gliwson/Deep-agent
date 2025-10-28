#!/usr/bin/env python3
"""
Test runner script for Deep Agent
"""
import subprocess
import sys
import os

def run_tests():
    """Run all tests"""
    print("Running Deep Agent tests...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("Warning: .env file not found. Please create one from .env.example")
        print("For testing purposes, you can run without OpenAI API key")
    
    # Run pytest
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_agent.py", 
            "-v", 
            "--tb=short"
        ], check=True)
        print("\n✅ All tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return False

def run_websocket_test():
    """Run WebSocket integration test"""
    print("\nRunning WebSocket integration test...")
    print("Make sure the server is running on localhost:8000")
    
    try:
        result = subprocess.run([
            sys.executable, "test_websocket_client.py"
        ], check=True)
        print("✅ WebSocket test completed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ WebSocket test failed with exit code {e.returncode}")
        return False

if __name__ == "__main__":
    print("Deep Agent Test Suite")
    print("=" * 50)
    
    # Run unit tests
    unit_tests_passed = run_tests()
    
    if unit_tests_passed:
        print("\n" + "=" * 50)
        print("Unit tests passed! You can now run the server and test WebSocket functionality.")
        print("\nTo start the server:")
        print("  python main.py")
        print("\nTo test WebSocket (in another terminal):")
        print("  python test_websocket_client.py")
        print("\nFor interactive testing:")
        print("  python test_websocket_client.py interactive")
    else:
        print("\n❌ Some tests failed. Please fix the issues before proceeding.")
        sys.exit(1)