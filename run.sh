#!/bin/bash

# Simple script to run the Foundation Potentials Comparison Dashboard

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import dash" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Check for API key
if [ -z "$MP_API_KEY" ]; then
    echo ""
    echo "WARNING: MP_API_KEY environment variable not set!"
    echo "Please set it by running: export MP_API_KEY='your_api_key_here'"
    echo "Or you can enter it in the app interface."
    echo ""
fi

# Run the app
echo "Starting the Foundation Potentials Comparison Dashboard..."
echo "Access the app at: http://127.0.0.1:8050"
echo ""
python app.py
