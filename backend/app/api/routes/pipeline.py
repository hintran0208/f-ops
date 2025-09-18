from fastapi import APIRouter, HTTPException
from app.agents.pipeline_agent import PipelineAgent
from app.core.kb_manager import KnowledgeBaseManager
from app.core.audit_logger import AuditLogger
from app.core.pr_orchestrator import PROrchestrator
from app.schemas.pipeline import PipelineRequest, PipelineResponse
from app.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize components
kb_manager = KnowledgeBaseManager()
audit_logger = AuditLogger()
pr_orchestrator = PROrchestrator(audit_logger)
pipeline_agent = PipelineAgent(kb_manager, audit_logger)

@router.post("/generate", response_model=PipelineResponse)
async def generate_pipeline(request: PipelineRequest):
    """Generate CI/CD pipeline and create PR"""
    try:
        logger.info(f"Pipeline generation requested for: {request.repo_url}")

        # Analyze repository
        stack = pipeline_agent.analyze_repository(request.repo_url)

        # Generate pipeline
        result = pipeline_agent.generate_pipeline(
            repo_url=request.repo_url,
            stack=stack,
            target=request.target,
            environments=request.environments
        )

        # Create PR with pipeline
        pr_url = pr_orchestrator.create_pipeline_pr(
            repo_url=request.repo_url,
            pipeline_content=result["pipeline"],
            pipeline_file=result["pipeline_file"],
            citations=result["citations"],
            validation_results=result["validation"]
        )

        # Log successful operation
        audit_logger.log_operation({
            "type": "pipeline_generation_complete",
            "agent": "pipeline",
            "inputs": request.dict(),
            "outputs": {"pr_url": pr_url},
            "citations": result["citations"],
            "validation": result["validation"]
        })

        return PipelineResponse(
            pr_url=pr_url,
            citations=result["citations"],
            validation_status=result["validation"]["status"],
            pipeline_file=result["pipeline_file"],
            stack=result["stack"],
            success=True
        )

    except Exception as e:
        logger.error(f"Pipeline generation failed: {e}")

        # Log error
        audit_logger.log_operation({
            "type": "pipeline_generation_error",
            "agent": "pipeline",
            "inputs": request.dict(),
            "error": str(e),
            "status": "failed"
        })

        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def pipeline_health():
    """Check pipeline agent health"""
    try:
        # Check KB connectivity
        kb_stats = kb_manager.get_collection_stats()

        return {
            "status": "healthy",
            "kb_collections": len(kb_stats),
            "kb_documents": sum(stats["document_count"] for stats in kb_stats.values()),
            "components": {
                "pipeline_agent": "ready",
                "kb_manager": "connected",
                "pr_orchestrator": "ready"
            }
        }
    except Exception as e:
        logger.error(f"Pipeline health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {e}")

@router.get("/stack-analysis/{repo_url:path}")
async def analyze_repository_stack(repo_url: str):
    """Analyze repository stack without generating pipeline"""
    try:
        stack = pipeline_agent.analyze_repository(repo_url)

        return {
            "repo_url": repo_url,
            "stack": stack,
            "supported": True
        }
    except Exception as e:
        logger.error(f"Stack analysis failed for {repo_url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))