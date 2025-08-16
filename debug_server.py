#!/usr/bin/env python3
"""
Debug script to test the server and API endpoints
"""

import requests
import json
import subprocess
import sys
import time
import threading

def test_server_connection():
    """Test if server is responding"""
    print("🔍 Testing server connection...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and responding")
            return True
        else:
            print(f"❌ Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server - is it running?")
        return False
    except requests.exceptions.Timeout:
        print("❌ Server connection timed out")
        return False
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return False

def test_medicines_endpoint():
    """Test the medicines endpoint specifically"""
    print("\n🔍 Testing /medicines endpoint...")
    
    try:
        response = requests.get("http://localhost:8000/medicines", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ /medicines endpoint working")
            print(f"📊 Found diseases: {data.get('available_diseases', [])}")
            return True
        else:
            print(f"❌ /medicines endpoint returned: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing /medicines endpoint: {e}")
        return False

def check_cors():
    """Check CORS headers"""
    print("\n🔍 Testing CORS headers...")
    
    try:
        response = requests.options("http://localhost:8000/medicines")
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        
        print("CORS Headers:")
        for header, value in cors_headers.items():
            print(f"  {header}: {value}")
        
        if cors_headers['Access-Control-Allow-Origin'] == '*':
            print("✅ CORS is properly configured")
            return True
        else:
            print("❌ CORS might be misconfigured")
            return False
    except Exception as e:
        print(f"❌ Error checking CORS: {e}")
        return False

def main():
    print("🧪 FastAPI Server Debug Tool")
    print("=" * 40)
    
    # Test server connection
    if not test_server_connection():
        print("\n💡 Server is not running. To start it:")
        print("   1. Open a terminal in your project directory")
        print("   2. Run: uvicorn main:app --reload")
        print("   3. Wait for 'Uvicorn running on http://127.0.0.1:8000'")
        print("   4. Then run this debug script again")
        return
    
    # Test medicines endpoint
    if not test_medicines_endpoint():
        print("\n❌ The /medicines endpoint is not working properly")
        return
    
    # Test CORS
    check_cors()
    
    print("\n🎉 All tests passed! Your server should work with the web interface.")
    print("\n🌐 Try opening: http://localhost:8000/static/crud.html")

if __name__ == "__main__":
    main()
