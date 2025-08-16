#!/usr/bin/env python3
"""
Startup script for the Paddy Disease API with CRUD interface
"""

import subprocess
import sys
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import pydantic
        print("✅ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False

def check_files():
    """Check if required files exist"""
    required_files = [
        "main.py",
        "disease_medicines.json",
        "static/crud.html"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    print("✅ All required files are present")
    return True

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting FastAPI server...")
    print("📡 API will be available at: http://localhost:8000")
    print("🌐 Web interface will be available at: http://localhost:8000/static/crud.html")
    print("📚 API documentation at: http://localhost:8000/docs")
    print("\n⏳ Starting server (this may take a moment to load the ML model)...")
    
    try:
        # Start the server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def main():
    print("🌾 Paddy Disease API with CRUD Interface")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check files
    if not check_files():
        return
    
    # Ask user if they want to open browser
    try:
        open_browser = input("\n🌐 Open web interface in browser after startup? (y/n): ").lower().strip()
        if open_browser in ['y', 'yes']:
            # Start server in background and open browser
            import threading
            server_thread = threading.Thread(target=start_server)
            server_thread.daemon = True
            server_thread.start()
            
            print("⏳ Waiting for server to start...")
            time.sleep(3)  # Give server time to start
            
            print("🌐 Opening web interface...")
            webbrowser.open("http://localhost:8000/static/crud.html")
            
            # Keep main thread alive
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Shutting down...")
        else:
            start_server()
    except KeyboardInterrupt:
        print("\n👋 Startup cancelled by user")

if __name__ == "__main__":
    main()
