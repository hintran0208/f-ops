from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
from app.core.agent import DevOpsAgent
from app.core.audit import AuditLogger, AuditAction
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
agent = DevOpsAgent()
audit = AuditLogger()

class OnboardRequest(BaseModel):
    repo_url: str
    target: str = "k8s"  # k8s, serverless, static
    environments: List[str] = ["staging", "prod"]
    auto_detect: bool = True
    dry_run: bool = True

class OnboardStatusRequest(BaseModel):
    repo_url: str

@router.post("/repo")
async def onboard_repository(request: OnboardRequest, background_tasks: BackgroundTasks):
    """Onboard a new repository with zero-to-deploy setup"""
    try:
        # Log onboarding start
        audit.log_action(
            AuditAction.ONBOARDING_STARTED,
            user="api",
            resource=request.repo_url,
            details={
                "target": request.target,
                "environments": request.environments,
                "dry_run": request.dry_run
            }
        )
        
        # Process onboarding through agent
        result = agent.onboard_repository(
            repo_url=request.repo_url,
            target=request.target,
            environments=request.environments,
            user="api"
        )
        
        if result["success"]:
            # Log successful onboarding
            audit.log_action(
                AuditAction.ONBOARDING_COMPLETED,
                user="api",
                resource=request.repo_url,
                details={"response_length": len(result.get("response", ""))}
            )
            
            return {
                "success": True,
                "repo_url": request.repo_url,
                "target": request.target,
                "environments": request.environments,
                "pr_url": f"https://github.com/{request.repo_url.split('/')[-2]}/{request.repo_url.split('/')[-1]}/pull/123",  # Mock PR URL
                "message": "Onboarding completed successfully",
                "details": result.get("response", "")[:500]  # First 500 chars of response
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Onboarding failed"))
    
    except Exception as e:
        logger.error(f"Onboarding failed: {e}")
        
        # Log failed onboarding
        audit.log_action(
            AuditAction.ONBOARDING_FAILED,
            user="api",
            resource=request.repo_url,
            details={"error": str(e)}
        )
        
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{repo_name}")
async def get_onboarding_status(repo_name: str):
    """Get onboarding status for a repository"""
    try:
        # Mock status - in production, this would query actual status
        return {
            "success": True,
            "repo_name": repo_name,
            "status": "completed",
            "environments": ["staging", "prod"],
            "ci_cd": "GitHub Actions",
            "infrastructure": "Kubernetes",
            "last_deployment": "2024-01-15T14:30:00Z"
        }
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_onboarded_repos():
    """List all onboarded repositories"""
    try:
        # Mock list - in production, this would query database
        repos = [
            {
                "name": "user/api-service",
                "status": "active",
                "environments": ["staging", "prod"],
                "target": "k8s",
                "onboarded_at": "2024-01-10T10:00:00Z"
            },
            {
                "name": "user/web-app",
                "status": "active",
                "environments": ["dev", "staging", "prod"],
                "target": "static",
                "onboarded_at": "2024-01-12T15:00:00Z"
            }
        ]
        
        return {
            "success": True,
            "repositories": repos,
            "count": len(repos)
        }
    except Exception as e:
        logger.error(f"Failed to list repos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate")
async def validate_repository(request: OnboardRequest):
    """Validate a repository before onboarding"""
    try:
        # Mock validation - in production, would actually clone and analyze repo
        validation_results = {
            "valid": True,
            "detected_stack": "Python/FastAPI",
            "detected_build_system": "pip",
            "detected_test_framework": "pytest",
            "has_dockerfile": True,
            "has_ci_config": False,
            "recommendations": [
                "Add GitHub Actions workflow",
                "Include health check endpoints",
                "Add environment-specific configs"
            ]
        }
        
        return {
            "success": True,
            "repo_url": request.repo_url,
            "validation": validation_results
        }
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))