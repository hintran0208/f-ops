#!/bin/bash

# F-Ops Backend Server Startup Script
# This script sets up the proper Python path and runs the backend server

echo "🚀 Starting F-Ops Backend Server..."

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set PYTHONPATH to include the project root
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

# Change to backend directory
cd "${SCRIPT_DIR}/backend"

# Run the server
echo "Running server on http://127.0.0.1:8002"
echo "API docs available at http://127.0.0.1:8002/docs"
echo ""

# Try to run the main server, fall back to simple if it fails
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload || \
    (echo "Main server failed, trying simplified version..." && \
     python -m uvicorn app.main_simple:app --host 127.0.0.1 --port 8002 --reload)