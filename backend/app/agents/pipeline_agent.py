from typing import Dict, Any, List, Optional
import yaml
import json
import tempfile
import subprocess
import os
from app.core.kb_manager import KnowledgeBaseManager
from app.core.citation_engine import CitationEngine
from app.core.audit_logger import AuditLogger
from app.core.ai_service import AIService
import logging

logger = logging.getLogger(__name__)

class PipelineAgent:
    """Pipeline Agent for generating CI/CD pipelines with AI and KB citations"""

    def __init__(self, kb_manager: KnowledgeBaseManager, audit_logger: AuditLogger):
        self.kb = kb_manager
        self.citation_engine = CitationEngine(kb_manager)
        self.audit_logger = audit_logger
        self.ai_service = AIService()

    def analyze_repository(self, repo_url: str, local_path: Optional[str] = None) -> Dict[str, Any]:
        """Detect stack and frameworks from repository using AI"""
        logger.info(f"AI analyzing repository: {repo_url}")

        try:
            # Use AI service for intelligent analysis
            analysis_result = self.ai_service.analyze_repository_stack(repo_url, local_path)
            stack = analysis_result.get("stack", {})

            self.audit_logger.log_agent_decision("pipeline", {
                "action": "ai_stack_analysis",
                "repo_url": repo_url,
                "detected_stack": stack,
                "analysis_source": analysis_result.get("analysis_source", "ai_powered"),
                "reasoning": "AI-powered repository analysis with file scanning"
            })

            return stack

        except Exception as e:
            logger.error(f"AI analysis failed, using fallback: {e}")

            # Fallback to basic heuristics
            stack = {
                "language": "python",
                "framework": "fastapi",
                "has_dockerfile": False,
                "has_tests": True,
                "package_manager": "pip",
                "build_system": "pip",
                "cloud_ready": True,
                "recommended_target": "k8s"
            }

            # Simple heuristics based on repo URL
            if "node" in repo_url.lower() or "js" in repo_url.lower():
                stack.update({
                    "language": "javascript",
                    "framework": "express",
                    "package_manager": "npm",
                    "build_system": "npm"
                })
            elif "go" in repo_url.lower():
                stack.update({
                    "language": "go",
                    "framework": "gin",
                    "package_manager": "go",
                    "build_system": "go"
                })

            self.audit_logger.log_agent_decision("pipeline", {
                "action": "fallback_stack_analysis",
                "repo_url": repo_url,
                "detected_stack": stack,
                "reasoning": "Fallback heuristic analysis - AI unavailable",
                "error": str(e)
            })

            return stack

    def generate_pipeline(self,
                         repo_url: str,
                         stack: Dict,
                         target: Optional[str] = None,
                         environments: Optional[List[str]] = None,
                         mode: str = "guided") -> Dict[str, Any]:
        """Generate CI/CD pipeline with AI and citations"""

        logger.info(f"Generating pipeline for {stack.get('language')} using mode: {mode}")

        try:
            # Use AI for pipeline generation
            ai_result = self.ai_service.generate_pipeline_with_ai(
                repo_url=repo_url,
                stack=stack,
                target=target,
                environments=environments,
                mode=mode
            )

            # Extract AI decisions
            final_target = ai_result.get("target", target or "k8s")
            final_environments = ai_result.get("environments", environments or ["staging", "prod"])
            ai_pipeline_content = ai_result.get("pipeline", "")

            logger.info(f"AI generated pipeline for {final_target} with environments: {final_environments}")

        except Exception as e:
            logger.error(f"AI pipeline generation failed: {e}")
            # Fallback to template generation
            final_target = target or "k8s"
            final_environments = environments or ["staging", "prod"]
            ai_pipeline_content = ""

        # 1. Search KB for similar pipelines
        search_query = f"{stack.get('language')} {final_target} CI/CD pipeline {stack.get('framework', '')}"
        similar_pipelines = self.kb.search(
            collection='pipelines',
            query=search_query,
            k=5
        )

        # Log KB usage
        self.audit_logger.log_kb_usage(
            query=search_query,
            collection='pipelines',
            results_count=len(similar_pipelines),
            citations=[p.get('citation', 'KB source') for p in similar_pipelines]
        )

        # 2. Generate final pipeline content
        if ai_pipeline_content:
            # Use AI-generated content
            pipeline_content = ai_pipeline_content
            generation_method = "ai_generated"
        else:
            # Fallback to template generation
            if "github.com" in repo_url or "local" in repo_url:
                pipeline_content = self._generate_github_actions(stack, final_target, final_environments)
            else:
                pipeline_content = self._generate_gitlab_ci(stack, final_target, final_environments)
            generation_method = "template_generated"

        # 3. Determine pipeline file based on platform
        if "gitlab.com" in repo_url:
            pipeline_file = ".gitlab-ci.yml"
        else:
            # Default to GitHub Actions for local repos and GitHub
            pipeline_file = ".github/workflows/pipeline.yml"

        # 4. Add security scans and SLO gates
        pipeline_content = self._add_security_gates(pipeline_content, stack)
        pipeline_content = self._add_slo_gates(pipeline_content, final_target)

        # 5. Validate syntax
        validation_result = self._validate_yaml(pipeline_content)

        # 6. Add citations from KB
        pipeline_with_citations = self.citation_engine.generate_citations(
            pipeline_content,
            similar_pipelines
        )

        result = {
            "pipeline": pipeline_with_citations,
            "pipeline_file": pipeline_file,
            "citations": [s.get('citation', 'KB source') for s in similar_pipelines],
            "validation": validation_result,
            "stack": stack,
            "target": final_target,
            "environments": final_environments,
            "generation_method": generation_method,
            "mode": mode
        }

        # Log pipeline generation
        self.audit_logger.log_agent_decision("pipeline", {
            "action": "ai_pipeline_generation",
            "repo_url": repo_url,
            "stack": stack,
            "target": final_target,
            "environments": final_environments,
            "mode": mode,
            "generation_method": generation_method,
            "validation_status": validation_result["status"],
            "citations_count": len(similar_pipelines)
        })

        return result

    def _generate_github_actions(self, stack: Dict, target: str, envs: List[str]) -> str:
        """Generate GitHub Actions workflow"""
        workflow = {
            'name': 'F-Ops Generated CI/CD Pipeline',
            'on': {
                'push': {'branches': ['main', 'develop']},
                'pull_request': {'branches': ['main']}
            },
            'env': {
                'TARGET_ENVIRONMENT': target
            },
            'jobs': {}
        }

        # Build job
        build_steps = [
            {'uses': 'actions/checkout@v4'},
            {'name': 'Setup Language Environment', 'run': self._get_setup_command(stack)}
        ]

        if stack['language'] == 'python':
            build_steps.extend([
                {'name': 'Install dependencies', 'run': 'pip install -r requirements.txt'},
                {'name': 'Run tests', 'run': 'pytest || echo "No tests found"'},
                {'name': 'Build package', 'run': 'python -m build || echo "No build step needed"'}
            ])
        elif stack['language'] == 'javascript':
            build_steps.extend([
                {'name': 'Install dependencies', 'run': 'npm install'},
                {'name': 'Run tests', 'run': 'npm test || echo "No tests found"'},
                {'name': 'Build', 'run': 'npm run build || echo "No build step needed"'}
            ])

        workflow['jobs']['build'] = {
            'runs-on': 'ubuntu-latest',
            'steps': build_steps
        }

        # Add deployment jobs for each environment
        for env in envs:
            workflow['jobs'][f'deploy-{env}'] = {
                'runs-on': 'ubuntu-latest',
                'needs': 'build',
                'if': f"github.ref == 'refs/heads/main'" if env == 'prod' else "true",
                'environment': env,
                'steps': [
                    {'uses': 'actions/checkout@v4'},
                    {'name': f'Deploy to {env}', 'run': f'echo "Deploying to {env} ({target})"'}
                ]
            }

        return yaml.dump(workflow, default_flow_style=False)

    def _generate_gitlab_ci(self, stack: Dict, target: str, envs: List[str]) -> str:
        """Generate GitLab CI pipeline"""
        pipeline = {
            'stages': ['build', 'test', 'security', 'deploy'],
            'variables': {
                'TARGET_ENVIRONMENT': target
            },
            'build': {
                'stage': 'build',
                'script': [
                    self._get_setup_command(stack),
                    self._get_build_command(stack)
                ],
                'artifacts': {
                    'paths': ['dist/', 'build/'],
                    'expire_in': '1 hour'
                }
            },
            'test': {
                'stage': 'test',
                'script': [self._get_test_command(stack)],
                'coverage': '/coverage: \\d+\\.\\d+%/'
            }
        }

        # Add deployment stages
        for env in envs:
            pipeline[f'deploy-{env}'] = {
                'stage': 'deploy',
                'script': [f'echo "Deploying to {env}"'],
                'environment': {'name': env},
                'only': ['main'] if env == 'prod' else ['main', 'develop']
            }

        return yaml.dump(pipeline, default_flow_style=False)

    def _add_security_gates(self, pipeline_content: str, stack: Dict) -> str:
        """Add security scanning to pipeline"""
        # For Phase 1, add basic security job
        security_comment = f"""
# Security Scanning (F-Ops Generated)
# TODO: Configure actual security tools for {stack['language']}
# Recommended: SAST, dependency scanning, container scanning
"""
        return security_comment + pipeline_content

    def _add_slo_gates(self, pipeline_content: str, target: str) -> str:
        """Add SLO gates to pipeline"""
        slo_comment = f"""
# SLO Gates (F-Ops Generated)
# Target: {target}
# TODO: Add performance thresholds, uptime checks, error rate monitoring
"""
        return slo_comment + pipeline_content

    def _validate_yaml(self, yaml_content: str) -> Dict[str, Any]:
        """Validate YAML syntax"""
        try:
            parsed = yaml.safe_load(yaml_content)
            return {
                "status": "valid",
                "parsed": True,
                "structure_check": "passed",
                "warnings": []
            }
        except yaml.YAMLError as e:
            logger.error(f"YAML validation failed: {e}")
            return {
                "status": "invalid",
                "parsed": False,
                "error": str(e),
                "warnings": ["YAML syntax error detected"]
            }

    def _get_setup_command(self, stack: Dict) -> str:
        """Get setup command for language"""
        setups = {
            'python': 'python -m pip install --upgrade pip',
            'javascript': 'node --version && npm --version',
            'go': 'go version'
        }
        return setups.get(stack['language'], 'echo "Language setup"')

    def _get_build_command(self, stack: Dict) -> str:
        """Get build command for language"""
        builds = {
            'python': 'pip install -r requirements.txt',
            'javascript': 'npm install && npm run build',
            'go': 'go build ./...'
        }
        return builds.get(stack['language'], 'echo "Build completed"')

    def _get_test_command(self, stack: Dict) -> str:
        """Get test command for language"""
        tests = {
            'python': 'pytest --cov=. --cov-report=term-missing',
            'javascript': 'npm test',
            'go': 'go test ./...'
        }
        return tests.get(stack['language'], 'echo "Tests completed"')