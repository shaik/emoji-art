#!/bin/bash

# Find the process running on port 5000 (default Flask port)
PID=$(lsof -ti:5000)

if [ ! -z "$PID" ]; then
    echo "Stopping Flask application (PID: $PID)"
    kill $PID
else
    echo "No Flask application found running on port 5000"
fi
