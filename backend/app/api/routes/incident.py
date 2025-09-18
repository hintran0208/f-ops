from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.core.agent import DevOpsAgent
from app.core.audit import AuditLogger, AuditAction
from app.core.database import get_db, Incident
from sqlalchemy.orm import Session
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
agent = DevOpsAgent()
audit = AuditLogger()

class IncidentCreateRequest(BaseModel):
    service_name: str
    severity: str = "medium"  # critical, high, medium, low
    title: str
    description: str
    metadata: Optional[Dict[str, Any]] = {}

class IncidentUpdateRequest(BaseModel):
    status: Optional[str] = None  # open, investigating, resolved
    root_cause: Optional[str] = None
    remediation: Optional[str] = None

class IncidentActionRequest(BaseModel):
    action_type: str  # rollback, restart, scale, custom
    parameters: Dict[str, Any]
    approve: bool = False

@router.post("/create")
async def create_incident(request: IncidentCreateRequest, db: Session = Depends(get_db)):
    """Create a new incident"""
    try:
        # Log incident creation
        audit.log_action(
            AuditAction.INCIDENT_CREATED,
            user="api",
            resource=request.service_name,
            details={
                "severity": request.severity,
                "title": request.title
            }
        )
        
        # Create incident in database
        incident = Incident(
            service_name=request.service_name,
            severity=request.severity,
            status="open",
            title=request.title,
            description=request.description,
            metadata=request.metadata
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        
        # Analyze incident through agent
        analysis = agent.analyze_incident(
            service_name=request.service_name,
            symptoms=request.description,
            user="api"
        )
        
        return {
            "success": True,
            "incident_id": incident.id,
            "service": request.service_name,
            "severity": request.severity,
            "status": "open",
            "analysis": analysis.get("analysis", "")[:500] if analysis["success"] else None,
            "message": "Incident created and analysis initiated"
        }
    except Exception as e:
        logger.error(f"Failed to create incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{incident_id}")
async def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """Get incident details"""
    try:
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        return {
            "success": True,
            "incident": {
                "id": incident.id,
                "service_name": incident.service_name,
                "severity": incident.severity,
                "status": incident.status,
                "title": incident.title,
                "description": incident.description,
                "root_cause": incident.root_cause,
                "remediation": incident.remediation,
                "created_at": incident.created_at.isoformat() if incident.created_at else None,
                "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
                "metadata": incident.metadata
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{incident_id}")
async def update_incident(
    incident_id: int,
    request: IncidentUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update incident status or details"""
    try:
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        # Update fields if provided
        if request.status:
            incident.status = request.status
            if request.status == "resolved":
                incident.resolved_at = datetime.utcnow()
                
                # Log incident resolution
                audit.log_action(
                    AuditAction.INCIDENT_RESOLVED,
                    user="api",
                    resource=incident.service_name,
                    details={"incident_id": incident_id}
                )
        
        if request.root_cause:
            incident.root_cause = request.root_cause
        
        if request.remediation:
            incident.remediation = request.remediation
        
        db.commit()
        db.refresh(incident)
        
        return {
            "success": True,
            "incident_id": incident_id,
            "status": incident.status,
            "message": "Incident updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{incident_id}/investigate")
async def investigate_incident(incident_id: int, db: Session = Depends(get_db)):
    """Investigate an incident with AI assistance"""
    try:
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        # Log investigation
        audit.log_action(
            AuditAction.INCIDENT_INVESTIGATED,
            user="api",
            resource=incident.service_name,
            details={"incident_id": incident_id}
        )
        
        # Perform investigation through agent
        analysis = agent.analyze_incident(
            service_name=incident.service_name,
            symptoms=f"{incident.title}: {incident.description}",
            user="api"
        )
        
        # Update incident with findings if successful
        if analysis["success"] and analysis.get("analysis"):
            # Extract root cause from analysis (simplified)
            incident.root_cause = analysis["analysis"][:500]
            incident.status = "investigating"
            db.commit()
        
        return {
            "success": True,
            "incident_id": incident_id,
            "investigation": analysis.get("analysis", ""),
            "recommended_actions": [
                {"action": "rollback", "description": "Rollback to previous version"},
                {"action": "scale", "description": "Scale up replicas"},
                {"action": "restart", "description": "Restart service pods"}
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to investigate incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{incident_id}/action")
async def execute_incident_action(
    incident_id: int,
    request: IncidentActionRequest,
    db: Session = Depends(get_db)
):
    """Execute an action to resolve incident"""
    try:
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        # Log action execution
        audit.log_action(
            AuditAction.INCIDENT_ACTION_EXECUTED,
            user="api",
            resource=incident.service_name,
            details={
                "incident_id": incident_id,
                "action": request.action_type,
                "parameters": request.parameters
            }
        )
        
        # Execute action based on type
        result = {"success": False, "message": "Action not implemented"}
        
        if request.action_type == "rollback":
            # Execute rollback through agent
            if 'kubernetes' in agent.mcp_packs:
                result = agent.mcp_packs['kubernetes'].execute_action(
                    "rollback",
                    {
                        "deployment_name": incident.service_name,
                        "namespace": request.parameters.get("environment", "staging")
                    }
                )
        elif request.action_type == "restart":
            # Execute restart
            if 'kubernetes' in agent.mcp_packs:
                result = agent.mcp_packs['kubernetes'].execute_action(
                    "restart_deployment",
                    {
                        "deployment_name": incident.service_name,
                        "namespace": request.parameters.get("environment", "staging")
                    }
                )
        elif request.action_type == "scale":
            # Execute scaling
            if 'kubernetes' in agent.mcp_packs:
                result = agent.mcp_packs['kubernetes'].execute_action(
                    "scale",
                    {
                        "deployment_name": incident.service_name,
                        "namespace": request.parameters.get("environment", "staging"),
                        "replicas": request.parameters.get("replicas", 3)
                    }
                )
        
        return {
            "success": result.get("success", False),
            "incident_id": incident_id,
            "action": request.action_type,
            "result": result,
            "message": f"Action {request.action_type} executed"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def list_incidents(
    status: Optional[str] = None,
    service: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """List incidents with optional filters"""
    try:
        query = db.query(Incident)
        
        if status:
            query = query.filter(Incident.status == status)
        if service:
            query = query.filter(Incident.service_name == service)
        if severity:
            query = query.filter(Incident.severity == severity)
        
        incidents = query.order_by(Incident.created_at.desc()).limit(limit).all()
        
        incident_list = []
        for incident in incidents:
            incident_list.append({
                "id": incident.id,
                "service_name": incident.service_name,
                "severity": incident.severity,
                "status": incident.status,
                "title": incident.title,
                "created_at": incident.created_at.isoformat() if incident.created_at else None,
                "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None
            })
        
        return {
            "success": True,
            "incidents": incident_list,
            "count": len(incident_list)
        }
    except Exception as e:
        logger.error(f"Failed to list incidents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/playbook/{scenario}")
async def get_incident_playbook(scenario: str):
    """Get incident response playbook for a scenario"""
    try:
        playbooks = {
            "high-latency": {
                "title": "High Latency Response",
                "steps": [
                    "Check current latency metrics",
                    "Identify affected endpoints",
                    "Review recent deployments",
                    "Check database performance",
                    "Scale if necessary",
                    "Consider rollback"
                ],
                "common_causes": [
                    "Slow database queries",
                    "Missing indexes",
                    "Cache misses",
                    "Resource constraints"
                ]
            },
            "outage": {
                "title": "Service Outage Response",
                "steps": [
                    "Declare incident",
                    "Check pod status",
                    "Review recent changes",
                    "Restart pods if needed",
                    "Scale up replicas",
                    "Rollback if necessary"
                ],
                "common_causes": [
                    "Deployment issues",
                    "Resource exhaustion",
                    "Configuration errors",
                    "External dependencies"
                ]
            },
            "memory-leak": {
                "title": "Memory Leak Response",
                "steps": [
                    "Monitor memory usage",
                    "Identify leaking service",
                    "Restart affected pods",
                    "Rollback if recent deployment",
                    "Increase memory limits temporarily",
                    "Fix and redeploy"
                ],
                "common_causes": [
                    "Unclosed connections",
                    "Cache growth",
                    "Event listener accumulation",
                    "Large object retention"
                ]
            }
        }
        
        playbook = playbooks.get(scenario)
        
        if not playbook:
            available = list(playbooks.keys())
            raise HTTPException(
                status_code=404,
                detail=f"Playbook '{scenario}' not found. Available: {available}"
            )
        
        return {
            "success": True,
            "scenario": scenario,
            "playbook": playbook
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get playbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))