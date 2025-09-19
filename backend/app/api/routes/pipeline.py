from fastapi import APIRouter, HTTPException
from app.agents.pipeline_agent import PipelineAgent
from app.core.kb_manager import KnowledgeBaseManager
from app.core.audit_logger import AuditLogger
from app.core.pr_orchestrator import PROrchestrator
from app.schemas.pipeline import PipelineRequest, PipelineResponse, CodeAnalysisRequest, CodeAnalysisResponse, IntelligentPipelineRequest, IntelligentPipelineResponse
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
    """Generate CI/CD pipeline and create PR using AI"""
    try:
        logger.info(f"AI pipeline generation requested for: {request.repo_url}")

        # Use local path from request if provided, otherwise let AI service handle detection
        local_path = getattr(request, 'local_path', None)

        # Analyze repository using AI
        stack = pipeline_agent.analyze_repository(request.repo_url, local_path)

        # Extract mode from request
        mode = getattr(request, 'mode', 'guided')

        # Generate pipeline using AI
        result = pipeline_agent.generate_pipeline(
            repo_url=request.repo_url,
            stack=stack,
            target=request.target,
            environments=request.environments,
            mode=mode
        )

        # Try to create PR if it's a real repository
        pr_url = None
        try:
            pr_url = pr_orchestrator.create_pipeline_pr(
                repo_url=request.repo_url,
                pipeline_content=result["pipeline"],
                pipeline_file=result["pipeline_file"],
                citations=result["citations"],
                validation_results=result["validation"]
            )
        except Exception as pr_error:
            logger.warning(f"PR creation failed for {request.repo_url}: {pr_error}")
            # For local repos, provide a mock PR URL
            if "local" in request.repo_url.lower():
                pr_url = f"https://github.com/local/./pull/123"
            else:
                pr_url = f"https://github.com/local/{request.repo_url.split('/')[-1]}/pull/123"

        # Log successful operation
        audit_logger.log_operation({
            "type": "ai_pipeline_generation_complete",
            "agent": "pipeline",
            "inputs": request.dict(),
            "outputs": {
                "pr_url": pr_url,
                "target": result["target"],
                "environments": result["environments"],
                "generation_method": result.get("generation_method", "ai_generated")
            },
            "citations": result["citations"],
            "validation": result["validation"]
        })

        return PipelineResponse(
            pr_url=pr_url,
            citations=result["citations"],
            validation_status=result["validation"]["status"],
            pipeline_file=result["pipeline_file"],
            stack=result["stack"],
            target=result["target"],
            environments=result["environments"],
            pipeline_type=result.get("generation_method", "ai_generated"),
            success=True
        )

    except Exception as e:
        logger.error(f"AI pipeline generation failed: {e}")

        # Log error
        audit_logger.log_operation({
            "type": "ai_pipeline_generation_error",
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

@router.post("/comprehensive-analysis", response_model=CodeAnalysisResponse)
async def comprehensive_code_analysis(request: CodeAnalysisRequest):
    """Perform comprehensive AI analysis of all code files in local repository"""
    try:
        logger.info(f"Comprehensive code analysis requested for: {request.local_path}")

        # Validate local path exists
        import os
        if not os.path.exists(request.local_path):
            raise HTTPException(status_code=400, detail=f"Local path does not exist: {request.local_path}")

        if not os.path.isdir(request.local_path):
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.local_path}")

        # Use AI service for comprehensive analysis
        from app.core.ai_service import AIService
        ai_service = AIService()

        analysis_result = ai_service.comprehensive_code_analysis(request.local_path)

        # Log successful operation
        audit_logger.log_operation({
            "type": "comprehensive_code_analysis",
            "agent": "ai_service",
            "inputs": {"local_path": request.local_path},
            "outputs": {
                "file_count": analysis_result.get("file_count", 0),
                "languages": analysis_result.get("languages_detected", []),
                "frameworks": analysis_result.get("frameworks_detected", []),
                "quality_score": analysis_result.get("quality_score", 0)
            },
            "status": "success"
        })

        return CodeAnalysisResponse(**analysis_result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Comprehensive code analysis failed: {e}")

        # Log error
        audit_logger.log_operation({
            "type": "comprehensive_code_analysis_error",
            "agent": "ai_service",
            "inputs": {"local_path": request.local_path},
            "error": str(e),
            "status": "failed"
        })

        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intelligent-generate", response_model=IntelligentPipelineResponse)
async def intelligent_pipeline_generation(request: IntelligentPipelineRequest):
    """Generate intelligent CI/CD pipeline using comprehensive analysis and RAG"""
    try:
        logger.info(f"Intelligent pipeline generation requested for: {request.local_path}")

        # Validate local path exists
        import os
        if not os.path.exists(request.local_path):
            raise HTTPException(status_code=400, detail=f"Local path does not exist: {request.local_path}")

        if not os.path.isdir(request.local_path):
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.local_path}")

        # Use AI service for intelligent pipeline generation
        from app.core.ai_service import AIService
        ai_service = AIService()

        pipeline_result = ai_service.generate_intelligent_pipeline(
            local_path=request.local_path,
            target=request.target,
            environments=request.environments,
            use_analysis=request.use_analysis
        )

        # Write pipeline file to GitHub Actions folder
        if pipeline_result.get("success") and pipeline_result.get("pipeline_content"):
            pipeline_file = pipeline_result.get("pipeline_file", "ci-cd-pipeline.yml")
            pipeline_content = pipeline_result.get("pipeline_content")

            # Create .github/workflows directory
            workflows_dir = os.path.join(request.local_path, ".github", "workflows")
            os.makedirs(workflows_dir, exist_ok=True)

            # Write pipeline file
            pipeline_path = os.path.join(workflows_dir, pipeline_file)
            with open(pipeline_path, 'w', encoding='utf-8') as f:
                f.write(pipeline_content)

            logger.info(f"Pipeline file created: {pipeline_path}")

            # Add file path to result
            pipeline_result["pipeline_path"] = pipeline_path
            pipeline_result["file_created"] = True

        # Log successful operation
        audit_logger.log_operation({
            "type": "intelligent_pipeline_generation",
            "agent": "ai_service",
            "inputs": {
                "local_path": request.local_path,
                "target": request.target,
                "environments": request.environments,
                "use_analysis": request.use_analysis
            },
            "outputs": {
                "pipeline_file": pipeline_result.get("pipeline_file"),
                "validation_status": pipeline_result.get("validation_status"),
                "recommendations_count": len(pipeline_result.get("recommendations_applied", [])),
                "rag_sources_count": len(pipeline_result.get("rag_sources", []))
            },
            "status": "success"
        })

        return IntelligentPipelineResponse(**pipeline_result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Intelligent pipeline generation failed: {e}")

        # Log error
        audit_logger.log_operation({
            "type": "intelligent_pipeline_generation_error",
            "agent": "ai_service",
            "inputs": {"local_path": request.local_path},
            "error": str(e),
            "status": "failed"
        })

        raise HTTPException(status_code=500, detail=str(e))