#!/usr/bin/env python3
"""
F-Ops Backend Runner

This script sets up the proper Python path and starts the FastAPI backend.
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
    # Run the server using module import
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8002,
        reload=True,
        reload_dirs=[project_root]  # Watch project root for mcp_packs changes
    )