#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start the Flask application
export FLASK_APP=app.py
export FLASK_ENV=development
python3 app.py
