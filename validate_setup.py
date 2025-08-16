#!/usr/bin/env python3
"""
Validation script to check if the CRUD setup is working correctly
"""

import json
import os
from pathlib import Path

def validate_json_structure():
    """Validate the structure of disease_medicines.json"""
    print("🔍 Validating JSON structure...")
    
    try:
        with open("disease_medicines.json", "r") as f:
            data = json.load(f)
        
        print(f"✅ JSON file loaded successfully")
        print(f"📊 Found {len(data)} disease categories")
        
        # Check structure
        total_medicines = 0
        for disease, medicines in data.items():
            if not isinstance(medicines, list):
                print(f"❌ Disease '{disease}' should contain a list of medicines")
                return False
            
            total_medicines += len(medicines)
            
            # Check first medicine structure if exists
            if medicines:
                first_med = medicines[0]
                required_fields = ['name']
                for field in required_fields:
                    if field not in first_med:
                        print(f"❌ Medicine in '{disease}' missing required field: {field}")
                        return False
        
        print(f"📈 Total medicines across all diseases: {total_medicines}")
        print("✅ JSON structure is valid")
        return True
        
    except FileNotFoundError:
        print("❌ disease_medicines.json not found")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        return False

def validate_static_files():
    """Validate static files exist"""
    print("\n🔍 Validating static files...")
    
    static_dir = Path("static")
    if not static_dir.exists():
        print("❌ static/ directory not found")
        return False
    
    crud_html = static_dir / "crud.html"
    if not crud_html.exists():
        print("❌ static/crud.html not found")
        return False
    
    # Check if HTML file contains expected content
    try:
        with open(crud_html, "r") as f:
            content = f.read()
        
        expected_elements = [
            "Disease Medicines CRUD Manager",
            "diseaseSelect",
            "medicineForm",
            "API_BASE"
        ]
        
        for element in expected_elements:
            if element not in content:
                print(f"❌ HTML file missing expected element: {element}")
                return False
        
        print("✅ Static files are valid")
        return True
        
    except Exception as e:
        print(f"❌ Error reading HTML file: {e}")
        return False

def validate_main_py():
    """Validate main.py has CRUD endpoints"""
    print("\n🔍 Validating main.py...")
    
    try:
        with open("main.py", "r") as f:
            content = f.read()
        
        expected_imports = [
            "from pydantic import BaseModel",
            "import threading",
            "import tempfile"
        ]
        
        expected_functions = [
            "class Medicine(BaseModel)",
            "_read_medicines_json",
            "_write_medicines_json",
            "def list_all_diseases_crud",
            "def create_medicine",
            "def update_medicine",
            "def delete_medicine"
        ]
        
        for imp in expected_imports:
            if imp not in content:
                print(f"❌ Missing import: {imp}")
                return False
        
        for func in expected_functions:
            if func not in content:
                print(f"❌ Missing function/class: {func}")
                return False
        
        print("✅ main.py contains all required CRUD components")
        return True
        
    except FileNotFoundError:
        print("❌ main.py not found")
        return False
    except Exception as e:
        print(f"❌ Error reading main.py: {e}")
        return False

def validate_dependencies():
    """Check if dependencies can be imported"""
    print("\n🔍 Validating dependencies...")
    
    required_modules = [
        ("fastapi", "FastAPI"),
        ("pydantic", "BaseModel"),
        ("uvicorn", "uvicorn server"),
    ]
    
    missing_modules = []
    
    for module, description in required_modules:
        try:
            __import__(module)
            print(f"✅ {description} available")
        except ImportError:
            print(f"❌ {description} not available")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n📦 Install missing modules with:")
        print(f"pip install {' '.join(missing_modules)}")
        return False
    
    return True

def main():
    print("🧪 Validating CRUD Setup")
    print("=" * 40)
    
    all_valid = True
    
    # Run all validations
    validations = [
        validate_json_structure,
        validate_static_files,
        validate_main_py,
        validate_dependencies
    ]
    
    for validation in validations:
        if not validation():
            all_valid = False
    
    print("\n" + "=" * 40)
    if all_valid:
        print("🎉 All validations passed! Your CRUD setup is ready.")
        print("\n🚀 To start the server, run:")
        print("   python3 start_server.py")
        print("   OR")
        print("   uvicorn main:app --reload")
        print("\n🌐 Then visit: http://localhost:8000/static/crud.html")
    else:
        print("❌ Some validations failed. Please fix the issues above.")
    
    return all_valid

if __name__ == "__main__":
    main()
