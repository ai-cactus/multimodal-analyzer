#!/bin/bash
# Setup Python 3.14 Virtual Environment

echo "🐍 Setting up Python 3.14 virtual environment..."

# Check if Python 3.14 is available
if ! command -v python3.14 &> /dev/null; then
    echo "❌ Python 3.14 not found. Please install it first."
    echo "Available Python versions:"
    ls -1 /usr/bin/python3.* 2>/dev/null || echo "No Python 3.x found"
    exit 1
fi

# Create venv with Python 3.14
echo "📦 Creating virtual environment..."
python3.14 -m venv venv

# Activate venv
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install all requirements
echo "📚 Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "Then start the server:"
echo "  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
