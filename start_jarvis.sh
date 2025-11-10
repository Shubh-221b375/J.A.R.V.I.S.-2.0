#!/bin/bash
# Auto-start script for JARVIS AI Assistant (Linux/macOS)
# Add to ~/.bashrc or ~/.zshrc or use systemd service

cd "$(dirname "$0")"

# Check if running from packaged executable
if [ -f "JARVIS" ]; then
    ./JARVIS &
    exit
fi

# Check if running from source
if [ -f "Main.py" ]; then
    # Check for virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
        python Main.py &
    else
        echo "ERROR: Virtual environment not found!"
        echo "Please run: python3 -m venv venv"
        echo "Then install dependencies: pip install -r Requirements.txt"
        exit 1
    fi
else
    echo "ERROR: Main.py not found!"
    echo "Please run this script from the JARVIS project directory."
    exit 1
fi

