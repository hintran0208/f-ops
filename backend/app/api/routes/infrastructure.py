from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
import logging
from app.agents.infrastructure_agent import InfrastructureAgent
from app.core.kb_manager import KnowledgeBaseManager
from app.core.citation_engine import CitationEngine
from app.core.audit_logger import AuditLogger
from app.core.ai_service import AIService
from app.core.pr_orchestrator import PROrchestrator
from app.schemas.infrastructure import (
    InfrastructureGenerateRequest,
    InfrastructureGenerateResponse,
    InfrastructureValidateRequest,
    InfrastructureValidateResponse,
    InfrastructureCreatePRRequest,
    InfrastructureCreatePRResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency injection
def get_infrastructure_agent() -> InfrastructureAgent:
    """Get Infrastructure Agent instance with dependencies"""
    kb_manager = KnowledgeBaseManager()
    citation_engine = CitationEngine(kb_manager)
    audit_logger = AuditLogger()
    ai_service = AIService()

    return InfrastructureAgent(
        kb=kb_manager,
        citation_engine=citation_engine,
        audit_logger=audit_logger,
        ai_service=ai_service
    )

def get_pr_orchestrator() -> PROrchestrator:
    """Get PR Orchestrator instance"""
    return PROrchestrator()

@router.post("/generate", response_model=InfrastructureGenerateResponse)
async def generate_infrastructure(
    request: InfrastructureGenerateRequest,
    agent: InfrastructureAgent = Depends(get_infrastructure_agent)
) -> InfrastructureGenerateResponse:
    """Generate infrastructure configurations with validation"""

    try:
        logger.info(f"Generating infrastructure for target: {request.target}")

        # Generate infrastructure
        result = agent.generate_infrastructure(
            target=request.target,
            environments=request.environments,
            domain=request.domain or f"app-{request.target}.example.com",
            registry=request.registry or "docker.io/myorg",
            secrets_strategy=request.secrets_strategy or "aws-secrets-manager"
        )

        return InfrastructureGenerateResponse(
            success=True,
            terraform=result["terraform"],
            helm=result["helm"],
            terraform_plan=result["terraform_plan"],
            helm_dry_run=result["helm_dry_run"],
            citations=result["citations"],
            message="Infrastructure generated successfully"
        )

    except Exception as e:
        logger.error(f"Infrastructure generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Infrastructure generation failed: {str(e)}"
        )

@router.post("/validate", response_model=InfrastructureValidateResponse)
async def validate_infrastructure(
    request: InfrastructureValidateRequest,
    agent: InfrastructureAgent = Depends(get_infrastructure_agent)
) -> InfrastructureValidateResponse:
    """Validate infrastructure configurations"""

    try:
        logger.info("Validating infrastructure configurations")

        validation_results = {
            "terraform_valid": True,
            "helm_valid": True,
            "terraform_errors": [],
            "helm_errors": [],
            "warnings": []
        }

        # Validate Terraform if provided
        if request.terraform:
            try:
                terraform_plan = agent._run_terraform_plan(request.terraform)
                if terraform_plan["status"] == "failed":
                    validation_results["terraform_valid"] = False
                    validation_results["terraform_errors"].append(terraform_plan.get("errors", "Unknown error"))
            except Exception as e:
                validation_results["terraform_valid"] = False
                validation_results["terraform_errors"].append(str(e))

        # Validate Helm if provided
        if request.helm:
            try:
                helm_dry_run = agent._run_helm_dry_run(request.helm)
                if helm_dry_run["status"] == "failed":
                    validation_results["helm_valid"] = False
                    validation_results["helm_errors"].append(helm_dry_run.get("errors", "Unknown error"))

                # Check lint results
                if not helm_dry_run.get("lint", {}).get("passed", True):
                    validation_results["warnings"].append("Helm chart has lint warnings")

            except Exception as e:
                validation_results["helm_valid"] = False
                validation_results["helm_errors"].append(str(e))

        overall_valid = validation_results["terraform_valid"] and validation_results["helm_valid"]

        return InfrastructureValidateResponse(
            success=True,
            valid=overall_valid,
            terraform_valid=validation_results["terraform_valid"],
            helm_valid=validation_results["helm_valid"],
            terraform_errors=validation_results["terraform_errors"],
            helm_errors=validation_results["helm_errors"],
            warnings=validation_results["warnings"],
            message="Validation completed"
        )

    except Exception as e:
        logger.error(f"Infrastructure validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Infrastructure validation failed: {str(e)}"
        )

@router.post("/create-pr", response_model=InfrastructureCreatePRResponse)
async def create_infrastructure_pr(
    request: InfrastructureCreatePRRequest,
    pr_orchestrator: PROrchestrator = Depends(get_pr_orchestrator)
) -> InfrastructureCreatePRResponse:
    """Create PR/MR with infrastructure configs and dry-run artifacts"""

    try:
        logger.info(f"Creating PR for infrastructure: {request.repo_url}")

        # Prepare files for PR
        files = {}

        # Add Terraform files
        if request.terraform:
            for path, content in request.terraform.items():
                files[f"infra/{path}"] = content

        # Add Helm files
        if request.helm:
            for path, content in request.helm.items():
                files[f"deploy/chart/{path}"] = content

        # Prepare PR body with citations
        pr_body = f"""# Infrastructure Configuration

## Summary
This PR adds infrastructure configuration for {request.target} deployment.

**Target Platform**: {request.target}
**Environments**: {', '.join(request.environments)}
**Domain**: {request.domain}

## Generated Components
"""

        if request.terraform:
            pr_body += f"""
### Terraform Infrastructure
- Network modules (VPC, subnets, NAT gateways)
- Container registry (ECR)
- DNS configuration (Route53, ACM certificates)
- Secrets management (AWS Secrets Manager)
"""

        if request.helm:
            pr_body += f"""
### Helm Chart
- Kubernetes deployment configuration
- Service and ingress definitions
- ConfigMaps and environment-specific values
- Autoscaling and resource limits
"""

        if request.citations:
            pr_body += f"""
## Knowledge Base Citations
This configuration was generated using the following sources:
{chr(10).join(['- ' + citation for citation in request.citations])}
"""

        # Prepare artifacts for attachment
        artifacts = {}

        if request.terraform_plan:
            artifacts["terraform_plan"] = request.terraform_plan

        if request.helm_dry_run:
            artifacts["helm_dry_run"] = request.helm_dry_run

        # Create PR with artifacts
        pr_url = pr_orchestrator.create_pr_with_artifacts(
            repo_url=request.repo_url,
            files=files,
            title=f"[F-Ops] Add {request.target} infrastructure configuration",
            body=pr_body,
            artifacts=artifacts
        )

        return InfrastructureCreatePRResponse(
            success=True,
            pr_url=pr_url,
            message="PR created successfully with infrastructure configurations and validation artifacts"
        )

    except Exception as e:
        logger.error(f"PR creation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"PR creation failed: {str(e)}"
        )

@router.get("/health")
async def infrastructure_health_check():
    """Health check for Infrastructure Agent"""
    try:
        # Basic health check - ensure dependencies are available
        agent = get_infrastructure_agent()

        return {
            "status": "healthy",
            "service": "infrastructure-agent",
            "capabilities": [
                "terraform-generation",
                "helm-charts",
                "dry-run-validation",
                "pr-creation"
            ]
        }
    except Exception as e:
        logger.error(f"Infrastructure Agent health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Infrastructure Agent service unavailable"
        )

@router.get("/targets")
async def get_supported_targets():
    """Get supported deployment targets"""
    return {
        "targets": [
            {
                "name": "k8s",
                "display_name": "Kubernetes",
                "description": "Container orchestration with Kubernetes",
                "components": ["terraform", "helm"]
            },
            {
                "name": "serverless",
                "display_name": "Serverless (AWS Lambda)",
                "description": "Serverless deployment with AWS Lambda",
                "components": ["terraform"]
            },
            {
                "name": "static",
                "display_name": "Static Site (S3 + CloudFront)",
                "description": "Static site hosting with S3 and CloudFront",
                "components": ["terraform"]
            }
        ]
    }

@router.get("/secrets-strategies")
async def get_secrets_strategies():
    """Get supported secrets management strategies"""
    return {
        "strategies": [
            {
                "name": "aws-secrets-manager",
                "display_name": "AWS Secrets Manager",
                "description": "AWS managed secrets service",
                "provider": "aws"
            },
            {
                "name": "k8s-secrets",
                "display_name": "Kubernetes Secrets",
                "description": "Native Kubernetes secrets",
                "provider": "kubernetes"
            },
            {
                "name": "vault",
                "display_name": "HashiCorp Vault",
                "description": "External Vault instance",
                "provider": "hashicorp"
            }
        ]
    }

@router.post("/terraform/plan")
async def run_terraform_plan(request: Dict[str, Any]):
    """Run terraform plan on provided configuration"""
    try:
        agent = get_infrastructure_agent()

        config = request.get("config", {})
        if not config:
            raise HTTPException(status_code=400, detail="Terraform configuration required")

        plan_result = agent._run_terraform_plan(config)

        return {
            "success": True,
            "plan": plan_result
        }

    except Exception as e:
        logger.error(f"Terraform plan failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Terraform plan failed: {str(e)}"
        )

@router.post("/helm/dry-run")
async def run_helm_dry_run(request: Dict[str, Any]):
    """Run helm dry-run on provided chart"""
    try:
        agent = get_infrastructure_agent()

        chart = request.get("chart", {})
        if not chart:
            raise HTTPException(status_code=400, detail="Helm chart configuration required")

        dry_run_result = agent._run_helm_dry_run(chart)

        return {
            "success": True,
            "dry_run": dry_run_result
        }

    except Exception as e:
        logger.error(f"Helm dry-run failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Helm dry-run failed: {str(e)}"
        )