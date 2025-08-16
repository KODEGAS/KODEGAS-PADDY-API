#!/bin/bash

echo "🌾 Starting Paddy Disease CRUD Server"
echo "======================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! python -c "import fastapi, uvicorn, pydantic" 2>/dev/null; then
    echo "📥 Installing dependencies..."
    pip install -r requirements_simple.txt
fi

echo "✅ Dependencies ready"

# Start the server
echo "🚀 Starting server on port 8001..."
echo "🌐 Web interface: http://localhost:8001/static/crud.html"
echo "📚 API docs: http://localhost:8001/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn main_crud_only:app --reload --port 8001 --host 0.0.0.0
