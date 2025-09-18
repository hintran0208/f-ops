from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.core.agent import DevOpsAgent
from app.core.audit import AuditLogger, AuditAction
from app.core.database import get_db, Deployment
from sqlalchemy.orm import Session
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services  
agent = DevOpsAgent()
audit = AuditLogger()

class DeployRequest(BaseModel):
    service_name: str
    environment: str = "staging"
    version: Optional[str] = None
    dry_run: bool = True
    approve: bool = False
    metadata: Optional[Dict[str, Any]] = {}

class ScaleRequest(BaseModel):
    service_name: str
    environment: str = "staging"
    replicas: int

class RollbackRequest(BaseModel):
    service_name: str
    environment: str = "staging"
    target_version: Optional[str] = None

@router.post("/service")
async def deploy_service(request: DeployRequest):
    """Deploy a service to an environment"""
    try:
        # Log deployment initiation
        audit.log_action(
            AuditAction.DEPLOYMENT_INITIATED,
            user="api",
            resource=request.service_name,
            details={
                "environment": request.environment,
                "version": request.version,
                "dry_run": request.dry_run
            }
        )
        
        # Execute deployment through agent
        result = agent.deploy_service(
            service_name=request.service_name,
            environment=request.environment,
            version=request.version,
            dry_run=request.dry_run,
            user="api"
        )
        
        if result["success"]:
            if not request.dry_run:
                # Log successful deployment
                audit.log_action(
                    AuditAction.DEPLOYMENT_COMPLETED,
                    user="api",
                    resource=request.service_name,
                    details=result
                )
            
            return {
                "success": True,
                "service": request.service_name,
                "environment": request.environment,
                "version": request.version or "latest",
                "dry_run": request.dry_run,
                "message": result.get("message", "Deployment successful"),
                "details": result
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Deployment failed"))
    
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        
        # Log failed deployment
        audit.log_action(
            AuditAction.DEPLOYMENT_FAILED,
            user="api",
            resource=request.service_name,
            details={"error": str(e)}
        )
        
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scale")
async def scale_service(request: ScaleRequest):
    """Scale a service deployment"""
    try:
        if 'kubernetes' not in agent.mcp_packs:
            raise HTTPException(status_code=503, detail="Kubernetes pack not available")
        
        # Execute scaling
        result = agent.mcp_packs['kubernetes'].execute_action(
            "scale",
            {
                "deployment_name": request.service_name,
                "namespace": request.environment,
                "replicas": request.replicas
            }
        )
        
        if result["success"]:
            return {
                "success": True,
                "service": request.service_name,
                "environment": request.environment,
                "replicas": request.replicas,
                "previous_replicas": result.get("previous_replicas"),
                "message": f"Scaled {request.service_name} to {request.replicas} replicas"
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Scaling failed"))
    
    except Exception as e:
        logger.error(f"Scaling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rollback")
async def rollback_deployment(request: RollbackRequest):
    """Rollback a service deployment"""
    try:
        # Log rollback initiation
        audit.log_action(
            AuditAction.DEPLOYMENT_ROLLBACK,
            user="api",
            resource=request.service_name,
            details={
                "environment": request.environment,
                "target_version": request.target_version
            }
        )
        
        if 'kubernetes' not in agent.mcp_packs:
            raise HTTPException(status_code=503, detail="Kubernetes pack not available")
        
        # Execute rollback
        result = agent.mcp_packs['kubernetes'].execute_action(
            "rollback",
            {
                "deployment_name": request.service_name,
                "namespace": request.environment,
                "revision": request.target_version
            }
        )
        
        if result["success"]:
            return {
                "success": True,
                "service": request.service_name,
                "environment": request.environment,
                "message": "Rollback initiated successfully",
                "details": result
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Rollback failed"))
    
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{service_name}")
async def get_deployment_status(service_name: str, environment: str = "staging"):
    """Get deployment status for a service"""
    try:
        if 'kubernetes' not in agent.mcp_packs:
            # Return mock status if K8s not available
            return {
                "success": True,
                "service": service_name,
                "environment": environment,
                "status": "running",
                "replicas": {"desired": 3, "ready": 3},
                "version": "v1.2.3",
                "last_updated": "2024-01-15T14:30:00Z"
            }
        
        # Get actual deployment status
        result = agent.mcp_packs['kubernetes'].execute_action(
            "get_deployments",
            {"namespace": environment}
        )
        
        # Find the specific deployment
        deployments = result.get("deployments", [])
        deployment = next((d for d in deployments if d["name"] == service_name), None)
        
        if deployment:
            return {
                "success": True,
                "service": service_name,
                "environment": environment,
                "status": "running" if deployment.get("ready_replicas", 0) > 0 else "stopped",
                "replicas": {
                    "desired": deployment.get("replicas", 0),
                    "ready": deployment.get("ready_replicas", 0)
                },
                "conditions": deployment.get("conditions", [])
            }
        else:
            raise HTTPException(status_code=404, detail=f"Deployment {service_name} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{service_name}")
async def get_deployment_history(service_name: str, environment: str = "staging", limit: int = 10):
    """Get deployment history for a service"""
    try:
        # Mock history - in production, query from database
        history = [
            {
                "version": "v1.2.3",
                "status": "success",
                "deployed_by": "john.doe",
                "deployed_at": "2024-01-15T14:30:00Z",
                "duration_seconds": 135
            },
            {
                "version": "v1.2.2",
                "status": "success",
                "deployed_by": "jane.smith",
                "deployed_at": "2024-01-14T10:15:00Z",
                "duration_seconds": 105
            },
            {
                "version": "v1.2.1",
                "status": "failed",
                "deployed_by": "john.doe",
                "deployed_at": "2024-01-13T16:20:00Z",
                "duration_seconds": 190,
                "error": "Health check failed"
            }
        ]
        
        return {
            "success": True,
            "service": service_name,
            "environment": environment,
            "history": history[:limit],
            "count": len(history[:limit])
        }
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_deployments(environment: str = "staging"):
    """List all deployments in an environment"""
    try:
        if 'kubernetes' not in agent.mcp_packs:
            # Return mock list if K8s not available
            return {
                "success": True,
                "environment": environment,
                "deployments": [
                    {
                        "name": "api-gateway",
                        "status": "running",
                        "replicas": {"desired": 3, "ready": 3},
                        "version": "v1.2.3"
                    },
                    {
                        "name": "user-service",
                        "status": "running",
                        "replicas": {"desired": 2, "ready": 2},
                        "version": "v2.0.1"
                    }
                ],
                "count": 2
            }
        
        # Get actual deployments
        result = agent.mcp_packs['kubernetes'].execute_action(
            "get_deployments",
            {"namespace": environment}
        )
        
        deployments = []
        for deployment in result.get("deployments", []):
            deployments.append({
                "name": deployment["name"],
                "status": "running" if deployment.get("ready_replicas", 0) > 0 else "stopped",
                "replicas": {
                    "desired": deployment.get("replicas", 0),
                    "ready": deployment.get("ready_replicas", 0)
                }
            })
        
        return {
            "success": True,
            "environment": environment,
            "deployments": deployments,
            "count": len(deployments)
        }
    except Exception as e:
        logger.error(f"Failed to list deployments: {e}")
        raise HTTPException(status_code=500, detail=str(e))