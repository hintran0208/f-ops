from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class InfrastructureGenerateRequest(BaseModel):
    """Request model for infrastructure generation"""
    target: str = Field(..., description="Target platform (k8s, serverless, static)")
    environments: List[str] = Field(..., description="List of environments (staging, prod)")
    domain: Optional[str] = Field(None, description="Domain name for the application")
    registry: Optional[str] = Field(None, description="Container registry URL")
    secrets_strategy: Optional[str] = Field(None, description="Secrets management strategy")

    class Config:
        schema_extra = {
            "example": {
                "target": "k8s",
                "environments": ["staging", "prod"],
                "domain": "app.example.com",
                "registry": "docker.io/myorg",
                "secrets_strategy": "aws-secrets-manager"
            }
        }

class TerraformPlanResult(BaseModel):
    """Terraform plan execution result"""
    status: str = Field(..., description="Plan execution status")
    output: str = Field(..., description="Plan output")
    errors: str = Field(..., description="Error messages if any")
    summary: Dict[str, Any] = Field(..., description="Plan summary with resource counts")
    raw_output: Optional[str] = Field(None, description="Raw terraform plan output")

class HelmDryRunResult(BaseModel):
    """Helm dry-run execution result"""
    status: str = Field(..., description="Dry-run execution status")
    lint: Dict[str, Any] = Field(..., description="Helm lint results")
    manifests: List[Dict[str, Any]] = Field(..., description="Generated Kubernetes manifests")
    notes: str = Field(..., description="Helm chart notes")
    raw_output: str = Field(..., description="Raw helm dry-run output")
    errors: str = Field(..., description="Error messages if any")

class InfrastructureGenerateResponse(BaseModel):
    """Response model for infrastructure generation"""
    success: bool = Field(..., description="Operation success status")
    terraform: Optional[Dict[str, str]] = Field(None, description="Generated Terraform files")
    helm: Optional[Dict[str, str]] = Field(None, description="Generated Helm chart files")
    terraform_plan: Optional[TerraformPlanResult] = Field(None, description="Terraform plan results")
    helm_dry_run: Optional[HelmDryRunResult] = Field(None, description="Helm dry-run results")
    citations: List[str] = Field(..., description="Knowledge base citations")
    message: str = Field(..., description="Response message")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "terraform": {
                    "main.tf": "terraform configuration content...",
                    "modules/network/main.tf": "network module content..."
                },
                "helm": {
                    "Chart.yaml": "chart metadata...",
                    "values.yaml": "default values...",
                    "templates/deployment.yaml": "deployment template..."
                },
                "terraform_plan": {
                    "status": "success",
                    "summary": {
                        "add": 12,
                        "change": 0,
                        "destroy": 0,
                        "resources": []
                    }
                },
                "helm_dry_run": {
                    "status": "success",
                    "lint": {"passed": True},
                    "manifests": []
                },
                "citations": [
                    "iac:terraform-aws-vpc-001",
                    "iac:helm-best-practices-003"
                ],
                "message": "Infrastructure generated successfully"
            }
        }

class InfrastructureValidateRequest(BaseModel):
    """Request model for infrastructure validation"""
    terraform: Optional[Dict[str, str]] = Field(None, description="Terraform configuration files")
    helm: Optional[Dict[str, str]] = Field(None, description="Helm chart files")

    class Config:
        schema_extra = {
            "example": {
                "terraform": {
                    "main.tf": "terraform configuration to validate..."
                },
                "helm": {
                    "Chart.yaml": "chart to validate...",
                    "values.yaml": "values to validate..."
                }
            }
        }

class InfrastructureValidateResponse(BaseModel):
    """Response model for infrastructure validation"""
    success: bool = Field(..., description="Operation success status")
    valid: bool = Field(..., description="Overall validation status")
    terraform_valid: bool = Field(..., description="Terraform validation status")
    helm_valid: bool = Field(..., description="Helm validation status")
    terraform_errors: List[str] = Field(..., description="Terraform validation errors")
    helm_errors: List[str] = Field(..., description="Helm validation errors")
    warnings: List[str] = Field(..., description="Validation warnings")
    message: str = Field(..., description="Response message")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "valid": True,
                "terraform_valid": True,
                "helm_valid": True,
                "terraform_errors": [],
                "helm_errors": [],
                "warnings": ["Helm chart has minor lint warnings"],
                "message": "Validation completed"
            }
        }

class InfrastructureCreatePRRequest(BaseModel):
    """Request model for creating infrastructure PR"""
    repo_url: str = Field(..., description="Repository URL")
    target: str = Field(..., description="Target platform")
    environments: List[str] = Field(..., description="Environments")
    domain: str = Field(..., description="Domain name")
    terraform: Optional[Dict[str, str]] = Field(None, description="Terraform files")
    helm: Optional[Dict[str, str]] = Field(None, description="Helm chart files")
    terraform_plan: Optional[TerraformPlanResult] = Field(None, description="Terraform plan results")
    helm_dry_run: Optional[HelmDryRunResult] = Field(None, description="Helm dry-run results")
    citations: List[str] = Field(..., description="Knowledge base citations")

    class Config:
        schema_extra = {
            "example": {
                "repo_url": "https://github.com/user/repo",
                "target": "k8s",
                "environments": ["staging", "prod"],
                "domain": "app.example.com",
                "terraform": {"main.tf": "terraform content..."},
                "helm": {"Chart.yaml": "chart content..."},
                "citations": ["iac:terraform-aws-001"]
            }
        }

class InfrastructureCreatePRResponse(BaseModel):
    """Response model for infrastructure PR creation"""
    success: bool = Field(..., description="Operation success status")
    pr_url: str = Field(..., description="Created PR/MR URL")
    message: str = Field(..., description="Response message")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "pr_url": "https://github.com/user/repo/pull/123",
                "message": "PR created successfully with infrastructure configurations and validation artifacts"
            }
        }

# Additional helper models

class TerraformModule(BaseModel):
    """Terraform module definition"""
    name: str = Field(..., description="Module name")
    source: str = Field(..., description="Module source")
    variables: Dict[str, Any] = Field(..., description="Module variables")

class HelmValues(BaseModel):
    """Helm chart values"""
    values: Dict[str, Any] = Field(..., description="Chart values")
    environment_overrides: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Environment-specific overrides")

class ResourceSummary(BaseModel):
    """Resource summary for plans"""
    type: str = Field(..., description="Resource type")
    name: str = Field(..., description="Resource name")
    action: str = Field(..., description="Planned action (create, update, delete)")
    provider: Optional[str] = Field(None, description="Provider name")

class ValidationError(BaseModel):
    """Validation error details"""
    file: str = Field(..., description="File with error")
    line: Optional[int] = Field(None, description="Line number")
    message: str = Field(..., description="Error message")
    severity: str = Field(..., description="Error severity (error, warning, info)")

class DeploymentTarget(BaseModel):
    """Deployment target configuration"""
    name: str = Field(..., description="Target name")
    display_name: str = Field(..., description="Display name")
    description: str = Field(..., description="Target description")
    components: List[str] = Field(..., description="Required components")
    supported_environments: List[str] = Field(..., description="Supported environments")

class SecretsStrategy(BaseModel):
    """Secrets management strategy"""
    name: str = Field(..., description="Strategy name")
    display_name: str = Field(..., description="Display name")
    description: str = Field(..., description="Strategy description")
    provider: str = Field(..., description="Provider name")
    configuration: Dict[str, Any] = Field(..., description="Strategy configuration")