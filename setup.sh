#!/bin/bash

echo "🚀 F-Ops Setup Script"
echo "===================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install backend dependencies
echo ""
echo "Installing backend dependencies..."
cd backend

# Install core dependencies first
pip install fastapi==0.104.0
pip install uvicorn==0.24.0
pip install pydantic==1.10.13
pip install python-multipart==0.0.6
pip install sqlalchemy==2.0.23
pip install python-dotenv==1.0.0
pip install aiofiles==23.2.1

echo ""
echo "Installing additional dependencies (may have some failures - that's OK)..."
# Try to install other dependencies - some may fail but that's OK
pip install chromadb==0.4.15 || echo "ChromaDB installation failed - continuing..."
pip install langchain==0.0.350 || echo "LangChain installation failed - continuing..."
pip install openai==1.3.0 || echo "OpenAI installation failed - continuing..."
pip install PyGithub==2.1.1 || echo "PyGithub installation failed - continuing..."
pip install kubernetes==28.1.0 || echo "Kubernetes client installation failed - continuing..."

cd ..

# Install CLI
echo ""
echo "Installing CLI..."
cd cli
pip install -e . || echo "CLI installation had issues - continuing..."
cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the server:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Go to backend: cd backend"
echo "  3. Run server: uvicorn app.main_simple:app --reload"
echo ""
echo "Or for the full server (if all dependencies installed):"
echo "  uvicorn app.main:app --reload"
echo ""
echo "The API will be available at: http://localhost:8000"
echo "API documentation at: http://localhost:8000/docs"