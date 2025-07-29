#!/usr/bin/env python3
"""
Test script for the Genomics Platform API
"""

import requests
import json
import time

def test_api():
    """Test the API endpoints."""
    base_url = "http://127.0.0.1:8000"
    
    print("🧬 Testing Genomics Platform API")
    print("=" * 50)
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Root endpoint: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
    
    print()
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/health")
        print(f"✅ Health endpoint: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
    
    print()
    
    # Test datasets endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/datasets")
        print(f"✅ Datasets endpoint: {response.status_code}")
        data = response.json()
        print(f"   Found {len(data.get('datasets', []))} datasets")
        print(f"   Total: {data.get('pagination', {}).get('total', 0)}")
    except Exception as e:
        print(f"❌ Datasets endpoint failed: {e}")
    
    print()
    
    # Test variants endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/variants?limit=5")
        print(f"✅ Variants endpoint: {response.status_code}")
        data = response.json()
        print(f"   Found {len(data.get('variants', []))} variants")
        print(f"   Total: {data.get('pagination', {}).get('total', 0)}")
    except Exception as e:
        print(f"❌ Variants endpoint failed: {e}")
    
    print()
    
    # Test API info endpoint
    try:
        response = requests.get(f"{base_url}/api/v1")
        print(f"✅ API info endpoint: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"❌ API info endpoint failed: {e}")

if __name__ == "__main__":
    test_api() 