#!/bin/bash

# Kalshi Mention Market Research Tool Installation Script

echo "🎯 Installing Kalshi Mention Market Research Tool..."

# Check if Python 3.8+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8 or higher is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create cache directory
echo "📁 Creating cache directory..."
mkdir -p cache

# Copy environment template
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your API keys before running the application"
fi

# Initialize database
echo "🗄️  Initializing database..."
python -c "from src.database import init_database; init_database(); print('Database initialized successfully')"

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run: python main.py"
echo "3. Type 'help' for available commands"
echo ""
echo "For more information, see README.md"



