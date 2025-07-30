#!/usr/bin/env python3
"""
Test script for the Genomics Platform API
"""

import requests
import json

def test_api_endpoints():
    base_url = "http://localhost:8000/api/v1"
    
    print("🧪 Testing API Endpoints...")
    print("=" * 50)
    
    # Test variants endpoint
    try:
        response = requests.get(f"{base_url}/variants?limit=5")
        print(f"✅ Variants API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total: {data.get('total', 'N/A')}")
            print(f"   Items: {len(data.get('items', []))}")
            if data.get('items'):
                print(f"   Sample variant: {data['items'][0].get('gene', 'N/A')} - {data['items'][0].get('chromosome', 'N/A')}:{data['items'][0].get('position', 'N/A')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Variants API Error: {e}")
    
    print()
    
    # Test drugs endpoint
    try:
        response = requests.get(f"{base_url}/drugs?limit=5")
        print(f"✅ Drugs API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total: {data.get('total', 'N/A')}")
            print(f"   Items: {len(data.get('items', []))}")
            if data.get('items'):
                print(f"   Sample drug: {data['items'][0].get('drug_name', 'N/A')} -> {data['items'][0].get('target_protein', 'N/A')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Drugs API Error: {e}")
    
    print()
    
    # Test gene expression endpoint
    try:
        response = requests.get(f"{base_url}/gene-expression?limit=5")
        print(f"✅ Gene Expression API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total: {data.get('total', 'N/A')}")
            print(f"   Items: {len(data.get('items', []))}")
            if data.get('items'):
                print(f"   Sample gene: {data['items'][0].get('gene_symbol', 'N/A')} - Expression: {data['items'][0].get('expression_level', 'N/A')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Gene Expression API Error: {e}")
    
    print()
    
    # Test ML model status
    try:
        response = requests.get(f"{base_url}/models/status")
        print(f"✅ ML Models Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Models loaded: {data.get('models_loaded', 'N/A')}")
            print(f"   Total models: {data.get('total_models', 'N/A')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ ML Models Status Error: {e}")

if __name__ == "__main__":
    test_api_endpoints() 