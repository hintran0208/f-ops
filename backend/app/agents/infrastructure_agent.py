from typing import Dict, Any, List, Optional
import subprocess
import tempfile
import yaml
import json
import os
import logging
from app.core.kb_manager import KnowledgeBaseManager
from app.core.citation_engine import CitationEngine
from app.core.audit_logger import AuditLogger
from app.core.ai_service import AIService

logger = logging.getLogger(__name__)

class InfrastructureAgent:
    """Infrastructure Agent for generating Terraform modules and Helm charts with validation"""

    def __init__(self, kb: KnowledgeBaseManager, citation_engine: CitationEngine,
                 audit_logger: AuditLogger, ai_service: AIService):
        self.kb = kb
        self.citation_engine = citation_engine
        self.audit_logger = audit_logger
        self.ai_service = ai_service

    def generate_infrastructure(self,
                              target: str,
                              environments: List[str],
                              domain: str,
                              registry: str,
                              secrets_strategy: str) -> Dict[str, Any]:
        """Generate Terraform and Helm configs with validation"""
        logger.info(f"Generating infrastructure for target: {target}")

        try:
            # 1. Search KB for similar infrastructure patterns
            similar_infra = self.kb.search(
                collection='iac',
                query=f"{target} infrastructure terraform helm",
                k=5
            )

            # 2. Generate Terraform modules
            terraform_config = self._generate_terraform(
                target, environments, domain, registry
            )

            # 3. Generate Helm charts (if k8s)
            helm_chart = None
            if target == "k8s":
                helm_chart = self._generate_helm_chart(
                    environments, domain, registry
                )

            # 4. Run terraform plan (dry-run)
            terraform_plan = self._run_terraform_plan(terraform_config)

            # 5. Run helm --dry-run (if k8s)
            helm_dry_run = None
            if helm_chart:
                helm_dry_run = self._run_helm_dry_run(helm_chart)

            # 6. Add citations
            result_with_citations = self.citation_engine.generate_citations(
                json.dumps({
                    "terraform": terraform_config,
                    "helm": helm_chart
                }),
                similar_infra
            )

            # 7. Log agent decision
            self.audit_logger.log_agent_decision("infrastructure", {
                "action": "infrastructure_generation",
                "target": target,
                "environments": environments,
                "terraform_plan_status": terraform_plan.get("status"),
                "helm_dry_run_status": helm_dry_run.get("status") if helm_dry_run else None,
                "citations_count": len(similar_infra),
                "reasoning": f"Generated {target} infrastructure with validation"
            })

            return {
                "terraform": terraform_config,
                "helm": helm_chart,
                "terraform_plan": terraform_plan,
                "helm_dry_run": helm_dry_run,
                "citations": [s.get('citation', s.get('source', 'Unknown source')) for s in similar_infra]
            }

        except Exception as e:
            logger.error(f"Infrastructure generation failed: {e}")
            self.audit_logger.log_agent_decision("infrastructure", {
                "action": "infrastructure_generation_failed",
                "target": target,
                "error": str(e),
                "reasoning": "Infrastructure generation failed with error"
            })
            raise

    def _generate_terraform(self, target: str, envs: List[str],
                           domain: str, registry: str) -> Dict[str, str]:
        """Generate Terraform modules"""
        files = {}

        # Main configuration
        files['main.tf'] = f"""terraform {{
  required_version = ">= 1.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = var.aws_region
}}

# Variables
variable "aws_region" {{
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}}

variable "environment" {{
  description = "Environment name"
  type        = string
}}

variable "domain" {{
  description = "Domain name"
  type        = string
  default     = "{domain}"
}}

variable "registry" {{
  description = "Container registry"
  type        = string
  default     = "{registry}"
}}

# Network module
module "network" {{
  source = "./modules/network"

  environment = var.environment
  domain      = var.domain
}}

# Registry module
module "registry" {{
  source = "./modules/registry"

  environment = var.environment
  registry    = var.registry
}}

# DNS module
module "dns" {{
  source = "./modules/dns"

  environment = var.environment
  domain      = var.domain
}}

# Secrets module
module "secrets" {{
  source = "./modules/secrets"

  environment = var.environment
}}
"""

        # Network module
        files['modules/network/main.tf'] = self._generate_network_module()
        files['modules/network/variables.tf'] = self._generate_network_variables()
        files['modules/network/outputs.tf'] = self._generate_network_outputs()

        # Registry module
        files['modules/registry/main.tf'] = self._generate_registry_module(registry)
        files['modules/registry/variables.tf'] = self._generate_registry_variables()
        files['modules/registry/outputs.tf'] = self._generate_registry_outputs()

        # DNS module
        files['modules/dns/main.tf'] = self._generate_dns_module(domain)
        files['modules/dns/variables.tf'] = self._generate_dns_variables()
        files['modules/dns/outputs.tf'] = self._generate_dns_outputs()

        # Secrets module
        files['modules/secrets/main.tf'] = self._generate_secrets_module()
        files['modules/secrets/variables.tf'] = self._generate_secrets_variables()
        files['modules/secrets/outputs.tf'] = self._generate_secrets_outputs()

        # Environment-specific configs
        for env in envs:
            files[f'environments/{env}/terraform.tfvars'] = self._generate_env_vars(env)

        return files

    def _generate_network_module(self) -> str:
        """Generate network module configuration"""
        return """# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.environment}-vpc"
    Environment = var.environment
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "${var.environment}-igw"
    Environment = var.environment
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count = 2

  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.environment}-public-${count.index + 1}"
    Environment = var.environment
    Type        = "public"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count = 2

  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name        = "${var.environment}-private-${count.index + 1}"
    Environment = var.environment
    Type        = "private"
  }
}

# NAT Gateways
resource "aws_eip" "nat" {
  count = 2

  domain = "vpc"

  tags = {
    Name        = "${var.environment}-nat-${count.index + 1}"
    Environment = var.environment
  }
}

resource "aws_nat_gateway" "main" {
  count = 2

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name        = "${var.environment}-nat-${count.index + 1}"
    Environment = var.environment
  }

  depends_on = [aws_internet_gateway.main]
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name        = "${var.environment}-public-rt"
    Environment = var.environment
  }
}

resource "aws_route_table" "private" {
  count = 2

  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = {
    Name        = "${var.environment}-private-rt-${count.index + 1}"
    Environment = var.environment
  }
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count = 2

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = 2

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}
"""

    def _generate_network_variables(self) -> str:
        """Generate network module variables"""
        return """variable "environment" {
  description = "Environment name"
  type        = string
}

variable "domain" {
  description = "Domain name"
  type        = string
}
"""

    def _generate_network_outputs(self) -> str:
        """Generate network module outputs"""
        return """output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = aws_vpc.main.cidr_block
}
"""

    def _generate_registry_module(self, registry: str) -> str:
        """Generate registry module configuration"""
        return f"""# ECR Repository
resource "aws_ecr_repository" "app" {{
  name                 = "${{var.environment}}-app"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {{
    scan_on_push = true
  }}

  lifecycle_policy {{
    policy = jsonencode({{
      rules = [
        {{
          rulePriority = 1
          description  = "Keep last 30 images"
          selection = {{
            tagStatus     = "tagged"
            tagPrefixList = ["v"]
            countType     = "imageCountMoreThan"
            countNumber   = 30
          }}
          action = {{
            type = "expire"
          }}
        }}
      ]
    }})
  }}

  tags = {{
    Name        = "${{var.environment}}-app-repo"
    Environment = var.environment
    Registry    = "{registry}"
  }}
}}

# ECR Repository Policy
resource "aws_ecr_repository_policy" "app" {{
  repository = aws_ecr_repository.app.name

  policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [
      {{
        Sid    = "AllowPull"
        Effect = "Allow"
        Principal = {{
          AWS = "*"
        }}
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability"
        ]
      }}
    ]
  }})
}}
"""

    def _generate_registry_variables(self) -> str:
        """Generate registry module variables"""
        return """variable "environment" {
  description = "Environment name"
  type        = string
}

variable "registry" {
  description = "Container registry"
  type        = string
}
"""

    def _generate_registry_outputs(self) -> str:
        """Generate registry module outputs"""
        return """output "repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.app.repository_url
}

output "repository_name" {
  description = "ECR repository name"
  value       = aws_ecr_repository.app.name
}
"""

    def _generate_dns_module(self, domain: str) -> str:
        """Generate DNS module configuration"""
        return f"""# Route53 Hosted Zone
resource "aws_route53_zone" "main" {{
  name = var.domain

  tags = {{
    Name        = "${{var.environment}}-zone"
    Environment = var.environment
    Domain      = "{domain}"
  }}
}}

# ACM Certificate
resource "aws_acm_certificate" "main" {{
  domain_name       = var.domain
  validation_method = "DNS"

  subject_alternative_names = [
    "*.{{var.domain}}"
  ]

  lifecycle {{
    create_before_destroy = true
  }}

  tags = {{
    Name        = "${{var.environment}}-cert"
    Environment = var.environment
  }}
}}

# Certificate validation
resource "aws_route53_record" "cert_validation" {{
  for_each = {{
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {{
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }}
  }}

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.main.zone_id
}}

resource "aws_acm_certificate_validation" "main" {{
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}}
"""

    def _generate_dns_variables(self) -> str:
        """Generate DNS module variables"""
        return """variable "environment" {
  description = "Environment name"
  type        = string
}

variable "domain" {
  description = "Domain name"
  type        = string
}
"""

    def _generate_dns_outputs(self) -> str:
        """Generate DNS module outputs"""
        return """output "zone_id" {
  description = "Route53 zone ID"
  value       = aws_route53_zone.main.zone_id
}

output "certificate_arn" {
  description = "ACM certificate ARN"
  value       = aws_acm_certificate_validation.main.certificate_arn
}

output "name_servers" {
  description = "Route53 name servers"
  value       = aws_route53_zone.main.name_servers
}
"""

    def _generate_secrets_module(self) -> str:
        """Generate secrets module configuration"""
        return """# Secrets Manager
resource "aws_secretsmanager_secret" "app_secrets" {
  name        = "${var.environment}-app-secrets"
  description = "Application secrets for ${var.environment}"

  tags = {
    Name        = "${var.environment}-app-secrets"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    database_password = "changeme"
    api_key          = "changeme"
    jwt_secret       = "changeme"
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# IAM Role for accessing secrets
resource "aws_iam_role" "secrets_access" {
  name = "${var.environment}-secrets-access"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.environment}-secrets-access"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy" "secrets_access" {
  name = "${var.environment}-secrets-access"
  role = aws_iam_role.secrets_access.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.app_secrets.arn
      }
    ]
  })
}
"""

    def _generate_secrets_variables(self) -> str:
        """Generate secrets module variables"""
        return """variable "environment" {
  description = "Environment name"
  type        = string
}
"""

    def _generate_secrets_outputs(self) -> str:
        """Generate secrets module outputs"""
        return """output "secrets_arn" {
  description = "Secrets Manager ARN"
  value       = aws_secretsmanager_secret.app_secrets.arn
}

output "secrets_role_arn" {
  description = "IAM role ARN for secrets access"
  value       = aws_iam_role.secrets_access.arn
}
"""

    def _generate_env_vars(self, env: str) -> str:
        """Generate environment-specific variables"""
        return f"""environment = "{env}"
aws_region  = "us-east-1"

# Environment-specific overrides
"""

    def _generate_helm_chart(self, environments: List[str],
                           domain: str, registry: str) -> Dict[str, str]:
        """Generate Helm chart skeleton"""
        files = {}

        # Chart.yaml
        files['Chart.yaml'] = """apiVersion: v2
name: f-ops-app
description: A Helm chart for F-Ops application
type: application
version: 0.1.0
appVersion: "1.0"
"""

        # values.yaml
        files['values.yaml'] = f"""replicaCount: 2

image:
  repository: {registry}/f-ops-app
  pullPolicy: IfNotPresent
  tag: ""

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: true
  className: nginx
  annotations: {{}}
  hosts:
    - host: {domain}
      paths:
        - path: /
          pathType: Prefix

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80

nodeSelector: {{}}

tolerations: []

affinity: {{}}

# Environment-specific configuration
env: []

# Security context
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 2000

# Pod security context
podSecurityContext:
  fsGroup: 2000
"""

        # Deployment template
        files['templates/deployment.yaml'] = self._generate_deployment_template()

        # Service template
        files['templates/service.yaml'] = self._generate_service_template()

        # Ingress template
        files['templates/ingress.yaml'] = self._generate_ingress_template()

        # ServiceAccount template
        files['templates/serviceaccount.yaml'] = self._generate_serviceaccount_template()

        # ConfigMap template
        files['templates/configmap.yaml'] = self._generate_configmap_template()

        # Environment-specific values
        for env in environments:
            files[f'values-{env}.yaml'] = self._generate_env_values(env)

        return files

    def _generate_deployment_template(self) -> str:
        """Generate Kubernetes Deployment template"""
        return """apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "f-ops-app.fullname" . }}
  labels:
    {{- include "f-ops-app.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "f-ops-app.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      {{- with .Values.podAnnotations }}
      annotations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      labels:
        {{- include "f-ops-app.selectorLabels" . | nindent 8 }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      serviceAccountName: {{ include "f-ops-app.serviceAccountName" . }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      containers:
        - name: {{ .Chart.Name }}
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: 8000
              protocol: TCP
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          env:
            - name: ENVIRONMENT
              value: {{ .Values.environment | quote }}
            {{- range .Values.env }}
            - name: {{ .name }}
              value: {{ .value | quote }}
            {{- end }}
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
"""

    def _generate_service_template(self) -> str:
        """Generate Kubernetes Service template"""
        return """apiVersion: v1
kind: Service
metadata:
  name: {{ include "f-ops-app.fullname" . }}
  labels:
    {{- include "f-ops-app.labels" . | nindent 4 }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    {{- include "f-ops-app.selectorLabels" . | nindent 4 }}
"""

    def _generate_ingress_template(self) -> str:
        """Generate Kubernetes Ingress template"""
        return """{{- if .Values.ingress.enabled -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "f-ops-app.fullname" . }}
  labels:
    {{- include "f-ops-app.labels" . | nindent 4 }}
  {{- with .Values.ingress.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  {{- if .Values.ingress.className }}
  ingressClassName: {{ .Values.ingress.className }}
  {{- end }}
  {{- if .Values.ingress.tls }}
  tls:
    {{- range .Values.ingress.tls }}
    - hosts:
        {{- range .hosts }}
        - {{ . | quote }}
        {{- end }}
      secretName: {{ .secretName }}
    {{- end }}
  {{- end }}
  rules:
    {{- range .Values.ingress.hosts }}
    - host: {{ .host | quote }}
      http:
        paths:
          {{- range .paths }}
          - path: {{ .path }}
            pathType: {{ .pathType }}
            backend:
              service:
                name: {{ include "f-ops-app.fullname" $ }}
                port:
                  number: {{ $.Values.service.port }}
          {{- end }}
    {{- end }}
{{- end }}
"""

    def _generate_serviceaccount_template(self) -> str:
        """Generate Kubernetes ServiceAccount template"""
        return """apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "f-ops-app.serviceAccountName" . }}
  labels:
    {{- include "f-ops-app.labels" . | nindent 4 }}
  {{- with .Values.serviceAccount.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
"""

    def _generate_configmap_template(self) -> str:
        """Generate Kubernetes ConfigMap template"""
        return """apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "f-ops-app.fullname" . }}-config
  labels:
    {{- include "f-ops-app.labels" . | nindent 4 }}
data:
  app.yaml: |
    environment: {{ .Values.environment }}
    debug: false
    log_level: "INFO"
"""

    def _generate_env_values(self, env: str) -> str:
        """Generate environment-specific Helm values"""
        return f"""# Environment-specific values for {env}
environment: {env}

replicaCount: {2 if env == 'prod' else 1}

image:
  tag: "latest"

resources:
  limits:
    cpu: {"1000m" if env == 'prod' else "500m"}
    memory: {"1Gi" if env == 'prod' else "512Mi"}
  requests:
    cpu: {"500m" if env == 'prod' else "250m"}
    memory: {"512Mi" if env == 'prod' else "256Mi"}

autoscaling:
  enabled: {str(env == 'prod').lower()}
  minReplicas: {5 if env == 'prod' else 2}
  maxReplicas: {20 if env == 'prod' else 10}

env:
  - name: LOG_LEVEL
    value: "{"INFO" if env == 'prod' else "DEBUG"}"
  - name: ENVIRONMENT
    value: "{env}"
"""

    def _run_terraform_plan(self, config: Dict[str, str]) -> Dict[str, Any]:
        """Execute terraform plan and capture output"""
        logger.info("Running terraform plan")

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # Write terraform files
                for path, content in config.items():
                    file_path = os.path.join(tmpdir, path)
                    # Create directories
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w') as f:
                        f.write(content)

                # Run terraform init
                init_result = subprocess.run(
                    ['terraform', 'init', '-backend=false'],
                    cwd=tmpdir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if init_result.returncode != 0:
                    return {
                        "status": "failed",
                        "stage": "init",
                        "output": init_result.stdout,
                        "errors": init_result.stderr,
                        "summary": {"add": 0, "change": 0, "destroy": 0, "resources": []}
                    }

                # Run terraform plan
                plan_result = subprocess.run(
                    ['terraform', 'plan', '-json'],
                    cwd=tmpdir,
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                # Parse plan output
                summary = self._parse_terraform_plan(plan_result.stdout)

                return {
                    "status": "success" if plan_result.returncode == 0 else "failed",
                    "output": plan_result.stdout,
                    "errors": plan_result.stderr,
                    "summary": summary,
                    "raw_output": plan_result.stdout
                }

            except subprocess.TimeoutExpired:
                return {
                    "status": "failed",
                    "stage": "timeout",
                    "output": "",
                    "errors": "Terraform plan timed out",
                    "summary": {"add": 0, "change": 0, "destroy": 0, "resources": []}
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "stage": "execution",
                    "output": "",
                    "errors": str(e),
                    "summary": {"add": 0, "change": 0, "destroy": 0, "resources": []}
                }

    def _parse_terraform_plan(self, output: str) -> Dict[str, Any]:
        """Parse terraform plan JSON output"""
        summary = {
            "add": 0,
            "change": 0,
            "destroy": 0,
            "resources": []
        }

        try:
            for line in output.split('\n'):
                if line.strip():
                    try:
                        data = json.loads(line)
                        if data.get('@level') == 'info' and 'change' in data:
                            change = data['change']
                            action = change.get('action')

                            if action == 'create':
                                summary['add'] += 1
                            elif action == 'update':
                                summary['change'] += 1
                            elif action == 'delete':
                                summary['destroy'] += 1

                            resource = change.get('resource', {})
                            summary['resources'].append({
                                'type': resource.get('type', 'unknown'),
                                'name': resource.get('name', 'unknown'),
                                'action': action or 'unknown'
                            })
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.warning(f"Failed to parse terraform plan output: {e}")

        return summary

    def _run_helm_dry_run(self, chart: Dict[str, str]) -> Dict[str, Any]:
        """Execute helm --dry-run and capture output"""
        logger.info("Running helm dry-run")

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                chart_dir = os.path.join(tmpdir, 'chart')
                os.makedirs(chart_dir)

                # Write helm files
                for path, content in chart.items():
                    file_path = os.path.join(chart_dir, path)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w') as f:
                        f.write(content)

                # Run helm lint first
                lint_result = subprocess.run(
                    ['helm', 'lint', chart_dir],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                # Run helm install --dry-run
                dry_run_result = subprocess.run(
                    ['helm', 'install', 'test-release', chart_dir, '--dry-run', '--debug'],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                manifests = self._extract_manifests(dry_run_result.stdout)

                return {
                    "status": "success" if dry_run_result.returncode == 0 else "failed",
                    "lint": {
                        "passed": lint_result.returncode == 0,
                        "output": lint_result.stdout,
                        "errors": lint_result.stderr
                    },
                    "manifests": manifests,
                    "notes": self._extract_notes(dry_run_result.stdout),
                    "raw_output": dry_run_result.stdout,
                    "errors": dry_run_result.stderr
                }

            except subprocess.TimeoutExpired:
                return {
                    "status": "failed",
                    "lint": {"passed": False, "output": "", "errors": "Helm lint timed out"},
                    "manifests": [],
                    "notes": "",
                    "raw_output": "",
                    "errors": "Helm dry-run timed out"
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "lint": {"passed": False, "output": "", "errors": str(e)},
                    "manifests": [],
                    "notes": "",
                    "raw_output": "",
                    "errors": str(e)
                }

    def _extract_manifests(self, output: str) -> List[Dict]:
        """Extract Kubernetes manifests from dry-run output"""
        manifests = []
        current_manifest = []
        in_manifest = False

        for line in output.split('\n'):
            if line.startswith('---'):
                if current_manifest:
                    manifest_text = '\n'.join(current_manifest)
                    try:
                        manifest = yaml.safe_load(manifest_text)
                        if manifest and isinstance(manifest, dict):
                            manifests.append(manifest)
                    except yaml.YAMLError:
                        pass
                    current_manifest = []
                in_manifest = True
            elif in_manifest and line.strip():
                current_manifest.append(line)

        # Process last manifest
        if current_manifest:
            manifest_text = '\n'.join(current_manifest)
            try:
                manifest = yaml.safe_load(manifest_text)
                if manifest and isinstance(manifest, dict):
                    manifests.append(manifest)
            except yaml.YAMLError:
                pass

        return manifests

    def _extract_notes(self, output: str) -> str:
        """Extract NOTES section from helm output"""
        lines = output.split('\n')
        notes_start = -1

        for i, line in enumerate(lines):
            if 'NOTES:' in line:
                notes_start = i + 1
                break

        if notes_start >= 0:
            notes_lines = []
            for line in lines[notes_start:]:
                if line.startswith('---') or line.startswith('apiVersion:'):
                    break
                notes_lines.append(line)
            return '\n'.join(notes_lines).strip()

        return ""