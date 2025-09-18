#!/usr/bin/env python
"""
Simple startup script to run the F-Ops backend server with proper Python path
"""
import sys
import os
import uvicorn

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Change to backend directory for relative imports
backend_dir = os.path.join(project_root, 'backend')
os.chdir(backend_dir)

if __name__ == "__main__":
    # Import the app after setting up the path
    from backend.app.main import app
    
    # Run the server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8002,
        reload=True,
        reload_dirs=[backend_dir]
    )