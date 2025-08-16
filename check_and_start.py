#!/usr/bin/env python3
"""
Check dependencies and start server with proper error handling
"""

import sys
import subprocess
import importlib
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'tensorflow',
        'pillow',
        'numpy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Install missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_files():
    """Check if required files exist"""
    required_files = [
        'main.py',
        'disease_medicines.json',
        'static/crud.html'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} is missing")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n📁 Missing files: {missing_files}")
        return False
    
    return True

def validate_json():
    """Validate JSON file structure"""
    try:
        with open('disease_medicines.json', 'r') as f:
            data = json.load(f)
        print(f"✅ JSON file is valid with {len(data)} disease categories")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ JSON file is invalid: {e}")
        return False
    except FileNotFoundError:
        print("❌ disease_medicines.json not found")
        return False

def start_server():
    """Start the FastAPI server"""
    print("\n🚀 Starting FastAPI server...")
    print("📡 Server will be available at: http://localhost:8000")
    print("🌐 Web interface at: http://localhost:8000/static/crud.html")
    print("📚 API docs at: http://localhost:8000/docs")
    print("\n⏳ Loading... (this may take a moment for the ML model)")
    print("Press Ctrl+C to stop the server\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except FileNotFoundError:
        print("❌ uvicorn not found. Install with: pip install uvicorn")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def main():
    print("🔧 FastAPI Server Startup Checker")
    print("=" * 50)
    
    # Run all checks
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Required Files", check_files),
        ("JSON Validation", validate_json)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n🔍 Checking {check_name}...")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 All checks passed!")
        
        # Ask user if they want to start the server
        try:
            start = input("\n🚀 Start the server now? (y/n): ").lower().strip()
            if start in ['y', 'yes']:
                start_server()
            else:
                print("👍 You can start the server later with: uvicorn main:app --reload")
        except KeyboardInterrupt:
            print("\n👋 Cancelled")
    else:
        print("❌ Some checks failed. Please fix the issues above before starting the server.")
        print("\n💡 Common solutions:")
        print("   • Install dependencies: pip install -r requirements.txt")
        print("   • Make sure all files are in the correct location")
        print("   • Check that your JSON file is valid")

if __name__ == "__main__":
    main()
