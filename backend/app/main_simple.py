"""
Simplified version of main.py for testing basic functionality
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="F-Ops DevOps AI Agent (Simplified)",
    version="0.1.0",
    description="AI-powered DevOps automation platform - Simplified version"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Starting F-Ops DevOps AI Agent (Simplified)...")
    logger.info("Server is ready!")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "F-Ops",
        "version": "0.1.0",
        "status": "operational",
        "mode": "simplified"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/api/test")
async def test_endpoint():
    """Test endpoint"""
    return {
        "message": "API is working!",
        "endpoints": [
            "/",
            "/health",
            "/api/test",
            "/docs"
        ]
    }