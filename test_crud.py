#!/usr/bin/env python3
"""
Simple test script to verify CRUD endpoints work correctly
Run this after starting the FastAPI server with: uvicorn main:app --reload
"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_crud_endpoints():
    print("🧪 Testing CRUD endpoints...")
    
    # Test 1: List all diseases
    print("\n1. Testing GET /medicines (list diseases)")
    try:
        response = requests.get(f"{API_BASE}/medicines")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: Found {len(data['available_diseases'])} diseases")
            print(f"   Diseases: {data['available_diseases'][:3]}...")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get medicines for a specific disease
    print("\n2. Testing GET /medicines/{disease}")
    try:
        response = requests.get(f"{API_BASE}/medicines/blast")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: Found {len(data['medicines'])} medicines for blast")
            if data['medicines']:
                print(f"   First medicine: {data['medicines'][0]['name']}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Create a new medicine
    print("\n3. Testing POST /medicines/{disease} (create)")
    test_medicine = {
        "name": "Test Medicine CRUD",
        "brand": "Test Brand",
        "type": "Test Fungicide",
        "active_ingredient": "Test Ingredient",
        "pack_size": "100ml",
        "price": "Rs. 500",
        "priority": 1,
        "note": "This is a test medicine created by CRUD test"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/medicines/blast",
            json=test_medicine,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 201:
            print("✅ Success: Medicine created")
            created_data = response.json()
            print(f"   Created: {created_data['created']['name']}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Get the created medicine
    print("\n4. Testing GET /medicines/{disease} (verify creation)")
    try:
        response = requests.get(f"{API_BASE}/medicines/blast")
        if response.status_code == 200:
            data = response.json()
            test_medicine_found = any(m['name'] == 'Test Medicine CRUD' for m in data['medicines'])
            if test_medicine_found:
                print("✅ Success: Test medicine found in list")
                # Find the index of our test medicine
                test_index = next(i for i, m in enumerate(data['medicines']) if m['name'] == 'Test Medicine CRUD')
                print(f"   Test medicine is at index: {test_index}")
                
                # Test 5: Update the medicine
                print(f"\n5. Testing PUT /medicines/blast/{test_index} (update)")
                updated_medicine = test_medicine.copy()
                updated_medicine['price'] = 'Rs. 600'
                updated_medicine['note'] = 'Updated by CRUD test'
                
                response = requests.put(
                    f"{API_BASE}/medicines/blast/{test_index}",
                    json=updated_medicine,
                    headers={"Content-Type": "application/json"}
                )
                if response.status_code == 200:
                    print("✅ Success: Medicine updated")
                else:
                    print(f"❌ Failed: {response.status_code} - {response.text}")
                
                # Test 6: Delete the medicine
                print(f"\n6. Testing DELETE /medicines/blast/{test_index} (delete)")
                response = requests.delete(f"{API_BASE}/medicines/blast/{test_index}")
                if response.status_code == 200:
                    print("✅ Success: Medicine deleted")
                    deleted_data = response.json()
                    print(f"   Deleted: {deleted_data['deleted']['name']}")
                else:
                    print(f"❌ Failed: {response.status_code} - {response.text}")
            else:
                print("❌ Test medicine not found in list")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🎉 CRUD testing completed!")
    print("\n📝 To use the web interface:")
    print("   1. Start the server: uvicorn main:app --reload")
    print("   2. Open: http://localhost:8000/static/crud.html")

if __name__ == "__main__":
    test_crud_endpoints()
