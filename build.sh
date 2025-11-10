#!/bin/bash
# Build script for JARVIS AI Assistant (Linux/macOS)
# This script packages JARVIS into a standalone executable

echo "========================================"
echo "JARVIS AI Assistant - Build Script"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade build dependencies
echo "Installing build dependencies..."
pip install --upgrade pip
pip install pyinstaller

# Install project dependencies
echo "Installing project dependencies..."
pip install -r Requirements.txt

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Check for spec file
if [ ! -f "jarvis.spec" ]; then
    echo "ERROR: jarvis.spec not found!"
    exit 1
fi

# Build the executable
echo ""
echo "========================================"
echo "Building JARVIS executable..."
echo "========================================"
echo ""

pyinstaller jarvis.spec

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "Build completed successfully!"
    echo "========================================"
    echo ""
    echo "Executable location: dist/JARVIS"
    echo ""
    echo "To test the build:"
    echo "  1. Navigate to dist folder"
    echo "  2. Copy your .env file to dist folder"
    echo "  3. Run ./JARVIS"
    echo ""
else
    echo ""
    echo "========================================"
    echo "Build failed! Check errors above."
    echo "========================================"
    echo ""
    exit 1
fi

