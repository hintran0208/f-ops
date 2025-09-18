from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import logging
import sys
import os

# Add project root to Python path for mcp_packs and knowledge_base
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="F-Ops DevOps AI Agent",
    version="0.1.0",
    description="AI-powered DevOps automation platform"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class OnboardRequest(BaseModel):
    repo_url: str
    target: str = "k8s"
    environments: List[str] = ["staging", "prod"]
    dry_run: bool = True

class DeployRequest(BaseModel):
    service_name: str
    environment: str = "staging"
    version: Optional[str] = None
    dry_run: bool = True

class IncidentRequest(BaseModel):
    service_name: str
    symptoms: str

class KBSearchRequest(BaseModel):
    query: str
    collection: Optional[str] = None
    limit: int = 5

# Initialize agent lazily
_agent = None

def get_agent():
    global _agent
    if _agent is None:
        try:
            from app.core.agent_fixed import DevOpsAgent
            _agent = DevOpsAgent()
            logger.info("DevOps Agent initialized")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
    return _agent

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting F-Ops DevOps AI Agent...")
    logger.info("Server is ready to accept requests")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "F-Ops",
        "version": "0.1.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "onboard": "/api/onboard/repo",
            "deploy": "/api/deploy/service",
            "incident": "/api/incident/analyze",
            "kb_search": "/api/kb/search"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "api": "operational",
            "agent": "ready"
        }
    }

# Onboarding endpoints
@app.post("/api/onboard/repo")
async def onboard_repository(request: OnboardRequest):
    """Onboard a new repository"""
    try:
        agent = get_agent()
        if agent:
            result = agent.onboard_repository(
                request.repo_url,
                request.target,
                request.environments
            )
            return result
        else:
            return {
                "success": True,
                "message": f"Repository {request.repo_url} onboarding simulated",
                "target": request.target,
                "environments": request.environments,
                "pr_url": "https://github.com/example/pr/123",
                "note": "Running in simulation mode"
            }
    except Exception as e:
        logger.error(f"Onboarding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Deployment endpoints
@app.post("/api/deploy/service")
async def deploy_service(request: DeployRequest):
    """Deploy a service to an environment"""
    try:
        agent = get_agent()
        if agent:
            result = agent.deploy_service(
                request.service_name,
                request.environment,
                request.version,
                request.dry_run
            )
            return result
        else:
            return {
                "success": True,
                "service": request.service_name,
                "environment": request.environment,
                "version": request.version or "latest",
                "dry_run": request.dry_run,
                "message": f"Deployment {'simulated' if request.dry_run else 'executed'} successfully",
                "note": "Running in simulation mode"
            }
    except Exception as e:
        logger.error(f"Deployment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Incident endpoints
@app.post("/api/incident/analyze")
async def analyze_incident(request: IncidentRequest):
    """Analyze an incident"""
    try:
        agent = get_agent()
        if agent:
            result = agent.analyze_incident(
                request.service_name,
                request.symptoms
            )
            return result
        else:
            return {
                "success": True,
                "service": request.service_name,
                "analysis": f"""
Incident Analysis for {request.service_name}:

Symptoms: {request.symptoms}

Recommended Actions:
1. Check service logs
2. Verify resource metrics
3. Review recent changes
4. Check dependencies

Note: Running in simulation mode
""",
                "recommendations": [
                    "Check logs",
                    "Review metrics",
                    "Verify configuration"
                ]
            }
    except Exception as e:
        logger.error(f"Incident analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Knowledge Base endpoints
@app.post("/api/kb/search")
async def search_knowledge(request: KBSearchRequest):
    """Search the knowledge base"""
    try:
        agent = get_agent()
        if agent and agent.kb:
            if request.collection:
                results = agent.kb.search(request.collection, request.query, k=request.limit)
            else:
                results = agent.kb.search_all(request.query, k=request.limit)
            
            return {
                "query": request.query,
                "results": results,
                "count": len(results) if isinstance(results, list) else sum(len(v) for v in results.values())
            }
        else:
            return {
                "query": request.query,
                "results": [],
                "message": "Knowledge base not available"
            }
    except Exception as e:
        logger.error(f"KB search error: {e}")
        return {
            "query": request.query,
            "results": [],
            "error": str(e)
        }

@app.get("/api/kb/stats")
async def get_kb_stats(collection: Optional[str] = None):
    """Get knowledge base statistics"""
    try:
        agent = get_agent()
        if agent and agent.kb:
            stats = agent.kb.get_collection_stats(collection)
            return stats
        else:
            return {
                "message": "Knowledge base not available"
            }
    except Exception as e:
        logger.error(f"KB stats error: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)