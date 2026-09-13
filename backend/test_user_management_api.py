#!/usr/bin/env python3
"""
Simple test script to verify user management API endpoints work correctly.
This is a basic verification that the API is running and routes are accessible.
"""

import requests
import time

def test_api_endpoints():
    base_url = "http://127.0.0.1:8000"
    
    print("Testing API endpoints...")
    
    # Test health check
    try:
        response = requests.get(f"{base_url}/api/health")
        print(f"✓ Health check: {response.json()}")
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        
    # Test root endpoint
    try:
        response = requests.get(base_url)
        print(f"✓ Root endpoint: {response.json()}")
    except Exception as e:
        print(f"✗ Root endpoint failed: {e}")

    # List all routes available (this would be in the OpenAPI docs)
    try:
        response = requests.get(f"{base_url}/openapi.json")
        if response.status_code == 200:
            data = response.json()
            paths = list(data.get('paths', {}).keys())
            user_routes = [p for p in paths if '/users/' in p]
            print(f"✓ Found {len(user_routes)} user management routes:")
            for route in user_routes[:5]:  # Show first 5
                print(f"  - {route}")
        else:
            print("✗ Could not retrieve OpenAPI documentation")
    except Exception as e:
        print(f"✗ OpenAPI test failed: {e}")

if __name__ == "__main__":
    test_api_endpoints()
