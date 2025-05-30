#!/bin/bash

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Set default values if not provided
export FLASK_DEBUG=${FLASK_DEBUG:-False}
export PORT=${PORT:-5000}

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "Error: GEMINI_API_KEY environment variable is not set."
    echo "Please create a .env file based on .env.example and set your API key."
    exit 1
fi

# Run the Flask application
python3 app.py 