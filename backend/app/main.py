from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(
    title="F-Ops — Local-First DevOps Assistant",
    version="0.1.0",
    description="Proposal-only CI/CD, IaC, and monitoring generation"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Local-first
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "F-Ops",
        "version": "0.1.0",
        "status": "operational",
        "description": "Local-first DevOps assistant with proposal-only operations",
        "endpoints": {
            "health": "/health",
            "pipeline": "/api/pipeline",
            "kb": "/api/kb"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "api": "operational",
            "chroma": "ready",
            "audit": "enabled"
        }
    }

# Include API routes
from app.api.routes import pipeline, kb

app.include_router(pipeline.router, prefix="/api/pipeline", tags=["pipeline-agent"])
app.include_router(kb.router, prefix="/api/kb", tags=["knowledge-base"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)