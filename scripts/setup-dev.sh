#!/bin/bash

# setup-dev.sh - TrendOps Development Environment Setup Script
# This script automates the setup of the development environment for TrendOps

set -e  # Exit on error

echo "🚀 Setting up TrendOps development environment..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.13 or higher."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Install pre-commit
echo "📦 Installing pre-commit..."
if command -v pip &> /dev/null; then
    pip install pre-commit
elif command -v pip3 &> /dev/null; then
    pip3 install pre-commit
else
    echo "❌ pip not found. Please install pip first."
    exit 1
fi

echo "✅ Pre-commit installed"
echo ""

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
pre-commit install

echo "✅ Pre-commit hooks installed"
echo ""

# Check if VS Code is installed
if command -v code &> /dev/null; then
    echo "💡 VS Code detected. You can install extensions using:"
    echo "   code --install-extension ms-python.python"
    echo "   code --install-extension ms-python.black-formatter"
    echo ""
else
    echo "📦 Please install the following VS Code extensions manually:"
    echo "   - Python (ms-python.python)"
    echo "   - Black Formatter (ms-python.black-formatter)"
    echo ""
fi

# Run initial formatting
echo "🔧 Running initial code formatting..."
pre-commit run --all-files || true

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "🎯 Next steps:"
echo "   1. Open project in VS Code"
echo "   2. Install recommended extensions (Python, Black Formatter)"
echo "   3. Start coding! (Files auto-format on save with Ctrl+S)"
echo ""
echo "📚 Useful commands:"
echo "   make format        # Format all Python files"
echo "   make safe-commit   # Run checks and commit safely"
echo "   make validate      # Run full CI validation locally"
echo "   make lint          # Run linting (informational only)"
echo ""
echo "Happy coding! 🚀"
