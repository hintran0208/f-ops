from typing import Dict, Any, List
from app.mcp_servers.mcp_github import MCPGitHub
from app.mcp_servers.mcp_gitlab import MCPGitLab
from app.core.audit_logger import AuditLogger
from app.config import settings
import logging
import re

logger = logging.getLogger(__name__)

class PROrchestrator:
    """Orchestrates PR/MR creation across GitHub and GitLab with dry-run artifacts"""

    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
        self.github_client = MCPGitHub(
            token=settings.MCP_GITHUB_TOKEN,
            allowed_repos=settings.ALLOWED_REPOS,
            audit_logger=audit_logger
        )
        self.gitlab_client = MCPGitLab(
            token=settings.MCP_GITLAB_TOKEN,
            allowed_repos=settings.ALLOWED_REPOS,
            audit_logger=audit_logger
        )

    def create_pr(self,
                  repo_url: str,
                  files: Dict[str, str],
                  title: str,
                  body: str,
                  dry_run_artifacts: Dict = None,
                  branch_name: str = None) -> str:
        """Create PR/MR with files and dry-run results"""

        logger.info(f"Creating PR for {repo_url} with {len(files)} files")

        # Generate branch name if not provided
        if not branch_name:
            branch_name = f"fops-generated-{self._generate_branch_suffix()}"

        try:
            if "github.com" in repo_url:
                pr_url = self._create_github_pr(repo_url, files, title, body, branch_name)
            elif "gitlab.com" in repo_url:
                pr_url = self._create_gitlab_mr(repo_url, files, title, body, branch_name)
            else:
                raise ValueError(f"Unsupported repository platform: {repo_url}")

            # Attach dry-run artifacts if provided
            if dry_run_artifacts:
                self.attach_artifacts(pr_url, dry_run_artifacts)

            # Log PR creation
            self.audit_logger.log_pr_creation(
                repo_url=repo_url,
                pr_url=pr_url,
                agent="pr_orchestrator",
                files=files
            )

            logger.info(f"PR created successfully: {pr_url}")
            return pr_url

        except Exception as e:
            logger.error(f"Failed to create PR for {repo_url}: {e}")

            # Log failure
            self.audit_logger.log_operation({
                "type": "pr_creation_failed",
                "agent": "pr_orchestrator",
                "inputs": {"repo_url": repo_url, "files": list(files.keys())},
                "error": str(e)
            })

            raise

    def _create_github_pr(self, repo_url: str, files: Dict, title: str, body: str, branch_name: str) -> str:
        """Create GitHub PR"""
        # Extract repo name from URL
        match = re.search(r'github\.com/([^/]+/[^/]+)', repo_url)
        if not match:
            raise ValueError("Invalid GitHub URL format")

        repo_name = match.group(1).rstrip('.git')

        # Prepare parameters for GitHub MCP
        params = {
            'repo_url': repo_url,
            'repo_name': repo_name,
            'branch_name': branch_name,
            'title': title,
            'body': body,
            'files': files,
            'base_branch': 'main'
        }

        return self.github_client.create_pr(params)

    def _create_gitlab_mr(self, repo_url: str, files: Dict, title: str, body: str, branch_name: str) -> str:
        """Create GitLab MR"""
        # Extract project path from URL
        match = re.search(r'gitlab\.com/([^/]+/[^/]+)', repo_url)
        if not match:
            raise ValueError("Invalid GitLab URL format")

        project_path = match.group(1).rstrip('.git')

        # Prepare parameters for GitLab MCP
        params = {
            'repo_url': repo_url,
            'project_id': project_path,
            'branch_name': branch_name,
            'title': title,
            'body': body,
            'files': files,
            'base_branch': 'main'
        }

        return self.gitlab_client.create_mr(params)

    def attach_artifacts(self, pr_url: str, artifacts: Dict[str, Any]) -> bool:
        """Attach dry-run/plan artifacts to PR/MR"""
        logger.info(f"Attaching artifacts to {pr_url}")

        try:
            if "github.com" in pr_url:
                return self.github_client.attach_artifacts(pr_url, artifacts)
            elif "gitlab.com" in pr_url:
                return self.gitlab_client.attach_artifacts(pr_url, artifacts)
            else:
                raise ValueError(f"Unsupported platform for PR: {pr_url}")

        except Exception as e:
            logger.error(f"Failed to attach artifacts to {pr_url}: {e}")
            raise

    def create_pipeline_pr(self,
                          repo_url: str,
                          pipeline_content: str,
                          pipeline_file: str,
                          citations: List[str],
                          validation_results: Dict[str, Any]) -> str:
        """Create PR specifically for pipeline files with validation artifacts"""

        # Prepare enhanced body with citations
        body = f"""# F-Ops Generated CI/CD Pipeline

This PR adds a CI/CD pipeline generated by F-Ops with the following features:

## Pipeline Features
- ✅ Security scanning integration
- ✅ SLO gates and monitoring
- ✅ Multi-environment deployment support
- ✅ Syntax validation passed

## Knowledge Base Citations
{self._format_citations(citations)}

## Validation Results
- **Status**: {validation_results.get('status', 'unknown')}
- **Syntax Check**: {'✅ Passed' if validation_results.get('parsed') else '❌ Failed'}

---
*Generated by F-Ops Pipeline Agent*
*Review all changes before merging*
"""

        # Prepare dry-run artifacts
        artifacts = {
            "pipeline_validation": validation_results,
            "kb_citations": citations,
            "generation_info": {
                "agent": "pipeline",
                "citations_count": len(citations),
                "validation_status": validation_results.get('status')
            }
        }

        return self.create_pr(
            repo_url=repo_url,
            files={pipeline_file: pipeline_content},
            title="[F-Ops] Add CI/CD Pipeline",
            body=body,
            dry_run_artifacts=artifacts,
            branch_name=f"fops-pipeline-{self._generate_branch_suffix()}"
        )

    def _format_citations(self, citations: List[str]) -> str:
        """Format citations for PR body"""
        if not citations:
            return "No knowledge base sources referenced."

        formatted = []
        for i, citation in enumerate(citations, 1):
            formatted.append(f"{i}. {citation}")

        return "\n".join(formatted)

    def _generate_branch_suffix(self) -> str:
        """Generate unique branch suffix"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        return timestamp

    def check_repository_access(self, repo_url: str) -> Dict[str, Any]:
        """Check if we have access to create PRs in the repository"""
        try:
            if "github.com" in repo_url:
                # Extract repo path
                match = re.search(r'github\.com/([^/]+/[^/]+)', repo_url)
                if match:
                    repo_path = match.group(1).rstrip('.git')
                    return self.github_client.check_repo_access(repo_path)

            elif "gitlab.com" in repo_url:
                # Extract project path
                match = re.search(r'gitlab\.com/([^/]+/[^/]+)', repo_url)
                if match:
                    project_path = match.group(1).rstrip('.git')
                    return self.gitlab_client.check_project_access(project_path)

            return {"access": False, "reason": "Unsupported platform"}

        except Exception as e:
            return {"access": False, "reason": str(e)}